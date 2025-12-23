# Installation

HAFO can be installed via HACS (recommended) or manually.

## HACS Installation (Recommended)

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

## Manual Installation

1. Download the latest release from the [releases page](https://github.com/hass-energy/hafo/releases)

2. Extract the `hafo` folder to your `custom_components` directory

3. Your directory structure should look like:

    ```
    config/
    └── custom_components/
        └── hafo/
            ├── __init__.py
            ├── manifest.json
            └── ...
    ```

4. Restart Home Assistant

## Prerequisites

HAFO requires:

- Home Assistant 2025.12.2 or newer
- The Recorder integration (enabled by default)
- Historical statistics for the entities you want to forecast

!!! tip "Check Recorder Settings"

    HAFO uses the Home Assistant recorder's hourly statistics.
    Make sure your source entities are being recorded and have at least a few days of history.
