"""Fixtures for HAFO scenario tests with fake recorder statistics."""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, TypedDict

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util


class FakeStatistic(TypedDict):
    """A fake statistic entry to insert into the recorder."""

    start: datetime
    mean: float


class ScenarioConfig(TypedDict):
    """Configuration for a scenario test."""

    entity_id: str
    history_days: int
    freeze_time: str
    statistics: list[dict[str, Any]]  # List of {"start": str, "mean": float}
    expected_forecast_length: int


class ScenarioData(TypedDict):
    """Full scenario test data."""

    config: ScenarioConfig


@pytest.fixture
def scenario_path(request: pytest.FixtureRequest) -> Path:
    """Get the path to the current scenario directory from parameterized test."""
    return request.param  # type: ignore[no-any-return]


# Note: Use the `recorder_mock` fixture from pytest-homeassistant-custom-component
# which provides an in-memory recorder for testing.


async def add_fake_statistics(
    hass: HomeAssistant,
    entity_id: str,
    statistics: list[dict[str, Any]],
) -> None:
    """Add fake statistics to the recorder for testing.

    Uses async_add_external_statistics to insert test data that can be
    queried by the forecaster.

    Args:
        hass: Home Assistant instance
        entity_id: The sensor entity ID to add statistics for
        statistics: List of statistics entries with 'start' (ISO string) and 'mean' (float)

    """
    from homeassistant.components.recorder.models import (  # noqa: PLC0415
        StatisticMeanType,
    )
    from homeassistant.components.recorder.statistics import (  # noqa: PLC0415
        async_add_external_statistics,
    )

    # Convert to the external statistics format
    # We use a custom source prefix for test data
    source = "hafo_test"
    statistic_id = f"{source}:{entity_id.replace('.', '_')}"

    metadata: dict[str, Any] = {
        "has_sum": False,
        "mean_type": StatisticMeanType.ARITHMETIC,
        "name": f"Test statistics for {entity_id}",
        "source": source,
        "statistic_id": statistic_id,
        "unit_class": "power",  # Generic unit class
        "unit_of_measurement": "W",
    }

    # Convert ISO strings to datetime objects
    external_statistics: list[dict[str, Any]] = []
    for stat in statistics:
        start = dt_util.parse_datetime(stat["start"]) if isinstance(stat["start"], str) else stat["start"]
        if start is None:
            continue

        external_statistics.append({
            "start": start,
            "mean": stat["mean"],
            "min": stat.get("min", stat["mean"]),
            "max": stat.get("max", stat["mean"]),
        })

    # Add the statistics - type: ignore needed for TypedDict compatibility
    async_add_external_statistics(hass, metadata, external_statistics)  # type: ignore[arg-type]

    # Wait for the statistics to be recorded
    # The recorder processes statistics asynchronously, so we need to wait for it
    from homeassistant.helpers.recorder import get_instance  # noqa: PLC0415

    instance = get_instance(hass)
    await instance.async_block_till_done()


def generate_hourly_statistics(
    start: datetime,
    hours: int,
    base_value: float = 100.0,
    variation: float = 50.0,
) -> list[dict[str, Any]]:
    """Generate fake hourly statistics with a simple pattern.

    Creates a sinusoidal pattern that varies throughout the day,
    simulating typical household power consumption.

    Args:
        start: Starting datetime for the statistics
        hours: Number of hours of statistics to generate
        base_value: Base power value in watts
        variation: Amplitude of variation

    Returns:
        List of statistics entries with 'start' and 'mean' fields

    """
    import math  # noqa: PLC0415

    statistics_list: list[dict[str, Any]] = []

    for hour_offset in range(hours):
        timestamp = start + timedelta(hours=hour_offset)
        hour_of_day = timestamp.hour

        # Create a pattern that peaks in morning (8am) and evening (6pm)
        # and is low at night
        morning_peak = math.exp(-((hour_of_day - 8) ** 2) / 8)
        evening_peak = math.exp(-((hour_of_day - 18) ** 2) / 8)
        night_dip = 1.0 - 0.6 * math.exp(-((hour_of_day - 3) ** 2) / 4)

        pattern = (morning_peak + evening_peak) * night_dip
        value = base_value + variation * pattern

        statistics_list.append({
            "start": timestamp.isoformat(),
            "mean": round(value, 2),
        })

    return statistics_list
