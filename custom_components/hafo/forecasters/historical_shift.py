"""Historical shift forecaster.

This forecaster builds a forecast by fetching historical statistics from the recorder
and shifting them forward by a configurable number of days.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from typing import Any

from homeassistant.components.recorder.statistics import StatisticsRow, statistics_during_period
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.recorder import get_instance
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from custom_components.hafo.const import CONF_HISTORY_DAYS, CONF_SOURCE_ENTITY, DEFAULT_HISTORY_DAYS, DOMAIN

_LOGGER = logging.getLogger(__name__)


# Type alias for statistics - accepts either StatisticsRow or dict-like objects
StatisticsLike = Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class ForecastPoint:
    """A single point in a forecast time series."""

    time: datetime
    value: float


@dataclass(frozen=True, slots=True)
class ForecastResult:
    """Result of a forecast operation."""

    forecast: list[ForecastPoint]
    source_entity: str
    history_days: int
    generated_at: datetime


async def get_statistics_for_sensor(
    hass: HomeAssistant,
    entity_id: str,
    start_time: datetime,
    end_time: datetime,
) -> Sequence["StatisticsRow"]:
    """Fetch hourly statistics for a sensor entity.

    Args:
        hass: Home Assistant instance
        entity_id: The sensor entity ID to fetch statistics for
        start_time: Start of the time range
        end_time: End of the time range

    Returns:
        List of statistics rows with 'start' and 'mean' fields.

    """
    recorder = get_instance(hass)
    statistics: dict[str, list[StatisticsRow]] = await recorder.async_add_executor_job(
        lambda: statistics_during_period(
            hass,
            start_time,
            end_time,
            {entity_id},
            "hour",
            None,
            {"mean"},
        )
    )
    return statistics.get(entity_id, [])


def shift_history_to_forecast(
    statistics: Sequence[StatisticsLike],
    history_days: int,
) -> list[ForecastPoint]:
    """Shift historical statistics forward by N days to create a forecast.

    Takes the raw hourly statistics and shifts each timestamp forward
    by `history_days` to project them into the future.

    Args:
        statistics: List of statistics rows with 'start' and 'mean' fields.
        history_days: Number of days to shift forward.

    Returns:
        List of ForecastPoint objects for the forecast.

    """
    forecast: list[ForecastPoint] = []
    shift = timedelta(days=history_days)

    for stat in statistics:
        start = stat.get("start")
        mean = stat.get("mean")

        if start is None or mean is None:
            continue

        # Convert start to datetime if needed
        if isinstance(start, datetime):
            dt_start = start
        else:
            # Handle numeric timestamp (int or float)
            try:
                timestamp = float(start)
                dt_start = datetime.fromtimestamp(timestamp, tz=dt_util.get_default_time_zone())
            except (TypeError, ValueError):
                continue

        # Shift forward by N days
        future_time = dt_start + shift
        forecast.append(ForecastPoint(time=future_time, value=float(mean)))

    # Sort by time
    forecast.sort(key=lambda x: x.time)
    return forecast


class HistoricalShiftForecaster(DataUpdateCoordinator[ForecastResult | None]):
    """Forecaster that builds forecasts from sensor historical statistics.

    This forecaster fetches historical data from the recorder and shifts it
    forward by N days to project past patterns into the future.

    Update interval: Hourly, aligned with recorder hourly statistics.
    """

    # Update interval: aligned with hourly statistics from the recorder
    UPDATE_INTERVAL = timedelta(hours=1)

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the forecaster.

        Args:
            hass: Home Assistant instance
            entry: Config entry containing forecaster settings

        """
        self._entry = entry
        self._source_entity: str = entry.data[CONF_SOURCE_ENTITY]
        # Read from options first (set via options flow), fall back to data (initial config)
        self._history_days: int = int(
            entry.options.get(CONF_HISTORY_DAYS, entry.data.get(CONF_HISTORY_DAYS, DEFAULT_HISTORY_DAYS))
        )

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=self.UPDATE_INTERVAL,
            config_entry=entry,
        )

    @property
    def source_entity(self) -> str:
        """Return the source entity ID."""
        return self._source_entity

    @property
    def history_days(self) -> int:
        """Return the number of history days used for forecasting."""
        return self._history_days

    @property
    def entry(self) -> ConfigEntry:
        """Return the config entry."""
        return self._entry

    async def _async_update_data(self) -> ForecastResult:
        """Fetch and update forecast data.

        Returns:
            ForecastResult with the latest forecast.

        """
        result = await self._generate_forecast()

        _LOGGER.debug(
            "Generated forecast for %s with %d points",
            self._source_entity,
            len(result.forecast),
        )

        return result

    async def _generate_forecast(self) -> ForecastResult:
        """Generate a forecast by shifting historical data forward.

        Returns:
            ForecastResult with the generated forecast.

        Raises:
            ValueError: If no historical data is available.

        """
        now = dt_util.now()
        start_time = now - timedelta(days=self._history_days)
        end_time = now

        # Fetch historical statistics
        statistics = await get_statistics_for_sensor(
            self.hass, self._source_entity, start_time, end_time
        )

        if not statistics:
            msg = f"No historical data available for {self._source_entity}"
            raise ValueError(msg)

        # Shift history forward to create forecast
        forecast = shift_history_to_forecast(statistics, self._history_days)

        if not forecast:
            msg = f"No valid forecast points generated for {self._source_entity}"
            raise ValueError(msg)

        return ForecastResult(
            forecast=forecast,
            source_entity=self._source_entity,
            history_days=self._history_days,
            generated_at=now,
        )

    def cleanup(self) -> None:
        """Clean up coordinator resources."""
        _LOGGER.debug("Cleaning up forecaster for %s", self._source_entity)
