"""Tests for the HAFO config flow."""

from unittest.mock import patch

from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
import pytest

from custom_components.hafo.config_flow import HafoConfigFlow
from custom_components.hafo.const import (
    CONF_FORECAST_TYPE,
    CONF_HISTORY_DAYS,
    CONF_SOURCE_ENTITY,
    DEFAULT_FORECAST_TYPE,
    DEFAULT_HISTORY_DAYS,
)


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
    assert result.get("title") == "Test Power Forecast"
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
