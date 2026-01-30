"""Tests for the HAFO config flow."""

from unittest.mock import patch

from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.hafo.config_flow import HafoConfigFlow, HafoOptionsFlow
from custom_components.hafo.const import (
    CONF_FORECAST_TYPE,
    CONF_HISTORY_DAYS,
    CONF_SOURCE_ENTITY,
    DEFAULT_FORECAST_TYPE,
    DEFAULT_HISTORY_DAYS,
    DOMAIN,
    FORECAST_TYPE_HISTORICAL_SHIFT,
)
from custom_components.hafo.coordinator import create_forecaster


@pytest.fixture
def config_flow(hass: HomeAssistant) -> HafoConfigFlow:
    """Create a config flow for testing."""
    flow = HafoConfigFlow()
    flow.hass = hass
    # Initialize the context dict that HA expects
    flow.context = {"source": "user"}
    return flow


async def test_user_flow_shows_form(hass: HomeAssistant, config_flow: HafoConfigFlow) -> None:
    """Test that the user flow shows the form initially."""
    result = await config_flow.async_step_user(user_input=None)

    assert result.get("type") == FlowResultType.FORM
    assert result.get("step_id") == "user"


async def test_user_flow_creates_entry(hass: HomeAssistant, config_flow: HafoConfigFlow) -> None:
    """Test that the user flow creates a config entry."""
    # Set up a test entity
    hass.states.async_set("sensor.test_power", "100.0", {"friendly_name": "Test Power"})

    # Mock async_set_unique_id since it requires more context
    with (
        patch.object(config_flow, "async_set_unique_id", return_value=None),
        patch.object(config_flow, "_abort_if_unique_id_configured", return_value=None),
    ):
        result = await config_flow.async_step_user(
            user_input={
                CONF_SOURCE_ENTITY: "sensor.test_power",
                CONF_HISTORY_DAYS: 7,
                CONF_FORECAST_TYPE: DEFAULT_FORECAST_TYPE,
            },
        )

    assert result.get("type") == FlowResultType.CREATE_ENTRY
    assert result.get("title") == "Test Power"
    data = dict(result.get("data", {}))
    assert data[CONF_SOURCE_ENTITY] == "sensor.test_power"
    assert data[CONF_HISTORY_DAYS] == 7


async def test_user_flow_entity_not_found(hass: HomeAssistant, config_flow: HafoConfigFlow) -> None:
    """Test that the user flow shows error for missing entity."""
    # Submit with a non-existent entity
    result = await config_flow.async_step_user(
        user_input={
            CONF_SOURCE_ENTITY: "sensor.nonexistent",
            CONF_HISTORY_DAYS: DEFAULT_HISTORY_DAYS,
            CONF_FORECAST_TYPE: DEFAULT_FORECAST_TYPE,
        },
    )

    assert result.get("type") == FlowResultType.FORM
    assert result.get("errors") == {CONF_SOURCE_ENTITY: "entity_not_found"}


def test_async_get_options_flow_returns_options_flow() -> None:
    """async_get_options_flow returns HafoOptionsFlow instance."""
    entry = MockConfigEntry(domain=DOMAIN, entry_id="test_id")
    flow = HafoConfigFlow.async_get_options_flow(entry)
    assert isinstance(flow, HafoOptionsFlow)


async def test_options_flow_show_form(hass: HomeAssistant) -> None:
    """Options flow shows form with current values."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test Forecast",
        data={
            CONF_SOURCE_ENTITY: "sensor.test_power",
            CONF_HISTORY_DAYS: 7,
            CONF_FORECAST_TYPE: FORECAST_TYPE_HISTORICAL_SHIFT,
        },
        entry_id="options_test_id",
    )
    entry.add_to_hass(hass)

    flow = HafoOptionsFlow()
    flow.hass = hass
    flow.handler = entry.entry_id

    result = await flow.async_step_init(user_input=None)

    assert result.get("type") == FlowResultType.FORM
    assert result.get("step_id") == "init"
    assert "data_schema" in result


async def test_options_flow_submit_updates_options(hass: HomeAssistant) -> None:
    """Options flow submit creates entry with new options."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test Forecast",
        data={
            CONF_SOURCE_ENTITY: "sensor.test_power",
            CONF_HISTORY_DAYS: 7,
            CONF_FORECAST_TYPE: FORECAST_TYPE_HISTORICAL_SHIFT,
        },
        entry_id="options_test_id",
    )
    entry.add_to_hass(hass)

    flow = HafoOptionsFlow()
    flow.hass = hass
    flow.handler = entry.entry_id

    result = await flow.async_step_init(user_input={CONF_HISTORY_DAYS: 14})

    assert result.get("type") == FlowResultType.CREATE_ENTRY
    assert result.get("data") == {CONF_HISTORY_DAYS: 14}


async def test_options_flow_aborts_when_entry_not_found(hass: HomeAssistant) -> None:
    """Options flow aborts when config entry is missing."""
    flow = HafoOptionsFlow()
    flow.hass = hass
    flow.handler = "nonexistent_entry_id"

    result = await flow.async_step_init(user_input=None)

    assert result.get("type") == FlowResultType.ABORT
    assert result.get("reason") == "entry_not_found"


async def test_forecaster_uses_updated_options(hass: HomeAssistant) -> None:
    """Test that forecaster uses history_days from options after update.

    When a user edits the integration options, the new values are stored
    in entry.options. The forecaster should read from options first,
    falling back to data for initial values.
    """
    # Set up a test entity
    hass.states.async_set("sensor.test_power", "100.0", {"unit_of_measurement": "W"})

    # Create entry with initial history_days=7 in data
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test Forecast",
        data={
            CONF_SOURCE_ENTITY: "sensor.test_power",
            CONF_HISTORY_DAYS: 7,
            CONF_FORECAST_TYPE: FORECAST_TYPE_HISTORICAL_SHIFT,
        },
        entry_id="test_entry_id",
    )
    entry.add_to_hass(hass)

    # Simulate options update: user changed history_days to 14
    hass.config_entries.async_update_entry(entry, options={CONF_HISTORY_DAYS: 14})

    # Create forecaster (as would happen during reload after options update)
    forecaster = create_forecaster(hass, entry)

    # Forecaster should use the updated value from options, not the original from data
    assert forecaster.history_days == 14, (
        f"Expected history_days=14 from options, got {forecaster.history_days}. "
        "Forecaster is not reading from entry.options."
    )
