# Troubleshooting

Common issues and solutions for HAFO.

## No Forecast Data

**Symptom**: The forecast sensor shows "unknown" or has no forecast attribute.

**Possible causes**:

1. **Recorder not ready**: The recorder integration hasn't finished initializing.

    - **Solution**: Wait a few minutes after Home Assistant starts.

2. **No historical data**: The source entity doesn't have enough history.

    - **Solution**: Wait for the recorder to collect at least `history_days` of data.

3. **Entity not recorded**: The source entity is excluded from the recorder.

    - **Solution**: Check your recorder configuration and ensure the entity is included.

## Forecast Values Seem Wrong

**Symptom**: The forecast values don't match expectations.

**Possible causes**:

1. **Wrong history period**: The history period captured unusual events.

    - **Solution**: Increase `history_days` to smooth out anomalies.

2. **Recent changes**: Your usage patterns have changed recently.

    - **Solution**: Wait for new patterns to be captured in history.

3. **Missing data**: Gaps in the historical data.

    - **Solution**: Check that the source entity was available during the history period.

## Sensor Not Updating

**Symptom**: The `last_forecast_update` attribute is stale.

**Possible causes**:

1. **Coordinator error**: An error occurred during the last update.

    - **Solution**: Check the Home Assistant logs for errors.

2. **System overload**: Home Assistant is under heavy load.

    - **Solution**: Check system resources and reduce load if needed.

## Debug Logging

To enable debug logging for HAFO, add this to your `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.hafo: debug
```

Then restart Home Assistant and check the logs for detailed information.

## Getting Help

If you're still having issues:

1. Check the [GitHub Issues](https://github.com/hass-energy/hafo/issues) for similar problems
2. Open a new issue with:
    - Your Home Assistant version
    - HAFO version
    - Debug logs
    - Steps to reproduce
