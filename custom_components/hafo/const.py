"""Constants for the Home Assistant Forecaster integration."""

from typing import Final

DOMAIN: Final = "hafo"

# Configuration keys
CONF_SOURCE_ENTITY: Final = "source_entity"
CONF_HISTORY_DAYS: Final = "history_days"
CONF_FORECAST_TYPE: Final = "forecast_type"

# Forecast types
FORECAST_TYPE_HISTORICAL_SHIFT: Final = "historical_shift"

# Default values
DEFAULT_HISTORY_DAYS: Final = 7
DEFAULT_FORECAST_TYPE: Final = FORECAST_TYPE_HISTORICAL_SHIFT

# Attribute keys
ATTR_FORECAST: Final = "forecast"
ATTR_LAST_UPDATED: Final = "last_forecast_update"
ATTR_SOURCE_ENTITY: Final = "source_entity"
ATTR_HISTORY_DAYS: Final = "history_days"
