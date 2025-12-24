"""Common utilities for HAFO forecasters."""

from .statistics import get_statistics_for_sensor, get_statistics_for_sensors
from .types import ForecastPoint, ForecastResult, StatisticsLike

__all__ = [
    "ForecastPoint",
    "ForecastResult",
    "StatisticsLike",
    "get_statistics_for_sensor",
    "get_statistics_for_sensors",
]
