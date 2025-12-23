# HAFO Scenario Tests

This directory contains scenario tests for the HAFO forecaster.

## How It Works

Scenario tests inject fake statistics into the Home Assistant recorder and verify
that the forecaster produces correct output. This allows testing the full
integration pipeline without requiring a real Home Assistant database.

## Structure

Each scenario folder contains:

- `config.json` - Scenario configuration (entity_id, history_days, freeze_time, expected output)

## Running Scenario Tests

```bash
uv run pytest tests/scenarios/ -v
```

## Adding New Scenarios

1. Create a new folder `scenario{N}/`
2. Add a `config.json` with the test configuration
3. Run the tests to verify

## Key Functions

- `add_fake_statistics()` - Injects fake statistics into the recorder
- `generate_hourly_statistics()` - Creates realistic hourly consumption patterns
