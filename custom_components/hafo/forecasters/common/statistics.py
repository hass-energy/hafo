"""Statistics utilities for fetching historical data from the recorder."""

from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Any, Literal

from homeassistant.core import HomeAssistant

# Type alias for statistics rows - accepts various dict-like structures
type StatisticsRowLike = Mapping[str, Any]

# Type aliases for statistics API
type StatisticPeriod = Literal["5minute", "hour", "day", "week", "month"]
type StatisticType = Literal["change", "last_reset", "max", "mean", "min", "state", "sum"]


async def get_statistics_for_sensor(
    hass: HomeAssistant,
    entity_id: str,
    start_time: datetime,
    end_time: datetime,
) -> Sequence[StatisticsRowLike]:
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
    result = await get_statistics_for_sensors(hass, {entity_id}, start_time, end_time)
    return result.get(entity_id, [])


async def get_statistics_for_sensors(
    hass: HomeAssistant,
    entity_ids: set[str],
    start_time: datetime,
    end_time: datetime,
    *,
    period: StatisticPeriod = "hour",
    types: set[StatisticType] | None = None,
) -> Mapping[str, Sequence[StatisticsRowLike]]:
    """Fetch statistics for multiple sensor entities.

    Args:
        hass: Home Assistant instance
        entity_ids: Set of sensor entity IDs to fetch statistics for
        start_time: Start of the time range
        end_time: End of the time range
        period: Statistics period ('5minute', 'hour', 'day', 'week', 'month')
        types: Set of statistics types to fetch (default: {'mean'})

    Returns:
        Dictionary mapping entity IDs to their statistics rows.

    Raises:
        ValueError: If the recorder is not available or not set up.

    """
    stat_types: set[StatisticType] = types if types is not None else {"mean"}

    if "recorder" not in hass.config.components:
        msg = "Recorder component not loaded"
        raise ValueError(msg)

    try:
        # Recorder is an optional after_dependency, so we import inline after checking it's loaded
        from homeassistant.components.recorder.statistics import statistics_during_period  # noqa: PLC0415
        from homeassistant.helpers.recorder import DATA_INSTANCE  # noqa: PLC0415

        if DATA_INSTANCE not in hass.data:
            msg = "Recorder not initialized"
            raise ValueError(msg)
    except ImportError:
        msg = "Recorder component not available"
        raise ValueError(msg) from None

    try:
        statistics = await hass.async_add_executor_job(
            lambda: statistics_during_period(
                hass,
                start_time,
                end_time,
                entity_ids,
                period,
                None,
                stat_types,
            )
        )
    except Exception as e:
        msg = f"Failed to fetch statistics: {e}"
        raise ValueError(msg) from e

    return statistics
