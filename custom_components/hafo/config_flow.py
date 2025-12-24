"""Config flow for Home Assistant Forecaster integration."""

from typing import Any, cast

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers import selector
import voluptuous as vol

from .const import (
    CONF_FORECAST_HOURS,
    CONF_FORECAST_TYPE,
    CONF_HISTORY_DAYS,
    CONF_INPUT_ENTITIES,
    CONF_OUTPUT_ENTITY,
    CONF_RIVER_MODEL_TYPE,
    CONF_SOURCE_ENTITY,
    DEFAULT_FORECAST_HOURS,
    DEFAULT_FORECAST_TYPE,
    DEFAULT_HISTORY_DAYS,
    DEFAULT_RIVER_MODEL_TYPE,
    DOMAIN,
    FORECAST_TYPE_HISTORICAL_SHIFT,
    FORECAST_TYPE_RIVER_ML,
    RIVER_MODEL_LINEAR,
    RIVER_MODEL_SNARIMAX,
)


class HafoConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Home Assistant Forecaster."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._data: dict[str, Any] = {}

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> "HafoOptionsFlow":  # noqa: ARG004
        """Get the options flow for this handler."""
        return HafoOptionsFlow()

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle the initial step - select forecast type."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._data.update(user_input)
            forecast_type = user_input.get(CONF_FORECAST_TYPE, DEFAULT_FORECAST_TYPE)

            if forecast_type == FORECAST_TYPE_RIVER_ML:
                return await self.async_step_river_ml()
            return await self.async_step_historical_shift()

        # Build the schema for forecast type selection
        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_FORECAST_TYPE,
                    default=DEFAULT_FORECAST_TYPE,
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            selector.SelectOptionDict(
                                value=FORECAST_TYPE_HISTORICAL_SHIFT,
                                label="Historical Shift",
                            ),
                            selector.SelectOptionDict(
                                value=FORECAST_TYPE_RIVER_ML,
                                label="RiverML",
                            ),
                        ],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_historical_shift(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle Historical Shift configuration."""
        errors: dict[str, str] = {}

        if user_input is not None:
            source_entity = user_input[CONF_SOURCE_ENTITY]
            if self.hass.states.get(source_entity) is None:
                errors[CONF_SOURCE_ENTITY] = "entity_not_found"
            else:
                self._data.update(user_input)

                await self.async_set_unique_id(f"{DOMAIN}_{source_entity}")
                self._abort_if_unique_id_configured()

                state = self.hass.states.get(source_entity)
                friendly_name = state.attributes.get("friendly_name", source_entity) if state else source_entity
                title = f"{friendly_name} Forecast"

                return self.async_create_entry(
                    title=title,
                    data=self._data,
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_SOURCE_ENTITY): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=["sensor", "input_number"])
                ),
                vol.Optional(
                    CONF_HISTORY_DAYS,
                    default=DEFAULT_HISTORY_DAYS,
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=1,
                        max=30,
                        step=1,
                        mode=selector.NumberSelectorMode.BOX,
                        unit_of_measurement="days",
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="historical_shift",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_river_ml(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle RiverML configuration."""
        errors: dict[str, str] = {}

        if user_input is not None:
            input_entities = user_input.get(CONF_INPUT_ENTITIES, [])
            output_entity = user_input.get(CONF_OUTPUT_ENTITY)

            # Validate at least one input entity
            if not input_entities:
                errors[CONF_INPUT_ENTITIES] = "no_input_entities"
            # Validate output entity exists
            elif output_entity and self.hass.states.get(output_entity) is None:
                errors[CONF_OUTPUT_ENTITY] = "entity_not_found"
            # Validate output is not in inputs
            elif output_entity in input_entities:
                errors[CONF_OUTPUT_ENTITY] = "output_in_inputs"
            # Validate all input entities exist
            else:
                for entity_id in input_entities:
                    if self.hass.states.get(entity_id) is None:
                        errors[CONF_INPUT_ENTITIES] = "entity_not_found"
                        break

            if not errors:
                # output_entity is validated above
                output_entity = cast("str", output_entity)
                self._data.update(user_input)

                await self.async_set_unique_id(f"{DOMAIN}_{output_entity}")
                self._abort_if_unique_id_configured()

                state = self.hass.states.get(output_entity)
                friendly_name = state.attributes.get("friendly_name", output_entity) if state else output_entity
                title = f"{friendly_name} RiverML Forecast"

                return self.async_create_entry(
                    title=title,
                    data=self._data,
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_INPUT_ENTITIES): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain=["sensor", "input_number"],
                        multiple=True,
                    )
                ),
                vol.Required(CONF_OUTPUT_ENTITY): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=["sensor", "input_number"])
                ),
                vol.Optional(
                    CONF_HISTORY_DAYS,
                    default=DEFAULT_HISTORY_DAYS,
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=1,
                        max=30,
                        step=1,
                        mode=selector.NumberSelectorMode.BOX,
                        unit_of_measurement="days",
                    )
                ),
                vol.Optional(
                    CONF_FORECAST_HOURS,
                    default=DEFAULT_FORECAST_HOURS,
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=1,
                        max=720,  # 30 days
                        step=1,
                        mode=selector.NumberSelectorMode.BOX,
                        unit_of_measurement="hours",
                    )
                ),
                vol.Optional(
                    CONF_RIVER_MODEL_TYPE,
                    default=DEFAULT_RIVER_MODEL_TYPE,
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            selector.SelectOptionDict(
                                value=RIVER_MODEL_SNARIMAX,
                                label="SNARIMAX",
                            ),
                            selector.SelectOptionDict(
                                value=RIVER_MODEL_LINEAR,
                                label="Linear Regression",
                            ),
                        ],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="river_ml",
            data_schema=schema,
            errors=errors,
        )


class HafoOptionsFlow(OptionsFlow):
    """Handle options flow for Home Assistant Forecaster."""

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle options flow."""
        entry = self.hass.config_entries.async_get_entry(self.handler)  # type: ignore[arg-type]
        if entry is None:
            return self.async_abort(reason="entry_not_found")

        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_data = entry.data
        forecast_type = current_data.get(CONF_FORECAST_TYPE, DEFAULT_FORECAST_TYPE)

        # Build schema based on forecast type
        if forecast_type == FORECAST_TYPE_RIVER_ML:
            schema = vol.Schema(
                {
                    vol.Optional(
                        CONF_HISTORY_DAYS,
                        default=current_data.get(CONF_HISTORY_DAYS, DEFAULT_HISTORY_DAYS),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=1,
                            max=30,
                            step=1,
                            mode=selector.NumberSelectorMode.BOX,
                            unit_of_measurement="days",
                        )
                    ),
                    vol.Optional(
                        CONF_FORECAST_HOURS,
                        default=current_data.get(CONF_FORECAST_HOURS, DEFAULT_FORECAST_HOURS),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=1,
                            max=720,
                            step=1,
                            mode=selector.NumberSelectorMode.BOX,
                            unit_of_measurement="hours",
                        )
                    ),
                    vol.Optional(
                        CONF_RIVER_MODEL_TYPE,
                        default=current_data.get(CONF_RIVER_MODEL_TYPE, DEFAULT_RIVER_MODEL_TYPE),
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                selector.SelectOptionDict(
                                    value=RIVER_MODEL_SNARIMAX,
                                    label="SNARIMAX",
                                ),
                                selector.SelectOptionDict(
                                    value=RIVER_MODEL_LINEAR,
                                    label="Linear Regression",
                                ),
                            ],
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    ),
                }
            )
        else:
            schema = vol.Schema(
                {
                    vol.Optional(
                        CONF_HISTORY_DAYS,
                        default=current_data.get(CONF_HISTORY_DAYS, DEFAULT_HISTORY_DAYS),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=1,
                            max=30,
                            step=1,
                            mode=selector.NumberSelectorMode.BOX,
                            unit_of_measurement="days",
                        )
                    ),
                }
            )

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
        )
