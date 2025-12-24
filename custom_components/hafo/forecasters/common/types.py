"""Common types for HAFO forecasters."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

# Type alias for statistics - accepts either StatisticsRow or dict-like objects
type StatisticsLike = Mapping[str, Any]


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
    metrics: dict[str, float] = field(default_factory=dict)
