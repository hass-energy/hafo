---
applyTo: tests/**
description: Testing standards
globs: [tests/**]
alwaysApply: false
---

# Testing standards

## Coverage requirements

Coverage is enforced by codecov which ensures coverage does not decrease from main on changed lines.
Focus on testing behavior and edge cases, not achieving arbitrary coverage percentages.

## Test style

Use function-style pytest tests, not class-based test organization:

```python
# ✅ Good - function style
def test_forecaster_generates_points() -> None:
    forecaster = create_forecaster(history_days=7)
    result = forecaster.generate()
    assert len(result.forecast) > 0


# ❌ Bad - class style
class TestForecaster:
    def test_generates_points(self) -> None: ...
```

## Parametrized data-driven tests

Use parametrized tests with test data modules rather than many similar test functions:

```python
@pytest.mark.parametrize("case", FORECAST_TEST_CASES, ids=lambda c: c["description"])
def test_forecast_generation(case: ForecastTestCase) -> None:
    forecaster = case["factory"](case["data"])
    result = forecaster.generate()
    assert result == case["expected"]
```

## Property access in tests

Access properties directly without None checks when you have created the entities:

```python
# ✅ Good - direct access
sensor = hass.states.get("sensor.test_forecast")
assert sensor.state == "2.5"

# ❌ Bad - unnecessary None checks
sensor = hass.states.get("sensor.test_forecast")
if sensor is not None:
    assert sensor.state == "2.5"
```

None checks reduce readability and make tests fragile to passing unexpectedly.

## Fixture patterns

```python
@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return mocked config entry."""
    return MockConfigEntry(
        title="Test Forecast",
        domain=DOMAIN,
        data={...},
        unique_id="test_unique_id",
    )


@pytest.fixture
async def init_integration(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> MockConfigEntry:
    """Set up integration for testing."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    return mock_config_entry
```

## Config flow testing

Test both success paths and error handling:

```python
async def test_user_flow_success(hass):
    """Test successful user flow."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    assert result["type"] == FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(result["flow_id"], user_input={...})
    assert result["type"] == FlowResultType.CREATE_ENTRY


async def test_flow_entity_not_found(hass):
    """Test entity not found error handling."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], user_input={...})
    assert result["errors"] == {"source_entity": "entity_not_found"}
```
