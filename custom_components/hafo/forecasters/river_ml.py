"""RiverML forecaster.

This forecaster uses River's online machine learning capabilities for multi-variate
time series forecasting. It supports multiple input entities as features to predict
a single output entity, with incremental learning from new data.
"""

from collections.abc import Mapping, Sequence
import contextlib
from datetime import datetime, timedelta
import logging
from pathlib import Path
import pickle
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util
from river import linear_model, metrics, preprocessing, time_series

from custom_components.hafo.const import (
    CONF_FORECAST_HOURS,
    CONF_HISTORY_DAYS,
    CONF_INPUT_ENTITIES,
    CONF_OUTPUT_ENTITY,
    CONF_RIVER_MODEL_TYPE,
    DEFAULT_FORECAST_HOURS,
    DEFAULT_HISTORY_DAYS,
    DEFAULT_RIVER_MODEL_TYPE,
    DOMAIN,
    RIVER_MODEL_SNARIMAX,
)

from .common import ForecastPoint, ForecastResult, get_statistics_for_sensors

_LOGGER = logging.getLogger(__name__)

# Storage directory for model persistence
STORAGE_DIR = ".storage/hafo_models"

# Type alias for RiverML models (SNARIMAX, Pipeline, etc.)
type RiverModel = Any


class RiverMLForecaster(DataUpdateCoordinator[ForecastResult | None]):
    """Forecaster using River's online machine learning for multi-variate prediction.

    This forecaster uses multiple input entities as features to predict a single
    output entity. It supports incremental learning, keeping the model in memory
    and persisting to disk after updates.

    Update interval: Hourly, aligned with recorder hourly statistics.
    """

    UPDATE_INTERVAL = timedelta(hours=1)

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the forecaster.

        Args:
            hass: Home Assistant instance
            entry: Config entry containing forecaster settings

        """
        self._entry = entry
        self._input_entities: list[str] = list(entry.data[CONF_INPUT_ENTITIES])
        self._output_entity: str = entry.data[CONF_OUTPUT_ENTITY]
        self._history_days: int = int(entry.data.get(CONF_HISTORY_DAYS, DEFAULT_HISTORY_DAYS))
        self._forecast_hours: int = int(entry.data.get(CONF_FORECAST_HOURS, DEFAULT_FORECAST_HOURS))
        self._model_type: str = entry.data.get(CONF_RIVER_MODEL_TYPE, DEFAULT_RIVER_MODEL_TYPE)

        # Model state (kept in memory)
        self._model: RiverModel | None = None
        self._last_update_timestamp: datetime | None = None
        self._metrics = metrics.MAE() + metrics.RMSE()
        self._metrics_samples: int = 0

        # Last known values for input entities (for future forecasting)
        self._last_known_inputs: dict[str, float] = {}

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=self.UPDATE_INTERVAL,
            config_entry=entry,
        )

        # Load persisted model on initialization
        self._load_model_from_disk()

    @property
    def source_entity(self) -> str:
        """Return the primary source entity (output entity for RiverML)."""
        return self._output_entity

    @property
    def history_days(self) -> int:
        """Return the number of history days used for initial training."""
        return self._history_days

    @property
    def entry(self) -> ConfigEntry:
        """Return the config entry."""
        return self._entry

    @property
    def forecast_hours(self) -> int:
        """Return the forecast horizon in hours."""
        return self._forecast_hours

    @property
    def input_entities(self) -> list[str]:
        """Return the list of input entities."""
        return self._input_entities

    @property
    def output_entity(self) -> str:
        """Return the output entity."""
        return self._output_entity

    @property
    def model_type(self) -> str:
        """Return the model type."""
        return self._model_type

    def _get_storage_path(self) -> Path:
        """Get the path for model persistence."""
        return Path(self.hass.config.path(STORAGE_DIR)) / f"{self._entry.entry_id}.pkl"

    def _load_model_from_disk(self) -> None:
        """Load persisted model from disk if available."""
        storage_path = self._get_storage_path()

        if not storage_path.exists():
            _LOGGER.debug("No persisted model found at %s", storage_path)
            return

        try:
            with storage_path.open("rb") as f:
                data = pickle.load(f)  # noqa: S301

            self._model = data.get("model")
            self._last_update_timestamp = data.get("last_update_timestamp")
            self._last_known_inputs = data.get("last_known_inputs", {})
            metrics_data = data.get("metrics")
            if metrics_data:
                self._metrics = metrics_data
            self._metrics_samples = data.get("metrics_samples", 0)

            _LOGGER.debug(
                "Loaded model from disk, last update: %s",
                self._last_update_timestamp,
            )
        except Exception as e:
            _LOGGER.warning("Failed to load model from disk: %s, will train from scratch", e)
            self._model = None
            self._last_update_timestamp = None

    def _save_model_to_disk(self) -> None:
        """Save model state to disk."""
        storage_path = self._get_storage_path()

        # Ensure directory exists
        storage_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "model": self._model,
            "last_update_timestamp": self._last_update_timestamp,
            "last_known_inputs": self._last_known_inputs,
            "metrics": self._metrics,
            "metrics_samples": self._metrics_samples,
        }

        try:
            with storage_path.open("wb") as f:
                pickle.dump(data, f)
            _LOGGER.debug("Saved model to disk at %s", storage_path)
        except Exception as e:
            _LOGGER.warning("Failed to save model to disk: %s", e)

    def _create_model(self) -> RiverModel:
        """Create a new model based on configured type."""
        if self._model_type == RIVER_MODEL_SNARIMAX:
            # SNARIMAX with sensible defaults for hourly data
            # p=24 for daily patterns, m=24 for daily seasonality
            return time_series.SNARIMAX(
                p=24,  # Autoregressive order (past 24 hours)
                d=0,  # Differencing order
                q=0,  # Moving average order
                m=24,  # Seasonal period (daily)
                sp=1,  # Seasonal autoregressive order
                sd=0,  # Seasonal differencing order
                sq=0,  # Seasonal moving average order
            )

        # Linear regression with standard scaler pipeline
        return preprocessing.StandardScaler() | linear_model.LinearRegression()

    async def _available(self) -> bool:
        """Check if we can generate a forecast.

        Returns:
            True if the recorder component is available and all entities exist.

        """
        if "recorder" not in self.hass.config.components:
            return False

        # Check all input entities exist
        for entity_id in self._input_entities:
            if self.hass.states.get(entity_id) is None:
                return False

        # Check output entity exists
        return self.hass.states.get(self._output_entity) is not None

    async def _async_update_data(self) -> ForecastResult | None:
        """Fetch and update forecast data.

        Returns:
            ForecastResult with the latest forecast, or None if unavailable.

        Raises:
            UpdateFailed: If the forecast cannot be generated.

        """
        try:
            if not await self._available():
                _LOGGER.warning("Forecaster not available - recorder may not be ready or entities missing")
                return None

            # Train or update the model
            await self._train_or_update_model()

            # Generate forecast
            result = await self._generate_forecast()

            _LOGGER.debug(
                "Generated forecast for %s with %d points",
                self._output_entity,
                len(result.forecast),
            )

            return result

        except ValueError as err:
            _LOGGER.warning("Failed to generate forecast: %s", err)
            return None
        except Exception as err:
            msg = f"Error generating forecast: {err}"
            raise UpdateFailed(msg) from err

    async def _train_or_update_model(self) -> None:
        """Train a new model or update existing model with new data."""
        now = dt_util.now()

        if self._model is None:
            # First run: train on full historical dataset
            _LOGGER.debug("No model in memory, training from scratch")
            await self._train_from_scratch(now)
        else:
            # Incremental update with new data
            await self._incremental_update(now)

        # Save model to disk after update
        await self.hass.async_add_executor_job(self._save_model_to_disk)

    async def _train_from_scratch(self, now: datetime) -> None:
        """Train a new model on all available historical data."""
        # Use a very early date to fetch all available statistics from recorder
        # The recorder will only return data it has, so this effectively gets everything
        start_time = datetime(2000, 1, 1, tzinfo=dt_util.get_default_time_zone())
        end_time = now

        # Fetch statistics for all entities
        all_entities = set(self._input_entities) | {self._output_entity}
        statistics = await get_statistics_for_sensors(
            self.hass,
            all_entities,
            start_time,
            end_time,
        )

        # Build training data from statistics
        training_data = self._build_training_data(statistics)

        if not training_data:
            msg = "No historical data available for training"
            raise ValueError(msg)

        # Create and train model
        self._model = self._create_model()

        for _, features, target in training_data:
            # Update metrics with prediction before learning (for consistency with incremental)
            prediction = self._predict_one(features)
            if prediction is not None:
                self._metrics.update(target, prediction)
                self._metrics_samples += 1

            self._train_one(features, target)
            # Update last known inputs
            self._last_known_inputs = features.copy()

        self._last_update_timestamp = now
        _LOGGER.info(
            "Trained model on %d data points for %s",
            len(training_data),
            self._output_entity,
        )

    async def _incremental_update(self, now: datetime) -> None:
        """Update model incrementally with new data since last update."""
        if self._last_update_timestamp is None:
            # Should not happen, but fallback to training from scratch
            await self._train_from_scratch(now)
            return

        start_time = self._last_update_timestamp
        end_time = now

        # Skip if no new data expected
        if end_time - start_time < self.UPDATE_INTERVAL:
            _LOGGER.debug("Less than update interval since last update, skipping")
            return

        # Fetch statistics for all entities
        all_entities = set(self._input_entities) | {self._output_entity}
        statistics = await get_statistics_for_sensors(
            self.hass,
            all_entities,
            start_time,
            end_time,
        )

        # Build training data from statistics
        training_data = self._build_training_data(statistics)

        if not training_data:
            _LOGGER.debug("No new data for incremental update")
            self._last_update_timestamp = now
            return

        # Update model incrementally
        for _, features, target in training_data:
            # Update metrics with prediction before learning
            if self._model is not None:
                prediction = self._predict_one(features)
                if prediction is not None:
                    self._metrics.update(target, prediction)
                    self._metrics_samples += 1

            self._train_one(features, target)
            # Update last known inputs
            self._last_known_inputs = features.copy()

        self._last_update_timestamp = now
        _LOGGER.debug(
            "Incremental update with %d data points",
            len(training_data),
        )

    def _build_training_data(
        self,
        statistics: Mapping[str, Sequence[Mapping[str, Any]]],
    ) -> list[tuple[datetime, dict[str, float], float]]:
        """Build training data from statistics.

        The HA statistics API already buckets data by hour, so timestamps
        naturally align across entities. We just need to extract the data
        and match by timestamp.

        Returns list of (timestamp, features_dict, target_value) tuples
        where all entities have data for that timestamp.
        """
        # Build timestamp -> value mapping for each entity
        entity_data: dict[str, dict[datetime, float]] = {}

        for entity_id, stats in statistics.items():
            entity_data[entity_id] = {}
            for stat in stats:
                start = stat.get("start")
                mean = stat.get("mean")

                if start is None or mean is None:
                    continue

                # Convert timestamp to datetime if needed
                if isinstance(start, datetime):
                    dt_start = start
                elif isinstance(start, float | int):
                    dt_start = datetime.fromtimestamp(start, tz=dt_util.get_default_time_zone())
                else:
                    continue

                entity_data[entity_id][dt_start] = float(mean)

        if not entity_data:
            return []

        # Find timestamps where all entities have data
        all_entity_ids = set(self._input_entities) | {self._output_entity}
        if not all(eid in entity_data for eid in all_entity_ids):
            return []

        common_timestamps = set.intersection(*(set(entity_data[eid].keys()) for eid in all_entity_ids))

        if not common_timestamps:
            return []

        # Build training data sorted by timestamp
        training_data: list[tuple[datetime, dict[str, float], float]] = []
        for timestamp in sorted(common_timestamps):
            features = {entity_id: entity_data[entity_id][timestamp] for entity_id in self._input_entities}
            target = entity_data[self._output_entity][timestamp]
            training_data.append((timestamp, features, target))

        return training_data

    def _train_one(self, features: dict[str, float], target: float) -> None:
        """Train the model on a single data point."""
        if self._model is None:
            return

        if self._model_type == RIVER_MODEL_SNARIMAX:
            # SNARIMAX uses x for exogenous variables
            self._model.learn_one(y=target, x=features)
        else:
            # Linear regression uses x for features
            self._model.learn_one(x=features, y=target)

    def _predict_one(self, features: dict[str, float]) -> float | None:
        """Predict a single value given features."""
        if self._model is None:
            return None

        try:
            if self._model_type == RIVER_MODEL_SNARIMAX:
                # SNARIMAX forecast_one with exogenous variables
                return self._model.forecast(horizon=1, xs=[features])[0]
            # Linear regression predict_one
            return self._model.predict_one(x=features)
        except Exception as e:
            _LOGGER.debug("Prediction failed: %s", e)
            return None

    def _get_future_input_values(
        self,
        entity_id: str,
        future_times: list[datetime],
    ) -> list[float]:
        """Get input values for future timestamps.

        This is an extension point for future forecast consumption.
        Currently returns last known value for all future steps.

        Args:
            entity_id: The input entity ID
            future_times: List of future timestamps to get values for

        Returns:
            List of values for each future timestamp

        """
        # EXTENSION POINT: Future implementation can check for external forecasts
        # from the entity's forecast attribute here. For now, use last known value.
        last_value = self._last_known_inputs.get(entity_id, 0.0)
        return [last_value] * len(future_times)

    async def _generate_forecast(self) -> ForecastResult:
        """Generate forecast using the trained model.

        Returns:
            ForecastResult with the generated forecast.

        Raises:
            ValueError: If no model is available.

        """
        if self._model is None:
            msg = "No model available for forecasting"
            raise ValueError(msg)

        now = dt_util.now()

        # Generate future timestamps at hourly intervals
        future_times = [now + timedelta(hours=i) for i in range(1, self._forecast_hours + 1)]

        # Get future input values for all input entities
        future_inputs: dict[str, list[float]] = {}
        for entity_id in self._input_entities:
            future_inputs[entity_id] = self._get_future_input_values(entity_id, future_times)

        # Generate predictions
        forecast_points: list[ForecastPoint] = []

        if self._model_type == RIVER_MODEL_SNARIMAX:
            # SNARIMAX can forecast multiple steps at once with exogenous variables
            xs = [
                {entity_id: future_inputs[entity_id][i] for entity_id in self._input_entities}
                for i in range(len(future_times))
            ]
            try:
                predictions = self._model.forecast(horizon=len(future_times), xs=xs)
                for i, prediction in enumerate(predictions):
                    forecast_points.append(ForecastPoint(time=future_times[i], value=float(prediction)))
            except Exception as e:
                _LOGGER.warning("SNARIMAX forecast failed: %s", e)
                msg = f"Failed to generate forecast: {e}"
                raise ValueError(msg) from e
        else:
            # Linear regression: predict one step at a time
            for i, future_time in enumerate(future_times):
                features = {entity_id: future_inputs[entity_id][i] for entity_id in self._input_entities}
                prediction = self._predict_one(features)
                if prediction is not None:
                    forecast_points.append(ForecastPoint(time=future_time, value=prediction))

        if not forecast_points:
            msg = "No valid forecast points generated"
            raise ValueError(msg)

        # Build metrics dict
        model_metrics = self._get_metrics()

        return ForecastResult(
            forecast=forecast_points,
            source_entity=self._output_entity,
            history_days=self._history_days,
            generated_at=now,
            metrics=model_metrics,
        )

    def _get_metrics(self) -> dict[str, float]:
        """Get current model performance metrics."""
        if self._metrics_samples == 0:
            return {}

        result: dict[str, float] = {"samples": float(self._metrics_samples)}

        # Extract individual metrics from composite
        for metric in self._metrics:
            metric_name = metric.__class__.__name__.lower()
            with contextlib.suppress(Exception):
                result[metric_name] = float(metric.get())

        return result

    def cleanup(self) -> None:
        """Clean up coordinator resources."""
        _LOGGER.debug("Cleaning up RiverML forecaster for %s", self._output_entity)
        # Save model one last time before cleanup
        self._save_model_to_disk()
