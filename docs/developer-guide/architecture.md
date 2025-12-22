# Architecture

HAFO follows a simple, focused architecture designed for extensibility.

## Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Home Assistant                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌──────────────┐    ┌───────────────┐  │
│  │ Config Flow │───▶│ Coordinator  │───▶│ Forecast      │  │
│  │             │    │              │    │ Sensor        │  │
│  └─────────────┘    └──────┬───────┘    └───────────────┘  │
│                            │                                │
│                     ┌──────▼───────┐                        │
│                     │ Forecaster   │                        │
│                     │ (Historical  │                        │
│                     │  Shift)      │                        │
│                     └──────┬───────┘                        │
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

### Coordinator (`coordinator.py`)

Manages data updates using Home Assistant's `DataUpdateCoordinator`.
Refreshes the forecast hourly and notifies sensors of updates.

### Forecasters (`forecasters/`)

Contains the forecasting algorithms.
Each forecaster implements a common interface for generating forecasts.

Currently implemented:

- **HistoricalShiftForecaster**: Shifts history forward by N days

### Sensor (`sensor.py`)

Exposes the forecast data to Home Assistant.
Provides the forecast as both state (current value) and attributes (full series).

## Data Flow

1. **Configuration**: User creates a forecast helper via the config flow
2. **Initialization**: Coordinator is created and starts hourly updates
3. **Fetching**: Forecaster fetches statistics from the recorder
4. **Transformation**: Historical data is shifted forward and cycled
5. **Exposure**: Sensor exposes the forecast data

## Adding New Forecasters

To add a new forecasting algorithm:

1. Create a new module in `forecasters/`
2. Implement the forecaster class with `available()` and `generate_forecast()` methods
3. Register it in the config flow dropdown
4. Add documentation

## Extension Points

- **New Forecasters**: Add algorithms in `forecasters/`
- **New Sensors**: Add sensor types in `sensor.py`
- **Data Sources**: Could extend beyond recorder statistics
