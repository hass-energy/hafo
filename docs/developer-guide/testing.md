# Testing

HAFO uses pytest for testing with the `pytest-homeassistant-custom-component` plugin.

## Running Tests

Run all tests:

```bash
uv run pytest
```

Run with coverage:

```bash
uv run pytest --cov=custom_components/hafo --cov-report=html
```

Run a specific test file:

```bash
uv run pytest tests/test_forecasters.py
```

Run a specific test:

```bash
uv run pytest tests/test_forecasters.py::TestHistoricalShiftForecaster::test_shift_history
```

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures
├── test_init.py             # Integration setup/unload tests
├── test_config_flow.py      # Config flow tests
├── test_coordinator.py      # Coordinator tests
├── test_sensor.py           # Sensor entity tests
└── forecasters/
    └── test_historical_shift.py  # Forecaster algorithm tests
```

## Writing Tests

### Fixtures

Use the `hass` fixture from `pytest-homeassistant-custom-component`:

```python
async def test_something(hass: HomeAssistant) -> None:
    """Test description."""
    # Test code here
```

### Mocking the Recorder

Mock the recorder statistics for testing:

```python
from unittest.mock import patch

async def test_forecast(hass: HomeAssistant) -> None:
    mock_stats = [
        {"start": datetime(2024, 1, 1, 10, 0, 0, tzinfo=UTC), "mean": 2.0},
    ]

    with patch(
        "custom_components.hafo.forecasters.historical_shift.get_statistics_for_sensor",
        return_value=mock_stats,
    ):
        # Test code
```

### Test Categories

1. **Unit Tests**: Test individual functions and classes
2. **Integration Tests**: Test component setup and teardown
3. **Config Flow Tests**: Test the configuration UI

## Coverage

Coverage is enforced on changed lines via Codecov.
Aim for comprehensive test coverage of new code.
