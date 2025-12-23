"""Historical shift forecaster.

This forecaster builds a forecast by fetching historical statistics from the recorder
and shifting them forward by a configurable number of days.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from typing import TYPE_CHECKING, Any

from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

if TYPE_CHECKING:
    from homeassistant.components.recorder.statistics import StatisticsRow

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

    Raises:
        ValueError: If the recorder is not available or not set up.

    """
    if "recorder" not in hass.config.components:
        msg = "Recorder component not loaded"
        raise ValueError(msg)

    try:
        from homeassistant.helpers.recorder import DATA_INSTANCE  # noqa: PLC0415

        if DATA_INSTANCE not in hass.data:
            msg = "Recorder not initialized"
            raise ValueError(msg)
    except ImportError:
        msg = "Recorder component not available"
        raise ValueError(msg) from None

    from homeassistant.components.recorder.statistics import statistics_during_period  # noqa: PLC0415

    try:
        statistics: dict[str, list[StatisticsRow]] = await hass.async_add_executor_job(
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
    except Exception as e:
        msg = f"Failed to fetch statistics: {e}"
        raise ValueError(msg) from e

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


def cycle_forecast_to_horizon(
    forecast: list[ForecastPoint],
    history_days: int,
    horizon_end: datetime,
) -> list[ForecastPoint]:
    """Repeat/cycle forecast series until it covers the full horizon.

    If we have N days of history and the horizon extends beyond that,
    repeat the pattern by shifting forward by N days each cycle.

    Args:
        forecast: Original forecast series (already shifted once)
        history_days: Number of days in one cycle
        horizon_end: End time of the horizon to fill

    Returns:
        Extended list of ForecastPoints covering the full horizon.

    """
    if not forecast:
        return forecast

    cycle_duration = timedelta(days=history_days)
    first_time = forecast[0].time

    # Calculate how many cycles we need
    horizon_span = horizon_end - first_time
    if horizon_span <= timedelta():
        return forecast

    cycles_needed = int(horizon_span / cycle_duration) + 1

    # Build extended series with all needed cycles
    extended: list[ForecastPoint] = list(forecast)
    for cycle in range(1, cycles_needed + 1):
        cycle_shift = cycle_duration * cycle
        for point in forecast:
            new_time = point.time + cycle_shift
            if new_time > horizon_end:
                break
            extended.append(ForecastPoint(time=new_time, value=point.value))

    return extended


class HistoricalShiftForecaster:
    """Forecaster that builds forecasts from sensor historical statistics.

    When a sensor doesn't have a forecast attribute, this forecaster fetches
    historical data, shifts it forward, and repeats to fill the horizon.
    """

    def __init__(self, history_days: int = 7) -> None:
        """Initialize the forecaster.

        Args:
            history_days: Number of days of history to fetch and shift forward.

        """
        self._history_days = history_days

    @property
    def history_days(self) -> int:
        """Return the number of history days used for forecasting."""
        return self._history_days

    async def available(self, hass: HomeAssistant, entity_id: str) -> bool:
        """Check if we can generate a forecast for the given sensor.

        Args:
            hass: Home Assistant instance
            entity_id: The sensor entity ID

        Returns:
            True if the recorder component is available and sensor exists.

        """
        if "recorder" not in hass.config.components:
            return False

        return hass.states.get(entity_id) is not None

    async def generate_forecast(
        self,
        hass: HomeAssistant,
        entity_id: str,
        horizon_hours: int = 168,
    ) -> ForecastResult:
        """Generate a forecast by shifting historical data forward.

        Args:
            hass: Home Assistant instance
            entity_id: Sensor entity ID to fetch history for
            horizon_hours: How far into the future to forecast (default 7 days = 168 hours)

        Returns:
            ForecastResult with the generated forecast.

        Raises:
            ValueError: If no historical data is available.

        """
        now = dt_util.now()
        start_time = now - timedelta(days=self._history_days)
        end_time = now
        horizon_end = now + timedelta(hours=horizon_hours)

        # Fetch historical statistics
        try:
            statistics = await get_statistics_for_sensor(hass, entity_id, start_time, end_time)
        except ValueError:
            _LOGGER.warning("Failed to get statistics for %s", entity_id)
            raise

        if not statistics:
            msg = f"No historical data available for {entity_id}"
            raise ValueError(msg)

        # Shift history forward to create forecast
        forecast = shift_history_to_forecast(statistics, self._history_days)

        if not forecast:
            msg = f"No valid forecast points generated for {entity_id}"
            raise ValueError(msg)

        # Cycle/repeat to fill the full horizon
        forecast = cycle_forecast_to_horizon(forecast, self._history_days, horizon_end)

        return ForecastResult(
            forecast=forecast,
            source_entity=entity_id,
            history_days=self._history_days,
            generated_at=now,
        )
