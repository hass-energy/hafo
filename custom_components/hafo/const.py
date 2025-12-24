"""Constants for the Home Assistant Forecaster integration."""

from typing import Final

DOMAIN: Final = "hafo"

# Configuration keys
CONF_SOURCE_ENTITY: Final = "source_entity"
CONF_HISTORY_DAYS: Final = "history_days"
CONF_FORECAST_TYPE: Final = "forecast_type"
CONF_INPUT_ENTITIES: Final = "input_entities"
CONF_OUTPUT_ENTITY: Final = "output_entity"
CONF_RIVER_MODEL_TYPE: Final = "river_model_type"
CONF_FORECAST_HOURS: Final = "forecast_hours"

# Forecast types
FORECAST_TYPE_HISTORICAL_SHIFT: Final = "historical_shift"
FORECAST_TYPE_RIVER_ML: Final = "river_ml"

# RiverML model types
RIVER_MODEL_SNARIMAX: Final = "snarimax"
RIVER_MODEL_LINEAR: Final = "linear"

# Default values
DEFAULT_HISTORY_DAYS: Final = 7
DEFAULT_FORECAST_TYPE: Final = FORECAST_TYPE_HISTORICAL_SHIFT
DEFAULT_FORECAST_HOURS: Final = 168  # 7 days at hourly cadence
DEFAULT_RIVER_MODEL_TYPE: Final = RIVER_MODEL_SNARIMAX

# Attribute keys
ATTR_FORECAST: Final = "forecast"
ATTR_LAST_UPDATED: Final = "last_forecast_update"
ATTR_SOURCE_ENTITY: Final = "source_entity"
ATTR_HISTORY_DAYS: Final = "history_days"
ATTR_MODEL_METRICS: Final = "model_metrics"
