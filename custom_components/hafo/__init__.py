"""The Home Assistant Forecaster integration."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .coordinator import HafoDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]

type HafoConfigEntry = ConfigEntry[HafoDataUpdateCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: HafoConfigEntry) -> bool:
    """Set up Home Assistant Forecaster from a config entry."""
    _LOGGER.info("Setting up HAFO forecaster: %s", entry.title)

    # Create and store coordinator
    coordinator = HafoDataUpdateCoordinator(hass, entry)
    entry.runtime_data = coordinator

    # Perform initial data fetch
    await coordinator.async_config_entry_first_refresh()

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register update listener for config changes
    entry.async_on_unload(entry.add_update_listener(async_update_listener))

    _LOGGER.info("HAFO forecaster setup complete: %s", entry.title)
    return True


async def async_update_listener(hass: HomeAssistant, entry: HafoConfigEntry) -> None:
    """Handle options update."""
    _LOGGER.info("HAFO configuration changed, reloading: %s", entry.title)
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: HafoConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("Unloading HAFO forecaster: %s", entry.title)

    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        # Clean up coordinator resources
        coordinator = entry.runtime_data
        coordinator.cleanup()

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: HafoConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
