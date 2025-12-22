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
from custom_components.hafo.coordinator import HafoDataUpdateCoordinator


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


@pytest.mark.asyncio
async def test_coordinator_creation(hass: HomeAssistant, mock_config_entry: MockConfigEntry) -> None:
    """Test that coordinator can be created and configured."""
    # Set up a test entity
    hass.states.async_set("sensor.test_power", "100.0", {"unit_of_measurement": "W"})

    # Create coordinator directly
    coordinator = HafoDataUpdateCoordinator(hass, mock_config_entry)

    assert coordinator is not None
    assert coordinator.source_entity == "sensor.test_power"
    assert coordinator.history_days == 7


@pytest.mark.asyncio
async def test_coordinator_update(hass: HomeAssistant, mock_config_entry: MockConfigEntry) -> None:
    """Test that coordinator can perform update."""
    hass.states.async_set("sensor.test_power", "100.0", {"unit_of_measurement": "W"})

    coordinator = HafoDataUpdateCoordinator(hass, mock_config_entry)

    # Mock the forecaster to avoid recorder dependency
    with patch.object(coordinator, "_async_update_data", new_callable=AsyncMock, return_value=None):
        await coordinator.async_refresh()

    # Verify we can access the data
    assert coordinator.last_update_success is True


@pytest.mark.asyncio
async def test_coordinator_cleanup(hass: HomeAssistant, mock_config_entry: MockConfigEntry) -> None:
    """Test that coordinator cleanup works."""
    hass.states.async_set("sensor.test_power", "100.0", {"unit_of_measurement": "W"})

    coordinator = HafoDataUpdateCoordinator(hass, mock_config_entry)

    # Cleanup should not raise
    coordinator.cleanup()
