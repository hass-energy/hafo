<p align="center">
    <img src="docs/assets/logo.svg" alt="HAFO Logo" width="512">
</p>

# HAFO - Home Assistant Forecaster

[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg)](https://github.com/hacs/integration) [![GitHub Release](https://img.shields.io/github/release/hass-energy/hafo.svg)](https://github.com/hass-energy/hafo/releases) [![License](https://img.shields.io/github/license/hass-energy/hafo.svg)](LICENSE) [![Documentation](https://img.shields.io/badge/docs-latest-blue.svg)](https://hass-energy.github.io/hafo/)

HAFO (Home Assistant Forecaster) is a custom integration that creates forecast helper sensors using various forecasting engines.
It transforms data from different sources into future predictions, making it easy to forecast values for sensors that don't have native forecast support.

## 🎯 Project Philosophy

HAFO follows the Unix philosophy: **do one thing and do it well**.

### What HAFO Does

- ✅ **Forecast generation** from multiple forecasting engines
- ✅ **Helper sensor creation** with forecast attributes
- ✅ **Integration** with Home Assistant's sensor ecosystem

### What HAFO Doesn't Do

HAFO focuses exclusively on forecasting and **will not** add features outside this scope:

- ❌ **Energy optimization** - Use [HAEO](https://github.com/hass-energy/haeo) for that
- ❌ **Device control** - Use Home Assistant automations
- ❌ **External API integrations** - Use dedicated integrations for external forecast services

This focused approach means:

- Better integration with the HA ecosystem
- Simpler, more maintainable codebase
- Users can choose best-in-class solutions for each component
- HAFO does forecasting exceptionally well

## 📚 Documentation

**[Read the full documentation →](https://hass-energy.github.io/hafo/)**

- **[Installation Guide](https://hass-energy.github.io/hafo/user-guide/installation/)** - Get started with HAFO
- **[Configuration Guide](https://hass-energy.github.io/hafo/user-guide/configuration/)** - Set up your forecasters
- **[Forecasters](https://hass-energy.github.io/hafo/user-guide/forecasters/)** - Available forecasting engines
- **[Developer Guide](https://hass-energy.github.io/hafo/developer-guide/)** - Contribute to HAFO

## ✨ Features

- **Multiple Forecasting Engines**: Choose the best algorithm for your data
- **Helper-based Design**: Easy to add and configure via the UI
- **HAEO Compatible**: Output format matches HAEO for seamless integration
- **Recorder Integration**: Leverage Home Assistant's built-in statistics
- **Extensible Architecture**: Add new forecasting engines easily

## 🔮 Forecasting Engines

### Historical Shift

Projects past patterns into the future by shifting historical data forward.
Best for data with repeating patterns (daily, weekly cycles).

- Fetches hourly statistics from the recorder
- Shifts data forward by configurable number of days
- Cycles patterns to fill any forecast horizon

*More forecasting engines coming soon!*

## 🎯 How It Works

HAFO creates forecast helper sensors that:

1. **Load Data**: Retrieves data from the configured source
2. **Apply Forecaster**: Runs the selected forecasting engine
3. **Generate Output**: Creates forecast points in HAEO-compatible format
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
   - **History Days**: Number of days of history to use (for historical forecasters)
   - **Forecast Type**: The forecasting engine to use

## 📊 Forecast Data Format

The sensor provides forecast data in HAEO-compatible format:

```yaml
state: 2.5  # Current/nearest forecast value
attributes:
  source_entity: sensor.home_power
  history_days: 7
  last_forecast_update: "2025-01-15T10:00:00+00:00"
  forecast:
    - time: "2025-01-15T10:00:00+00:00"
      value: 2.5
    - time: "2025-01-15T11:00:00+00:00"
      value: 3.1
    # ... more forecast points
```

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
