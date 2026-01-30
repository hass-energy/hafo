"""Tests for the Historical Shift forecaster."""

from datetime import UTC, datetime, timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.hafo.const import (
    CONF_FORECAST_TYPE,
    CONF_HISTORY_DAYS,
    CONF_SOURCE_ENTITY,
    DOMAIN,
    FORECAST_TYPE_HISTORICAL_SHIFT,
)
from custom_components.hafo.forecasters import historical_shift as hs
from custom_components.hafo.forecasters.historical_shift import HistoricalShiftForecaster, shift_history_to_forecast

# Tests for shift_history_to_forecast function


def test_shift_timestamps_forward() -> None:
    """Shifts historical timestamps forward by N days."""
    base = datetime(2024, 1, 1, 10, 0, 0, tzinfo=UTC)
    stats: list[dict[str, Any]] = [
        {"start": base, "mean": 2.0},
        {"start": base + timedelta(hours=1), "mean": 3.0},
    ]

    result = shift_history_to_forecast(stats, history_days=7)

    # Should have 2 forecast points
    assert len(result) == 2

    # Timestamps should be shifted forward by 7 days
    expected_base = base + timedelta(days=7)
    assert result[0].time == expected_base
    assert result[1].time == expected_base + timedelta(hours=1)

    # Values should be unchanged
    assert result[0].value == pytest.approx(2.0)
    assert result[1].value == pytest.approx(3.0)


def test_shift_returns_empty_for_no_statistics() -> None:
    """Returns empty list when no statistics provided."""
    result = shift_history_to_forecast([], history_days=7)
    assert result == []


def test_shift_skips_entries_with_missing_values() -> None:
    """Skips entries without start or mean values."""
    base = datetime(2024, 1, 1, 10, 0, 0, tzinfo=UTC)
    stats: list[dict[str, Any]] = [
        {"start": base, "mean": 2.0},
        {"start": base + timedelta(hours=1), "mean": None},  # Missing mean
        {"start": None, "mean": 3.0},  # Missing start
    ]

    result = shift_history_to_forecast(stats, history_days=7)

    # Only the first entry should be included
    assert len(result) == 1
    assert result[0].value == pytest.approx(2.0)


def test_shift_handles_timestamp_as_float() -> None:
    """Handles statistics with timestamp as float."""
    base = datetime(2024, 1, 1, 10, 0, 0, tzinfo=UTC)
    stats: list[dict[str, Any]] = [
        {"start": base.timestamp(), "mean": 5.0},
    ]

    result = shift_history_to_forecast(stats, history_days=7)

    assert len(result) == 1
    expected_time = base + timedelta(days=7)
    # Compare timestamps since timezone handling may differ
    assert abs(result[0].time.timestamp() - expected_time.timestamp()) < 1
    assert result[0].value == pytest.approx(5.0)


def test_shift_sorts_by_timestamp() -> None:
    """Sorts results by timestamp."""
    base = datetime(2024, 1, 1, 10, 0, 0, tzinfo=UTC)
    # Provide out-of-order statistics
    stats: list[dict[str, Any]] = [
        {"start": base + timedelta(hours=2), "mean": 3.0},
        {"start": base, "mean": 1.0},
        {"start": base + timedelta(hours=1), "mean": 2.0},
    ]

    result = shift_history_to_forecast(stats, history_days=7)

    # Should be sorted by timestamp
    assert result[0].value == pytest.approx(1.0)
    assert result[1].value == pytest.approx(2.0)
    assert result[2].value == pytest.approx(3.0)


def test_shift_skips_invalid_timestamp() -> None:
    """Skips entries with start that cannot be converted to datetime."""
    base = datetime(2024, 1, 1, 10, 0, 0, tzinfo=UTC)
    stats: list[dict[str, Any]] = [
        {"start": base, "mean": 2.0},
        {"start": "not_a_timestamp", "mean": 3.0},
        {"start": base + timedelta(hours=1), "mean": 1.0},
    ]

    result = shift_history_to_forecast(stats, history_days=7)

    assert len(result) == 2
    assert result[0].value == pytest.approx(2.0)
    assert result[1].value == pytest.approx(1.0)


# Tests for HistoricalShiftForecaster class


def _create_mock_entry(hass: HomeAssistant, history_days: int = 7) -> MockConfigEntry:
    """Create a mock config entry for testing."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test Forecast",
        data={
            CONF_SOURCE_ENTITY: "sensor.test",
            CONF_HISTORY_DAYS: history_days,
            CONF_FORECAST_TYPE: FORECAST_TYPE_HISTORICAL_SHIFT,
        },
        entry_id="test_entry_id",
    )
    entry.add_to_hass(hass)
    return entry


def test_forecaster_properties(hass: HomeAssistant) -> None:
    """Forecaster exposes configuration properties."""
    entry = _create_mock_entry(hass, history_days=14)
    forecaster = HistoricalShiftForecaster(hass, entry)

    assert forecaster.history_days == 14
    assert forecaster.source_entity == "sensor.test"
    assert forecaster.entry is entry


async def test_forecaster_generate_forecast_returns_result(
    hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch
) -> None:
    """_generate_forecast() returns a ForecastResult."""
    hass.states.async_set("sensor.test", "100.0")
    entry = _create_mock_entry(hass, history_days=7)
    forecaster = HistoricalShiftForecaster(hass, entry)
    tz = dt_util.get_default_time_zone()

    # Historical data from Jan 1-7
    history_base = datetime(2024, 1, 1, 10, 0, 0, tzinfo=tz)
    mock_stats: list[dict[str, Any]] = [
        {"start": history_base, "mean": 100.0},
        {"start": history_base + timedelta(hours=1), "mean": 200.0},
    ]

    async def mock_get_stats(
        _hass: HomeAssistant,
        _entity_id: str,
        _start_time: datetime,
        _end_time: datetime,
    ) -> list[dict[str, Any]]:
        return mock_stats

    monkeypatch.setattr(hs, "get_statistics_for_sensor", mock_get_stats)

    result = await forecaster._generate_forecast()

    assert result is not None
    assert result.source_entity == "sensor.test"
    assert result.history_days == 7
    # No cycling, so should have exactly 2 points
    assert len(result.forecast) == 2


async def test_forecaster_generate_forecast_raises_when_no_data(
    hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch
) -> None:
    """_generate_forecast() raises when no historical data is available."""
    entry = _create_mock_entry(hass)
    forecaster = HistoricalShiftForecaster(hass, entry)

    async def mock_get_stats(
        _hass: HomeAssistant,
        _entity_id: str,
        _start_time: datetime,
        _end_time: datetime,
    ) -> list[dict[str, Any]]:
        return []

    monkeypatch.setattr(hs, "get_statistics_for_sensor", mock_get_stats)

    with pytest.raises(ValueError, match="No historical data available"):
        await forecaster._generate_forecast()


def test_forecaster_update_interval() -> None:
    """Forecaster has hourly update interval."""
    assert timedelta(hours=1) == HistoricalShiftForecaster.UPDATE_INTERVAL


async def test_forecaster_returns_none_when_no_statistics_exist(
    hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Forecaster returns None when entity has no historical statistics."""
    entry = _create_mock_entry(hass)
    forecaster = HistoricalShiftForecaster(hass, entry)

    async def mock_get_stats(
        _hass: HomeAssistant,
        _entity_id: str,
        _start_time: datetime,
        _end_time: datetime,
    ) -> list[dict[str, Any]]:
        return []

    monkeypatch.setattr(hs, "get_statistics_for_sensor", mock_get_stats)

    result = await forecaster._async_update_data()

    # Should gracefully return None
    assert result is None


async def test_forecaster_async_update_data_returns_result(
    hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch
) -> None:
    """_async_update_data() returns ForecastResult when statistics are available."""
    hass.states.async_set("sensor.test", "100.0")
    entry = _create_mock_entry(hass, history_days=7)
    forecaster = HistoricalShiftForecaster(hass, entry)
    tz = dt_util.get_default_time_zone()
    history_base = datetime(2024, 1, 1, 10, 0, 0, tzinfo=tz)
    mock_stats: list[dict[str, Any]] = [
        {"start": history_base, "mean": 100.0},
        {"start": history_base + timedelta(hours=1), "mean": 200.0},
    ]

    async def mock_get_stats(
        _hass: HomeAssistant,
        _entity_id: str,
        _start_time: datetime,
        _end_time: datetime,
    ) -> list[dict[str, Any]]:
        return mock_stats

    monkeypatch.setattr(hs, "get_statistics_for_sensor", mock_get_stats)

    result = await forecaster._async_update_data()

    assert result is not None
    assert result.source_entity == "sensor.test"
    assert len(result.forecast) == 2


async def test_forecaster_async_update_data_returns_none_on_value_error(
    hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch
) -> None:
    """_async_update_data() returns None when get_statistics raises ValueError."""
    entry = _create_mock_entry(hass)
    forecaster = HistoricalShiftForecaster(hass, entry)

    async def mock_get_stats_raises(
        _hass: HomeAssistant,
        _entity_id: str,
        _start_time: datetime,
        _end_time: datetime,
    ) -> list[dict[str, Any]]:
        msg = "Recorder not available"
        raise ValueError(msg)

    monkeypatch.setattr(hs, "get_statistics_for_sensor", mock_get_stats_raises)

    result = await forecaster._async_update_data()

    assert result is None


async def test_forecaster_generate_forecast_raises_when_forecast_empty(
    hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch
) -> None:
    """_generate_forecast() raises when statistics exist but all rows are skipped."""
    entry = _create_mock_entry(hass)
    forecaster = HistoricalShiftForecaster(hass, entry)

    # Stats with start/mean that get skipped (e.g. all None mean) so forecast is []
    async def mock_get_stats(
        _hass: HomeAssistant,
        _entity_id: str,
        _start_time: datetime,
        _end_time: datetime,
    ) -> list[dict[str, Any]]:
        return [{"start": None, "mean": 1.0}, {"start": datetime(2024, 1, 1, tzinfo=UTC), "mean": None}]

    monkeypatch.setattr(hs, "get_statistics_for_sensor", mock_get_stats)

    with pytest.raises(ValueError, match="No valid forecast points"):
        await forecaster._generate_forecast()
