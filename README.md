<p align="center">
    <img src="docs/assets/logo.svg" alt="HAFO Logo" width="512">
</p>

# HAFO - Home Assistant Forecaster

[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg)](https://github.com/hacs/integration) [![GitHub Release](https://img.shields.io/github/release/hass-energy/hafo.svg)](https://github.com/hass-energy/hafo/releases) [![License](https://img.shields.io/github/license/hass-energy/hafo.svg)](LICENSE) [![Documentation](https://img.shields.io/badge/docs-latest-blue.svg)](https://hass-energy.github.io/hafo/)

HAFO (Home Assistant Forecaster) is a custom integration that creates forecast helper sensors from entity history.
It transforms historical data from the Home Assistant recorder into future predictions, making it easy to forecast values for sensors that don't have native forecast support.

## 🎯 Project Philosophy

HAFO follows the Unix philosophy: **do one thing and do it well**.

### What HAFO Does

- ✅ **Forecast generation** from historical statistics
- ✅ **Helper sensor creation** with forecast attributes
- ✅ **Integration** with Home Assistant's recorder and statistics

### What HAFO Doesn't Do

HAFO focuses exclusively on forecasting and **will not** add features outside this scope:

- ❌ **Energy optimization** - Use [HAEO](https://github.com/hass-energy/haeo) for that
- ❌ **Device control** - Use Home Assistant automations
- ❌ **External API integrations** - Use dedicated integrations for external forecast services

## 📚 Documentation

**[Read the full documentation →](https://hass-energy.github.io/hafo/)**

- **[Installation Guide](https://hass-energy.github.io/hafo/user-guide/installation/)** - Get started with HAFO
- **[Configuration Guide](https://hass-energy.github.io/hafo/user-guide/configuration/)** - Set up your forecasters
- **[Historical Shift](https://hass-energy.github.io/hafo/user-guide/forecasters/historical-shift/)** - Understand the main forecasting algorithm
- **[Developer Guide](https://hass-energy.github.io/hafo/developer-guide/)** - Contribute to HAFO

## ✨ Features

- **Historical Shift Forecasting**: Projects past patterns into the future
- **Automatic Cycling**: Repeats patterns to fill any forecast horizon
- **Helper-based Design**: Easy to add and configure via the UI
- **Recorder Integration**: Uses Home Assistant's built-in statistics
- **Forecast Attributes**: Provides standard forecast data format

## 🎯 How It Works

HAFO creates forecast helper sensors that:

1. **Fetch History**: Retrieves hourly statistics from the Home Assistant recorder
2. **Shift Forward**: Projects historical data forward by N days
3. **Cycle Patterns**: Repeats the pattern to fill your desired forecast horizon
4. **Update Regularly**: Refreshes the forecast hourly

### Example Use Cases

- **Load Forecasting**: Predict home power consumption from historical patterns
- **Temperature Patterns**: Forecast indoor temperatures based on past data
- **Usage Prediction**: Estimate resource usage (water, gas) from history
- **Integration with HAEO**: Provide load forecasts for energy optimization

## 📦 Installation

### HACS Installation (Recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=hass-energy&repository=hafo&category=integration)

1. Open HACS in your Home Assistant instance
2. Click on "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/hass-energy/hafo`
6. Select "Integration" as the category
7. Click "Add"
8. Search for "HAFO" and click "Download"
9. Restart Home Assistant

### Manual Installation

1. Download the latest release from the [releases page](https://github.com/hass-energy/hafo/releases)
2. Extract the `hafo` folder to your `custom_components` directory
3. Restart Home Assistant

## ⚙️ Configuration

### Creating a Forecast Helper

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for **HAFO**
4. Configure your forecast helper:
   - **Source Entity**: The sensor to generate a forecast for
   - **History Days**: Number of days of history to use (default: 7)
   - **Forecast Type**: The forecasting algorithm (Historical Shift)

### Understanding History Days

The `history_days` parameter controls how the forecast is generated:

| History Days | Best For                                          |
| ------------ | ------------------------------------------------- |
| 1-3          | Highly variable data, recent patterns only        |
| 7 (default)  | Weekly patterns (weekday vs weekend differences)  |
| 14-30        | Longer-term averaging, smoothing out anomalies    |

**Example**: With `history_days: 7`, consumption from last Monday 2pm becomes the forecast for next Monday 2pm.

## 📊 Forecast Data Format

The sensor provides forecast data in the standard Home Assistant format:

```yaml
state: 2.5  # Current/nearest forecast value
attributes:
  source_entity: sensor.home_power
  history_days: 7
  last_forecast_update: "2025-01-15T10:00:00+00:00"
  forecast:
    - datetime: "2025-01-15T10:00:00+00:00"
      native_value: 2.5
    - datetime: "2025-01-15T11:00:00+00:00"
      native_value: 3.1
    # ... more forecast points
```

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
