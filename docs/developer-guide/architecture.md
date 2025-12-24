# Architecture

HAFO follows a simple, focused architecture designed for extensibility.

## Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Home Assistant                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌──────────────┐    ┌───────────────┐  │
│  │ Config Flow │───▶│ Forecaster   │───▶│ Forecast      │  │
│  │             │    │ Coordinator  │    │ Sensor        │  │
│  └─────────────┘    └──────┬───────┘    └───────────────┘  │
│                            │                                │
│                     ┌──────▼───────┐                        │
│                     │ Recorder     │                        │
│                     │ Statistics   │                        │
│                     └──────────────┘                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Components

### Config Flow (`config_flow.py`)

Handles the UI configuration for creating forecast helpers.
Uses Home Assistant's helper pattern for entity creation.

### Forecasters (`forecasters/`)

Each forecaster **is** a coordinator - they extend `DataUpdateCoordinator` directly.
This design allows each forecaster to determine its own update interval based on its data source characteristics.

The coordinator module (`coordinator.py`) provides a factory function `create_forecaster()` that instantiates the appropriate forecaster type based on configuration.

Currently implemented:

- **HistoricalShiftForecaster**: Extends `DataUpdateCoordinator`, shifts history forward by N days, updates hourly

### Sensor (`sensor.py`)

Exposes the forecast data to Home Assistant.
Provides the forecast as both state (current value) and attributes (full series).

## Data Flow

1. **Configuration**: User creates a forecast helper via the config flow
2. **Initialization**: The appropriate forecaster coordinator is created via `create_forecaster()`
3. **Fetching**: Forecaster fetches statistics from the recorder on its update interval
4. **Transformation**: Historical data is shifted forward to project into the future
5. **Exposure**: Sensor exposes the forecast data

Note: Forecast cycling (repeating patterns to fill longer horizons) is **not** done by HAFO.
Consumers of the forecast (like HAEO) are responsible for cycling data to meet their specific horizon requirements.

## Adding New Forecasters

To add a new forecasting algorithm:

1. Create a new module in `forecasters/`
2. Extend `DataUpdateCoordinator` and implement `_async_update_data()`
3. Define an appropriate `UPDATE_INTERVAL` for the data source
4. Register it in `FORECASTER_TYPES` in `coordinator.py`
5. Add the option to the config flow dropdown
6. Add documentation

## Extension Points

- **New Forecasters**: Add coordinator classes in `forecasters/` and register in `FORECASTER_TYPES`
- **New Sensors**: Add sensor types in `sensor.py`
- **Data Sources**: Each forecaster can fetch from different sources (recorder, APIs, etc.)
