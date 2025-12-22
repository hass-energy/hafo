"""Tests for the Historical Shift forecaster."""

from datetime import UTC, datetime, timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
import pytest

from custom_components.hafo.forecasters import historical_shift as hs
from custom_components.hafo.forecasters.historical_shift import (
    ForecastPoint,
    HistoricalShiftForecaster,
    cycle_forecast_to_horizon,
    shift_history_to_forecast,
)


class TestShiftHistoryToForecast:
    """Tests for shift_history_to_forecast function."""

    def test_shifts_timestamps_forward(self) -> None:
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
        assert result[0].datetime == expected_base
        assert result[1].datetime == expected_base + timedelta(hours=1)

        # Values should be unchanged
        assert result[0].value == pytest.approx(2.0)
        assert result[1].value == pytest.approx(3.0)

    def test_returns_empty_for_no_statistics(self) -> None:
        """Returns empty list when no statistics provided."""
        result = shift_history_to_forecast([], history_days=7)
        assert result == []

    def test_skips_entries_with_missing_values(self) -> None:
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

    def test_handles_timestamp_as_float(self) -> None:
        """Handles statistics with timestamp as float."""
        base = datetime(2024, 1, 1, 10, 0, 0, tzinfo=UTC)
        stats: list[dict[str, Any]] = [
            {"start": base.timestamp(), "mean": 5.0},
        ]

        result = shift_history_to_forecast(stats, history_days=7)

        assert len(result) == 1
        expected_time = base + timedelta(days=7)
        # Compare timestamps since timezone handling may differ
        assert abs(result[0].datetime.timestamp() - expected_time.timestamp()) < 1
        assert result[0].value == pytest.approx(5.0)

    def test_sorts_by_timestamp(self) -> None:
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


class TestCycleForecastToHorizon:
    """Tests for cycle_forecast_to_horizon function."""

    def test_returns_empty_for_empty_forecast(self) -> None:
        """Returns empty list when forecast is empty."""
        horizon_end = datetime(2024, 1, 15, 0, 0, 0, tzinfo=UTC)
        result = cycle_forecast_to_horizon([], history_days=7, horizon_end=horizon_end)
        assert result == []

    def test_no_cycle_when_forecast_covers_horizon(self) -> None:
        """Doesn't add cycles when forecast already covers horizon."""
        base = datetime(2024, 1, 8, 10, 0, 0, tzinfo=UTC)
        forecast = [
            ForecastPoint(datetime=base, value=100.0),
            ForecastPoint(datetime=base + timedelta(hours=1), value=200.0),
        ]
        # Horizon ends before the last forecast point
        horizon_end = base + timedelta(minutes=30)

        result = cycle_forecast_to_horizon(forecast, history_days=7, horizon_end=horizon_end)

        # Should be unchanged
        assert len(result) == 2
        assert result[0].value == 100.0
        assert result[1].value == 200.0

    def test_repeats_to_fill_horizon(self) -> None:
        """Repeats forecast pattern to fill a longer horizon."""
        base = datetime(2024, 1, 8, 0, 0, 0, tzinfo=UTC)
        # 2 days of history data (shifted to future)
        forecast = [
            ForecastPoint(datetime=base, value=100.0),  # Day 1, 00:00
            ForecastPoint(datetime=base + timedelta(hours=12), value=200.0),  # Day 1, 12:00
            ForecastPoint(datetime=base + timedelta(days=1), value=150.0),  # Day 2, 00:00
            ForecastPoint(datetime=base + timedelta(days=1, hours=12), value=250.0),  # Day 2, 12:00
        ]

        # Horizon is 6 days (should repeat 3 times)
        horizon_end = base + timedelta(days=6)

        result = cycle_forecast_to_horizon(forecast, history_days=2, horizon_end=horizon_end)

        # Should have more points than original (3 cycles worth)
        assert len(result) > 4
        # First 4 should be unchanged
        assert result[0].value == 100.0
        assert result[1].value == 200.0
        assert result[2].value == 150.0
        assert result[3].value == 250.0
        # Cycle 2 should have same values at shifted times
        assert result[4].value == 100.0  # First value repeats
        assert result[5].value == 200.0

    def test_partial_cycle_at_end(self) -> None:
        """Stops cycling when horizon is reached mid-cycle."""
        base = datetime(2024, 1, 8, 0, 0, 0, tzinfo=UTC)
        forecast = [
            ForecastPoint(datetime=base, value=100.0),
            ForecastPoint(datetime=base + timedelta(hours=12), value=200.0),
        ]

        # Horizon is 1.5 cycles (18 hours into a 24-hour pattern)
        horizon_end = base + timedelta(hours=30)

        result = cycle_forecast_to_horizon(forecast, history_days=1, horizon_end=horizon_end)

        # Should have 3 points: original 2 + first point of cycle 2
        assert len(result) == 3
        assert result[0].value == 100.0
        assert result[1].value == 200.0
        assert result[2].value == 100.0  # First point repeated


class TestHistoricalShiftForecaster:
    """Tests for HistoricalShiftForecaster class."""

    def test_default_history_days(self) -> None:
        """Forecaster uses default history days when not specified."""
        forecaster = HistoricalShiftForecaster()
        assert forecaster.history_days == 7

    def test_custom_history_days(self) -> None:
        """Forecaster respects custom history days."""
        forecaster = HistoricalShiftForecaster(history_days=14)
        assert forecaster.history_days == 14

    @pytest.mark.asyncio
    async def test_available_when_recorder_loaded_and_sensor_exists(self, hass: HomeAssistant) -> None:
        """available() returns True when recorder is loaded and sensor exists."""
        hass.config.components.add("recorder")
        hass.states.async_set("sensor.test", "5.0")

        forecaster = HistoricalShiftForecaster()
        assert await forecaster.available(hass, "sensor.test")

    @pytest.mark.asyncio
    async def test_not_available_when_recorder_missing(
        self, hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """available() returns False when recorder is not loaded."""
        monkeypatch.setattr(
            hass.config.components,
            "__contains__",
            lambda component: component != "recorder",
        )
        forecaster = HistoricalShiftForecaster()
        assert not await forecaster.available(hass, "sensor.test")

    @pytest.mark.asyncio
    async def test_not_available_when_sensor_missing(self, hass: HomeAssistant) -> None:
        """available() returns False when sensor doesn't exist."""
        hass.config.components.add("recorder")
        forecaster = HistoricalShiftForecaster()
        assert not await forecaster.available(hass, "sensor.nonexistent")

    @pytest.mark.asyncio
    async def test_generate_forecast_returns_result(
        self, hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """generate_forecast() returns a ForecastResult."""
        forecaster = HistoricalShiftForecaster(history_days=7)
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

        result = await forecaster.generate_forecast(hass, "sensor.test")

        assert result is not None
        assert result.source_entity == "sensor.test"
        assert result.history_days == 7
        assert len(result.forecast) >= 2

    @pytest.mark.asyncio
    async def test_generate_forecast_raises_when_no_data(
        self, hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """generate_forecast() raises when no historical data is available."""
        forecaster = HistoricalShiftForecaster()

        async def mock_get_stats(
            _hass: HomeAssistant,
            _entity_id: str,
            _start_time: datetime,
            _end_time: datetime,
        ) -> list[dict[str, Any]]:
            return []

        monkeypatch.setattr(hs, "get_statistics_for_sensor", mock_get_stats)

        with pytest.raises(ValueError, match="No historical data available"):
            await forecaster.generate_forecast(hass, "sensor.test")
