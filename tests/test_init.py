"""Tests for the HAFO integration initialization."""

from unittest.mock import AsyncMock, patch

from homeassistant.core import HomeAssistant
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.hafo.const import (
    CONF_FORECAST_TYPE,
    CONF_HISTORY_DAYS,
    CONF_SOURCE_ENTITY,
    DOMAIN,
    FORECAST_TYPE_HISTORICAL_SHIFT,
)
from custom_components.hafo.coordinator import create_forecaster
from custom_components.hafo.forecasters.historical_shift import HistoricalShiftForecaster


@pytest.fixture
def mock_config_entry(hass: HomeAssistant) -> MockConfigEntry:
    """Create a mock config entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test Forecast",
        data={
            CONF_SOURCE_ENTITY: "sensor.test_power",
            CONF_HISTORY_DAYS: 7,
            CONF_FORECAST_TYPE: FORECAST_TYPE_HISTORICAL_SHIFT,
        },
        entry_id="test_entry_id",
    )
    entry.add_to_hass(hass)
    return entry


async def test_forecaster_creation(hass: HomeAssistant, mock_config_entry: MockConfigEntry) -> None:
    """Test that forecaster can be created and configured."""
    # Set up a test entity
    hass.states.async_set("sensor.test_power", "100.0", {"unit_of_measurement": "W"})

    # Create forecaster via factory
    forecaster = create_forecaster(hass, mock_config_entry)

    assert forecaster is not None
    assert isinstance(forecaster, HistoricalShiftForecaster)
    assert forecaster.source_entity == "sensor.test_power"
    assert forecaster.history_days == 7


async def test_forecaster_update(hass: HomeAssistant, mock_config_entry: MockConfigEntry) -> None:
    """Test that forecaster can perform update."""
    hass.states.async_set("sensor.test_power", "100.0", {"unit_of_measurement": "W"})

    forecaster = create_forecaster(hass, mock_config_entry)

    # Mock the update to avoid recorder dependency
    with patch.object(forecaster, "_async_update_data", new_callable=AsyncMock, return_value=None):
        await forecaster.async_refresh()

    # Verify we can access the data
    assert forecaster.last_update_success is True


async def test_forecaster_cleanup(hass: HomeAssistant, mock_config_entry: MockConfigEntry) -> None:
    """Test that forecaster cleanup works."""
    hass.states.async_set("sensor.test_power", "100.0", {"unit_of_measurement": "W"})

    forecaster = create_forecaster(hass, mock_config_entry)

    # Cleanup should not raise
    forecaster.cleanup()


async def test_create_forecaster_unknown_type(hass: HomeAssistant) -> None:
    """Test that create_forecaster raises for unknown forecast type."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test Forecast",
        data={
            CONF_SOURCE_ENTITY: "sensor.test_power",
            CONF_HISTORY_DAYS: 7,
            CONF_FORECAST_TYPE: "unknown_type",
        },
        entry_id="test_entry_id",
    )
    entry.add_to_hass(hass)

    with pytest.raises(ValueError, match="Unknown forecast type"):
        create_forecaster(hass, entry)
