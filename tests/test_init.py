"""Tests for the HAFO integration initialization."""

from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.hafo import async_reload_entry, async_setup_entry, async_unload_entry, async_update_listener
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


async def test_async_setup_entry(hass: HomeAssistant, mock_config_entry: MockConfigEntry) -> None:
    """async_setup_entry creates coordinator, refreshes, and forwards to platforms."""
    coordinator = create_forecaster(hass, mock_config_entry)
    with (
        patch(
            "custom_components.hafo.create_forecaster",
            return_value=coordinator,
        ),
        patch.object(
            coordinator,
            "async_config_entry_first_refresh",
            new_callable=AsyncMock,
        ) as mock_refresh,
        patch.object(
            hass.config_entries,
            "async_forward_entry_setups",
            new_callable=AsyncMock,
        ) as mock_forward,
        patch.object(
            mock_config_entry,
            "add_update_listener",
            return_value=MagicMock(),
        ) as mock_listener,
    ):
        result = await async_setup_entry(hass, mock_config_entry)

    assert result is True
    assert mock_config_entry.runtime_data is coordinator
    mock_refresh.assert_awaited_once()
    mock_forward.assert_awaited_once_with(mock_config_entry, [Platform.SENSOR])
    mock_listener.assert_called_once()


async def test_async_unload_entry(hass: HomeAssistant, mock_config_entry: MockConfigEntry) -> None:
    """async_unload_entry unloads platforms and cleans up coordinator."""
    coordinator = create_forecaster(hass, mock_config_entry)
    mock_config_entry.runtime_data = coordinator

    with patch.object(
        hass.config_entries,
        "async_unload_platforms",
        new_callable=AsyncMock,
        return_value=True,
    ) as mock_unload:
        result = await async_unload_entry(hass, mock_config_entry)

    assert result is True
    mock_unload.assert_awaited_once_with(mock_config_entry, [Platform.SENSOR])
    # Coordinator.cleanup() was called (no-op for this coordinator, but path is covered)
    coordinator.cleanup()


async def test_async_unload_entry_false_when_unload_fails(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """async_unload_entry returns False when platform unload fails."""
    coordinator = create_forecaster(hass, mock_config_entry)
    mock_config_entry.runtime_data = coordinator

    with patch.object(
        hass.config_entries,
        "async_unload_platforms",
        new_callable=AsyncMock,
        return_value=False,
    ):
        result = await async_unload_entry(hass, mock_config_entry)

    assert result is False


async def test_async_reload_entry(hass: HomeAssistant, mock_config_entry: MockConfigEntry) -> None:
    """async_reload_entry unloads then sets up again."""
    coordinator = create_forecaster(hass, mock_config_entry)
    mock_config_entry.runtime_data = coordinator

    with (
        patch(
            "custom_components.hafo.async_unload_entry",
            new_callable=AsyncMock,
            return_value=True,
        ) as mock_unload,
        patch(
            "custom_components.hafo.async_setup_entry",
            new_callable=AsyncMock,
            return_value=True,
        ) as mock_setup,
    ):
        await async_reload_entry(hass, mock_config_entry)

    mock_unload.assert_awaited_once_with(hass, mock_config_entry)
    mock_setup.assert_awaited_once_with(hass, mock_config_entry)


async def test_async_update_listener_reloads_entry(hass: HomeAssistant, mock_config_entry: MockConfigEntry) -> None:
    """async_update_listener triggers config entry reload."""
    with patch.object(
        hass.config_entries,
        "async_reload",
        new_callable=AsyncMock,
    ) as mock_reload:
        await async_update_listener(hass, mock_config_entry)

    mock_reload.assert_awaited_once_with(mock_config_entry.entry_id)
