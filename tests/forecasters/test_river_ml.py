"""Tests for the RiverML forecaster."""

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from unittest.mock import patch

from homeassistant.core import HomeAssistant
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
from river import compose, time_series

from custom_components.hafo.const import (
    CONF_FORECAST_HOURS,
    CONF_FORECAST_TYPE,
    CONF_HISTORY_DAYS,
    CONF_INPUT_ENTITIES,
    CONF_OUTPUT_ENTITY,
    CONF_RIVER_MODEL_TYPE,
    DOMAIN,
    FORECAST_TYPE_RIVER_ML,
    RIVER_MODEL_LINEAR,
    RIVER_MODEL_SNARIMAX,
)
from custom_components.hafo.forecasters import river_ml as rml
from custom_components.hafo.forecasters.river_ml import RiverMLForecaster


def _create_mock_entry(
    hass: HomeAssistant,
    *,
    input_entities: list[str] | None = None,
    output_entity: str = "sensor.output",
    history_days: int = 7,
    forecast_hours: int = 24,
    model_type: str = RIVER_MODEL_SNARIMAX,
) -> MockConfigEntry:
    """Create a mock config entry for RiverML testing."""
    if input_entities is None:
        input_entities = ["sensor.input1", "sensor.input2"]

    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test RiverML Forecast",
        data={
            CONF_INPUT_ENTITIES: input_entities,
            CONF_OUTPUT_ENTITY: output_entity,
            CONF_HISTORY_DAYS: history_days,
            CONF_FORECAST_HOURS: forecast_hours,
            CONF_RIVER_MODEL_TYPE: model_type,
            CONF_FORECAST_TYPE: FORECAST_TYPE_RIVER_ML,
        },
        entry_id="test_riverml_entry_id",
    )
    entry.add_to_hass(hass)
    return entry


def _create_mock_statistics(
    start_time: datetime,
    hours: int,
    entity_values: dict[str, list[float]],
) -> dict[str, list[dict[str, Any]]]:
    """Create mock statistics for multiple entities."""
    result: dict[str, list[dict[str, Any]]] = {}

    for entity_id, values in entity_values.items():
        result[entity_id] = [
            {"start": start_time + timedelta(hours=i), "mean": values[i % len(values)]} for i in range(hours)
        ]

    return result


# Tests for RiverMLForecaster class properties


def test_forecaster_properties(hass: HomeAssistant) -> None:
    """Forecaster exposes configuration properties."""
    entry = _create_mock_entry(
        hass,
        input_entities=["sensor.temp", "sensor.humidity"],
        output_entity="sensor.power",
        history_days=14,
        forecast_hours=48,
        model_type=RIVER_MODEL_LINEAR,
    )
    forecaster = RiverMLForecaster(hass, entry)

    assert forecaster.input_entities == ["sensor.temp", "sensor.humidity"]
    assert forecaster.output_entity == "sensor.power"
    assert forecaster.source_entity == "sensor.power"
    assert forecaster.history_days == 14
    assert forecaster.forecast_hours == 48
    assert forecaster.model_type == RIVER_MODEL_LINEAR
    assert forecaster.entry is entry


def test_forecaster_update_interval() -> None:
    """Forecaster has hourly update interval."""
    assert timedelta(hours=1) == RiverMLForecaster.UPDATE_INTERVAL


# Tests for availability


async def test_forecaster_available_when_all_entities_exist(hass: HomeAssistant) -> None:
    """_available() returns True when recorder is loaded and all entities exist."""
    hass.config.components.add("recorder")
    hass.states.async_set("sensor.input1", "10.0")
    hass.states.async_set("sensor.input2", "20.0")
    hass.states.async_set("sensor.output", "100.0")

    entry = _create_mock_entry(hass)
    forecaster = RiverMLForecaster(hass, entry)

    assert await forecaster._available()


async def test_forecaster_not_available_when_recorder_missing(hass: HomeAssistant) -> None:
    """_available() returns False when recorder is not loaded."""
    hass.states.async_set("sensor.input1", "10.0")
    hass.states.async_set("sensor.input2", "20.0")
    hass.states.async_set("sensor.output", "100.0")

    entry = _create_mock_entry(hass)
    forecaster = RiverMLForecaster(hass, entry)

    assert not await forecaster._available()


async def test_forecaster_not_available_when_input_entity_missing(hass: HomeAssistant) -> None:
    """_available() returns False when an input entity doesn't exist."""
    hass.config.components.add("recorder")
    hass.states.async_set("sensor.input1", "10.0")
    # sensor.input2 is missing
    hass.states.async_set("sensor.output", "100.0")

    entry = _create_mock_entry(hass)
    forecaster = RiverMLForecaster(hass, entry)

    assert not await forecaster._available()


async def test_forecaster_not_available_when_output_entity_missing(hass: HomeAssistant) -> None:
    """_available() returns False when output entity doesn't exist."""
    hass.config.components.add("recorder")
    hass.states.async_set("sensor.input1", "10.0")
    hass.states.async_set("sensor.input2", "20.0")
    # sensor.output is missing

    entry = _create_mock_entry(hass)
    forecaster = RiverMLForecaster(hass, entry)

    assert not await forecaster._available()


# Tests for model creation


def test_create_snarimax_model(hass: HomeAssistant) -> None:
    """Creates SNARIMAX model when configured."""
    entry = _create_mock_entry(hass, model_type=RIVER_MODEL_SNARIMAX)
    forecaster = RiverMLForecaster(hass, entry)

    model = forecaster._create_model()

    assert isinstance(model, time_series.SNARIMAX)


def test_create_linear_regression_model(hass: HomeAssistant) -> None:
    """Creates Linear Regression pipeline when configured."""
    entry = _create_mock_entry(hass, model_type=RIVER_MODEL_LINEAR)
    forecaster = RiverMLForecaster(hass, entry)

    model = forecaster._create_model()

    # Should be a pipeline with StandardScaler and LinearRegression
    assert isinstance(model, compose.Pipeline)


# Tests for data alignment


def test_align_statistics_common_timestamps(hass: HomeAssistant) -> None:
    """Aligns statistics across multiple entities by timestamp."""
    entry = _create_mock_entry(hass, input_entities=["sensor.input1"], output_entity="sensor.output")
    forecaster = RiverMLForecaster(hass, entry)

    base = datetime(2024, 1, 1, 10, 0, 0, tzinfo=UTC)
    statistics = {
        "sensor.input1": [
            {"start": base, "mean": 10.0},
            {"start": base + timedelta(hours=1), "mean": 20.0},
            {"start": base + timedelta(hours=2), "mean": 30.0},
        ],
        "sensor.output": [
            {"start": base, "mean": 100.0},
            {"start": base + timedelta(hours=1), "mean": 200.0},
            # Missing hour 2
        ],
    }

    aligned = forecaster._align_statistics(statistics)

    # Only timestamps with all entities should be included
    assert len(aligned) == 2
    assert aligned[0][1] == {"sensor.input1": 10.0}
    assert aligned[0][2] == pytest.approx(100.0)
    assert aligned[1][1] == {"sensor.input1": 20.0}
    assert aligned[1][2] == pytest.approx(200.0)


def test_align_statistics_empty_when_no_common_timestamps(hass: HomeAssistant) -> None:
    """Returns empty list when no common timestamps exist."""
    entry = _create_mock_entry(hass, input_entities=["sensor.input1"], output_entity="sensor.output")
    forecaster = RiverMLForecaster(hass, entry)

    base = datetime(2024, 1, 1, 10, 0, 0, tzinfo=UTC)
    statistics = {
        "sensor.input1": [
            {"start": base, "mean": 10.0},
        ],
        "sensor.output": [
            {"start": base + timedelta(hours=1), "mean": 100.0},
        ],
    }

    aligned = forecaster._align_statistics(statistics)

    assert aligned == []


def test_align_statistics_skips_none_values(hass: HomeAssistant) -> None:
    """Skips entries with None start or mean values."""
    entry = _create_mock_entry(hass, input_entities=["sensor.input1"], output_entity="sensor.output")
    forecaster = RiverMLForecaster(hass, entry)

    base = datetime(2024, 1, 1, 10, 0, 0, tzinfo=UTC)
    statistics = {
        "sensor.input1": [
            {"start": base, "mean": 10.0},
            {"start": base + timedelta(hours=1), "mean": None},  # Should skip
        ],
        "sensor.output": [
            {"start": base, "mean": 100.0},
            {"start": base + timedelta(hours=1), "mean": 200.0},
        ],
    }

    aligned = forecaster._align_statistics(statistics)

    assert len(aligned) == 1
    assert aligned[0][1] == {"sensor.input1": 10.0}


# Tests for model persistence


def test_get_storage_path(hass: HomeAssistant) -> None:
    """Returns correct storage path for model persistence."""
    entry = _create_mock_entry(hass)
    forecaster = RiverMLForecaster(hass, entry)

    path = forecaster._get_storage_path()

    assert path.name == f"{entry.entry_id}.pkl"
    assert ".storage/hafo_models" in str(path)


def test_save_and_load_model(hass: HomeAssistant, tmp_path: Path) -> None:
    """Model can be saved and loaded from disk."""
    entry = _create_mock_entry(hass)
    forecaster = RiverMLForecaster(hass, entry)

    # Create a model
    forecaster._model = forecaster._create_model()
    forecaster._last_update_timestamp = datetime(2024, 1, 1, tzinfo=UTC)
    forecaster._last_known_inputs = {"sensor.input1": 10.0}

    # Mock storage path
    storage_path = tmp_path / f"{entry.entry_id}.pkl"
    with patch.object(forecaster, "_get_storage_path", return_value=storage_path):
        # Save model
        forecaster._save_model_to_disk()

        assert storage_path.exists()

        # Reset model state
        forecaster._model = None
        forecaster._last_update_timestamp = None
        forecaster._last_known_inputs = {}

        # Load model
        forecaster._load_model_from_disk()

        assert forecaster._model is not None
        assert forecaster._last_update_timestamp == datetime(2024, 1, 1, tzinfo=UTC)
        assert forecaster._last_known_inputs == {"sensor.input1": 10.0}


def test_load_model_handles_missing_file(hass: HomeAssistant, tmp_path: Path) -> None:
    """Loading from non-existent file leaves model as None."""
    entry = _create_mock_entry(hass)
    forecaster = RiverMLForecaster(hass, entry)

    storage_path = tmp_path / "nonexistent.pkl"
    with patch.object(forecaster, "_get_storage_path", return_value=storage_path):
        forecaster._load_model_from_disk()

        assert forecaster._model is None


def test_load_model_handles_corrupted_file(hass: HomeAssistant, tmp_path: Path) -> None:
    """Loading from corrupted file leaves model as None."""
    entry = _create_mock_entry(hass)
    forecaster = RiverMLForecaster(hass, entry)

    storage_path = tmp_path / f"{entry.entry_id}.pkl"
    storage_path.write_bytes(b"corrupted data")

    with patch.object(forecaster, "_get_storage_path", return_value=storage_path):
        forecaster._load_model_from_disk()

        assert forecaster._model is None


# Tests for future input values


def test_get_future_input_values_uses_last_known(hass: HomeAssistant) -> None:
    """Future input values use last known value."""
    entry = _create_mock_entry(hass)
    forecaster = RiverMLForecaster(hass, entry)
    forecaster._last_known_inputs = {"sensor.input1": 42.0}

    future_times = [
        datetime(2024, 1, 1, 10, tzinfo=UTC),
        datetime(2024, 1, 1, 11, tzinfo=UTC),
        datetime(2024, 1, 1, 12, tzinfo=UTC),
    ]

    values = forecaster._get_future_input_values("sensor.input1", future_times)

    assert values == [42.0, 42.0, 42.0]


def test_get_future_input_values_defaults_to_zero(hass: HomeAssistant) -> None:
    """Future input values default to 0 when no last known value."""
    entry = _create_mock_entry(hass)
    forecaster = RiverMLForecaster(hass, entry)
    forecaster._last_known_inputs = {}

    future_times = [datetime(2024, 1, 1, 10, tzinfo=UTC)]

    values = forecaster._get_future_input_values("sensor.unknown", future_times)

    assert values == [0.0]


# Tests for training and forecast generation


async def test_train_from_scratch_creates_model(
    hass: HomeAssistant,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Training from scratch creates and trains a model."""
    entry = _create_mock_entry(
        hass,
        input_entities=["sensor.input1"],
        output_entity="sensor.output",
        model_type=RIVER_MODEL_LINEAR,
    )
    forecaster = RiverMLForecaster(hass, entry)

    # Mock storage path to avoid file system issues
    storage_path = tmp_path / f"{entry.entry_id}.pkl"
    monkeypatch.setattr(forecaster, "_get_storage_path", lambda: storage_path)

    base = datetime(2024, 1, 1, 10, 0, 0, tzinfo=UTC)
    mock_stats = {
        "sensor.input1": [{"start": base + timedelta(hours=i), "mean": float(i * 10)} for i in range(24)],
        "sensor.output": [{"start": base + timedelta(hours=i), "mean": float(i * 100)} for i in range(24)],
    }

    async def mock_get_stats(*args: Any, **kwargs: Any) -> dict[str, list[dict[str, Any]]]:
        return mock_stats

    monkeypatch.setattr(rml, "get_statistics_for_sensors", mock_get_stats)

    now = datetime(2024, 1, 8, 10, 0, 0, tzinfo=UTC)
    await forecaster._train_from_scratch(now)

    assert forecaster._model is not None
    assert forecaster._last_update_timestamp == now
    assert forecaster._last_known_inputs == {"sensor.input1": 230.0}  # Last value


async def test_generate_forecast_returns_result(
    hass: HomeAssistant,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """_generate_forecast() returns a ForecastResult."""
    entry = _create_mock_entry(
        hass,
        input_entities=["sensor.input1"],
        output_entity="sensor.output",
        forecast_hours=24,
        model_type=RIVER_MODEL_LINEAR,
    )
    forecaster = RiverMLForecaster(hass, entry)

    # Mock storage path
    storage_path = tmp_path / f"{entry.entry_id}.pkl"
    monkeypatch.setattr(forecaster, "_get_storage_path", lambda: storage_path)

    # Create and pre-train model
    forecaster._model = forecaster._create_model()
    forecaster._last_known_inputs = {"sensor.input1": 50.0}

    # Train with some data
    for i in range(24):
        features = {"sensor.input1": float(i * 10)}
        target = float(i * 100)
        forecaster._train_one(features, target)

    result = await forecaster._generate_forecast()

    assert result is not None
    assert result.source_entity == "sensor.output"
    assert result.history_days == 7
    assert len(result.forecast) == 24  # forecast_hours


async def test_generate_forecast_raises_when_no_model(hass: HomeAssistant) -> None:
    """_generate_forecast() raises when no model is available."""
    entry = _create_mock_entry(hass)
    forecaster = RiverMLForecaster(hass, entry)
    forecaster._model = None

    with pytest.raises(ValueError, match="No model available"):
        await forecaster._generate_forecast()


# Tests for metrics


def test_get_metrics_empty_when_no_samples(hass: HomeAssistant) -> None:
    """Returns empty dict when no metrics samples collected."""
    entry = _create_mock_entry(hass)
    forecaster = RiverMLForecaster(hass, entry)
    forecaster._metrics_samples = 0

    metrics = forecaster._get_metrics()

    assert metrics == {}


def test_get_metrics_returns_values_with_samples(hass: HomeAssistant) -> None:
    """Returns metrics dict with values when samples collected."""
    entry = _create_mock_entry(hass)
    forecaster = RiverMLForecaster(hass, entry)

    # Simulate some metric updates
    forecaster._metrics.update(100.0, 95.0)
    forecaster._metrics.update(200.0, 190.0)
    forecaster._metrics_samples = 2

    metrics = forecaster._get_metrics()

    assert "samples" in metrics
    assert metrics["samples"] == 2.0
    assert "mae" in metrics
    assert "rmse" in metrics


# Tests for cleanup


def test_cleanup_saves_model(hass: HomeAssistant, tmp_path: Path) -> None:
    """Cleanup saves model to disk."""
    entry = _create_mock_entry(hass)
    forecaster = RiverMLForecaster(hass, entry)

    storage_path = tmp_path / f"{entry.entry_id}.pkl"
    with patch.object(forecaster, "_get_storage_path", return_value=storage_path):
        forecaster._model = forecaster._create_model()
        forecaster.cleanup()

        assert storage_path.exists()
