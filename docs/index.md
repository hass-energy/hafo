# HAFO Documentation

Welcome to the HAFO (Home Assistant Forecaster) documentation!

HAFO is a Home Assistant integration that creates forecast helper sensors from entity history.
It transforms historical data from the recorder into future predictions, making it easy to forecast values for sensors that don't have native forecast support.

## Quick Start

1. [Install HAFO](user-guide/installation.md)
2. [Create a forecast helper](user-guide/configuration.md)
3. [Understand the forecast data](user-guide/forecasters/historical-shift.md)

## Key Features

- **Historical Shift Forecasting**: Projects past patterns into the future
- **Automatic Cycling**: Repeats patterns to fill any forecast horizon
- **Helper-based Design**: Easy to add and configure via the UI
- **Standard Format**: Provides forecast data in Home Assistant's standard format

## Use Cases

- **Load Forecasting**: Predict home power consumption from historical patterns
- **Integration with HAEO**: Provide load forecasts for energy optimization
- **Temperature Patterns**: Forecast indoor temperatures based on past data
- **Usage Prediction**: Estimate resource usage from history

## Navigation

- **[User Guide](user-guide/index.md)**: Installation, configuration, and usage
- **[Developer Guide](developer-guide/index.md)**: Contributing and architecture
