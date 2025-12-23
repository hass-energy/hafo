# Forecasters

HAFO provides forecasting algorithms that transform historical entity data into future predictions.

## Available Forecasters

### [Historical Shift](historical-shift.md)

The primary forecasting algorithm that shifts historical data forward in time.

- Fetches hourly statistics from the recorder
- Shifts timestamps forward by N days
- Cycles the pattern to fill the forecast horizon

## Choosing a Forecaster

Currently, HAFO offers one forecasting algorithm.
Future versions may include additional algorithms such as:

- Weighted moving averages
- Seasonal decomposition
- Machine learning models

## How Forecasts Work

All forecasters in HAFO follow a similar pattern:

1. **Data Collection**: Fetch historical data from the recorder
2. **Transformation**: Apply the forecasting algorithm
3. **Horizon Filling**: Extend the forecast to cover the desired time range
4. **Output**: Provide forecast as sensor attributes

The forecast is refreshed hourly to incorporate new data.
