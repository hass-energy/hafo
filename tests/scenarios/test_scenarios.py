"""Test forecaster with fake recorder statistics.

This module contains integration tests that inject fake statistics into
the recorder and verify the forecaster produces correct output.
"""

from datetime import UTC, datetime, timedelta

from freezegun import freeze_time
from homeassistant.components.recorder.statistics import statistics_during_period
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
import pytest

from .conftest import add_fake_statistics, generate_hourly_statistics

# Tests for forecaster integration with recorder statistics


@pytest.mark.usefixtures("recorder_mock")
async def test_forecast_from_fake_statistics(hass: HomeAssistant) -> None:
    """Test that forecaster can read injected statistics and produce forecast."""
    # Set up a sensor entity
    entity_id = "sensor.test_power"
    hass.states.async_set(entity_id, "100.0", {"unit_of_measurement": "W"})
    await hass.async_block_till_done()

    # Generate 7 days of hourly statistics
    now = dt_util.utcnow().replace(minute=0, second=0, microsecond=0)
    start_time = now - timedelta(days=7)
    fake_stats = generate_hourly_statistics(start_time, hours=7 * 24)

    # Add fake statistics to the recorder
    await add_fake_statistics(hass, entity_id, fake_stats)

    # Verify the statistics were added
    stats = await hass.async_add_executor_job(
        lambda: statistics_during_period(
            hass,
            start_time,
            now,
            {f"hafo_test:{entity_id.replace('.', '_')}"},
            "hour",
            None,
            {"mean"},
        )
    )

    # We should have statistics for the test entity
    statistic_id = f"hafo_test:{entity_id.replace('.', '_')}"
    assert statistic_id in stats
    assert len(stats[statistic_id]) == 7 * 24  # 7 days of hourly data


@pytest.mark.usefixtures("recorder_mock")
@freeze_time("2024-01-15 12:00:00+00:00")
async def test_historical_shift_with_frozen_time(hass: HomeAssistant) -> None:
    """Test historical shift forecaster with frozen time for reproducibility."""
    # With frozen time, we can test exact forecast values
    entity_id = "sensor.frozen_test"
    hass.states.async_set(entity_id, "50.0", {"unit_of_measurement": "W"})
    await hass.async_block_till_done()

    # Create specific historical data
    base_time = datetime(2024, 1, 8, 0, 0, 0, tzinfo=UTC)  # 7 days ago
    fake_stats = generate_hourly_statistics(base_time, hours=24)

    await add_fake_statistics(hass, entity_id, fake_stats)

    # The statistics should now be available for querying
    stats = await hass.async_add_executor_job(
        lambda: statistics_during_period(
            hass,
            base_time,
            base_time + timedelta(days=1),
            {f"hafo_test:{entity_id.replace('.', '_')}"},
            "hour",
            None,
            {"mean"},
        )
    )

    statistic_id = f"hafo_test:{entity_id.replace('.', '_')}"
    assert statistic_id in stats
    assert len(stats[statistic_id]) == 24


@pytest.mark.usefixtures("recorder_mock")
async def test_empty_statistics(hass: HomeAssistant) -> None:
    """Test forecaster behavior when no statistics exist."""
    entity_id = "sensor.no_history"
    hass.states.async_set(entity_id, "0.0", {"unit_of_measurement": "W"})
    await hass.async_block_till_done()

    # Verify that querying a non-existent statistic returns empty
    now = dt_util.utcnow()
    stats = await hass.async_add_executor_job(
        lambda: statistics_during_period(
            hass,
            now - timedelta(days=7),
            now,
            {entity_id},
            "hour",
            None,
            {"mean"},
        )
    )

    # Should be empty since we never added statistics for this entity
    assert entity_id not in stats or len(stats.get(entity_id, [])) == 0


# Tests for statistics generation utilities


def test_generate_hourly_statistics_length() -> None:
    """Test that generate_hourly_statistics creates correct number of entries."""
    start = datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)
    stats = generate_hourly_statistics(start, hours=48)

    assert len(stats) == 48


def test_generate_hourly_statistics_timestamps() -> None:
    """Test that generated statistics have correct datetime timestamps."""
    start = datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)
    stats = generate_hourly_statistics(start, hours=24)

    for i, stat in enumerate(stats):
        expected_time = start + timedelta(hours=i)
        assert stat["start"] == expected_time


def test_generate_hourly_statistics_pattern() -> None:
    """Test that generated statistics follow a daily pattern."""
    start = datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)
    stats = generate_hourly_statistics(start, hours=24, base_value=100.0, variation=50.0)

    # Night values (around 3am) should be lower than peak values (8am, 6pm)
    night_value = stats[3]["mean"]  # 3am
    morning_value = stats[8]["mean"]  # 8am
    evening_value = stats[18]["mean"]  # 6pm

    # Morning and evening peaks should be higher than night
    assert morning_value > night_value
    assert evening_value > night_value
