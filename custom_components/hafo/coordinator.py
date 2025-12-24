"""Forecaster factory for Home Assistant Forecaster.

This module provides factory functions to create the appropriate forecaster
coordinator based on the forecast type configured in the entry.
"""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_FORECAST_TYPE, FORECAST_TYPE_HISTORICAL_SHIFT
from .forecasters.historical_shift import ForecastResult, HistoricalShiftForecaster

# Type alias for any forecaster coordinator
type ForecasterCoordinator = HistoricalShiftForecaster

# Mapping of forecast types to their coordinator classes
FORECASTER_TYPES: dict[str, type[ForecasterCoordinator]] = {
    FORECAST_TYPE_HISTORICAL_SHIFT: HistoricalShiftForecaster,
}


def create_forecaster(hass: HomeAssistant, entry: ConfigEntry) -> ForecasterCoordinator:
    """Create the appropriate forecaster coordinator for a config entry.

    Args:
        hass: Home Assistant instance
        entry: Config entry containing the forecast type and settings

    Returns:
        The forecaster coordinator instance

    Raises:
        ValueError: If the forecast type is not recognized

    """
    forecast_type = entry.data.get(CONF_FORECAST_TYPE)

    if forecast_type not in FORECASTER_TYPES:
        msg = f"Unknown forecast type: {forecast_type}"
        raise ValueError(msg)

    forecaster_class = FORECASTER_TYPES[forecast_type]
    return forecaster_class(hass, entry)


__all__ = [
    "ForecastResult",
    "ForecasterCoordinator",
    "create_forecaster",
]
