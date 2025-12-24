"""Tests for the HAFO config flow."""

from unittest.mock import patch

from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
import pytest

from custom_components.hafo.config_flow import HafoConfigFlow
from custom_components.hafo.const import (
    CONF_FORECAST_HOURS,
    CONF_FORECAST_TYPE,
    CONF_HISTORY_DAYS,
    CONF_INPUT_ENTITIES,
    CONF_OUTPUT_ENTITY,
    CONF_RIVER_MODEL_TYPE,
    CONF_SOURCE_ENTITY,
    DEFAULT_FORECAST_HOURS,
    DEFAULT_HISTORY_DAYS,
    DEFAULT_RIVER_MODEL_TYPE,
    FORECAST_TYPE_HISTORICAL_SHIFT,
    FORECAST_TYPE_RIVER_ML,
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


async def test_user_flow_proceeds_to_historical_shift(hass: HomeAssistant, config_flow: HafoConfigFlow) -> None:
    """Test that selecting historical shift proceeds to that step."""
    result = await config_flow.async_step_user(
        user_input={CONF_FORECAST_TYPE: FORECAST_TYPE_HISTORICAL_SHIFT},
    )

    assert result.get("type") == FlowResultType.FORM
    assert result.get("step_id") == "historical_shift"


async def test_user_flow_proceeds_to_river_ml(hass: HomeAssistant, config_flow: HafoConfigFlow) -> None:
    """Test that selecting RiverML proceeds to that step."""
    result = await config_flow.async_step_user(
        user_input={CONF_FORECAST_TYPE: FORECAST_TYPE_RIVER_ML},
    )

    assert result.get("type") == FlowResultType.FORM
    assert result.get("step_id") == "river_ml"


async def test_historical_shift_creates_entry(hass: HomeAssistant, config_flow: HafoConfigFlow) -> None:
    """Test that the historical shift step creates a config entry."""
    hass.states.async_set("sensor.test_power", "100.0", {"friendly_name": "Test Power"})

    with (
        patch.object(config_flow, "async_set_unique_id", return_value=None),
        patch.object(config_flow, "_abort_if_unique_id_configured", return_value=None),
    ):
        # First, select forecast type
        config_flow._data = {CONF_FORECAST_TYPE: FORECAST_TYPE_HISTORICAL_SHIFT}

        result = await config_flow.async_step_historical_shift(
            user_input={
                CONF_SOURCE_ENTITY: "sensor.test_power",
                CONF_HISTORY_DAYS: 7,
            },
        )

    assert result.get("type") == FlowResultType.CREATE_ENTRY
    assert result.get("title") == "Test Power Forecast"
    data = dict(result.get("data", {}))
    assert data[CONF_SOURCE_ENTITY] == "sensor.test_power"
    assert data[CONF_HISTORY_DAYS] == 7
    assert data[CONF_FORECAST_TYPE] == FORECAST_TYPE_HISTORICAL_SHIFT


async def test_historical_shift_entity_not_found(hass: HomeAssistant, config_flow: HafoConfigFlow) -> None:
    """Test that the historical shift step shows error for missing entity."""
    result = await config_flow.async_step_historical_shift(
        user_input={
            CONF_SOURCE_ENTITY: "sensor.nonexistent",
            CONF_HISTORY_DAYS: DEFAULT_HISTORY_DAYS,
        },
    )

    assert result.get("type") == FlowResultType.FORM
    assert result.get("errors") == {CONF_SOURCE_ENTITY: "entity_not_found"}


async def test_river_ml_creates_entry(hass: HomeAssistant, config_flow: HafoConfigFlow) -> None:
    """Test that the RiverML step creates a config entry."""
    hass.states.async_set("sensor.input1", "10.0", {"friendly_name": "Input 1"})
    hass.states.async_set("sensor.input2", "20.0", {"friendly_name": "Input 2"})
    hass.states.async_set("sensor.output", "100.0", {"friendly_name": "Output"})

    with (
        patch.object(config_flow, "async_set_unique_id", return_value=None),
        patch.object(config_flow, "_abort_if_unique_id_configured", return_value=None),
    ):
        config_flow._data = {CONF_FORECAST_TYPE: FORECAST_TYPE_RIVER_ML}

        result = await config_flow.async_step_river_ml(
            user_input={
                CONF_INPUT_ENTITIES: ["sensor.input1", "sensor.input2"],
                CONF_OUTPUT_ENTITY: "sensor.output",
                CONF_HISTORY_DAYS: 7,
                CONF_FORECAST_HOURS: 48,
                CONF_RIVER_MODEL_TYPE: DEFAULT_RIVER_MODEL_TYPE,
            },
        )

    assert result.get("type") == FlowResultType.CREATE_ENTRY
    assert result.get("title") == "Output RiverML Forecast"
    data = dict(result.get("data", {}))
    assert data[CONF_INPUT_ENTITIES] == ["sensor.input1", "sensor.input2"]
    assert data[CONF_OUTPUT_ENTITY] == "sensor.output"
    assert data[CONF_FORECAST_TYPE] == FORECAST_TYPE_RIVER_ML


async def test_river_ml_no_input_entities(hass: HomeAssistant, config_flow: HafoConfigFlow) -> None:
    """Test that the RiverML step shows error when no input entities provided."""
    hass.states.async_set("sensor.output", "100.0")

    result = await config_flow.async_step_river_ml(
        user_input={
            CONF_INPUT_ENTITIES: [],
            CONF_OUTPUT_ENTITY: "sensor.output",
            CONF_HISTORY_DAYS: DEFAULT_HISTORY_DAYS,
            CONF_FORECAST_HOURS: DEFAULT_FORECAST_HOURS,
            CONF_RIVER_MODEL_TYPE: DEFAULT_RIVER_MODEL_TYPE,
        },
    )

    assert result.get("type") == FlowResultType.FORM
    assert result.get("errors") == {CONF_INPUT_ENTITIES: "no_input_entities"}


async def test_river_ml_output_in_inputs(hass: HomeAssistant, config_flow: HafoConfigFlow) -> None:
    """Test that the RiverML step shows error when output is in inputs."""
    hass.states.async_set("sensor.input1", "10.0")
    hass.states.async_set("sensor.output", "100.0")

    result = await config_flow.async_step_river_ml(
        user_input={
            CONF_INPUT_ENTITIES: ["sensor.input1", "sensor.output"],  # Output is in inputs
            CONF_OUTPUT_ENTITY: "sensor.output",
            CONF_HISTORY_DAYS: DEFAULT_HISTORY_DAYS,
            CONF_FORECAST_HOURS: DEFAULT_FORECAST_HOURS,
            CONF_RIVER_MODEL_TYPE: DEFAULT_RIVER_MODEL_TYPE,
        },
    )

    assert result.get("type") == FlowResultType.FORM
    assert result.get("errors") == {CONF_OUTPUT_ENTITY: "output_in_inputs"}


async def test_river_ml_output_entity_not_found(hass: HomeAssistant, config_flow: HafoConfigFlow) -> None:
    """Test that the RiverML step shows error when output entity missing."""
    hass.states.async_set("sensor.input1", "10.0")

    result = await config_flow.async_step_river_ml(
        user_input={
            CONF_INPUT_ENTITIES: ["sensor.input1"],
            CONF_OUTPUT_ENTITY: "sensor.nonexistent",
            CONF_HISTORY_DAYS: DEFAULT_HISTORY_DAYS,
            CONF_FORECAST_HOURS: DEFAULT_FORECAST_HOURS,
            CONF_RIVER_MODEL_TYPE: DEFAULT_RIVER_MODEL_TYPE,
        },
    )

    assert result.get("type") == FlowResultType.FORM
    assert result.get("errors") == {CONF_OUTPUT_ENTITY: "entity_not_found"}
