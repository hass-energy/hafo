# Removal

How to remove HAFO from Home Assistant.

## Removing a Single Forecast Helper

To remove a specific forecast helper:

1. Go to **Settings** → **Devices & Services**
2. Find the HAFO device you want to remove
3. Click the three dots menu
4. Select **Delete**
5. Confirm the deletion

## Removing HAFO Completely

To remove HAFO entirely:

1. Remove all forecast helpers (see above)
2. Go to **Settings** → **Devices & Services**
3. Find the HAFO integration
4. Click the three dots menu
5. Select **Delete**
6. Restart Home Assistant
7. Remove the `hafo` folder from `custom_components` (if manually installed)
8. Remove HAFO from HACS (if installed via HACS)

## Data Cleanup

HAFO does not store any persistent data outside of Home Assistant's configuration.
When you remove the integration, all configuration is automatically cleaned up.

Historical data in the recorder is not affected by removing HAFO.
