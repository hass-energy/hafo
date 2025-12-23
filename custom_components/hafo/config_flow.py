"""Config flow for Home Assistant Forecaster integration."""

from typing import Any

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers import selector
import voluptuous as vol

from .const import (
    CONF_FORECAST_TYPE,
    CONF_HISTORY_DAYS,
    CONF_SOURCE_ENTITY,
    DEFAULT_FORECAST_TYPE,
    DEFAULT_HISTORY_DAYS,
    DOMAIN,
    FORECAST_TYPE_HISTORICAL_SHIFT,
)


class HafoConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Home Assistant Forecaster."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> "HafoOptionsFlow":  # noqa: ARG004
        """Get the options flow for this handler."""
        return HafoOptionsFlow()

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate the source entity exists
            source_entity = user_input[CONF_SOURCE_ENTITY]
            if self.hass.states.get(source_entity) is None:
                errors[CONF_SOURCE_ENTITY] = "entity_not_found"
            else:
                # Create unique ID from source entity
                await self.async_set_unique_id(f"{DOMAIN}_{source_entity}")
                self._abort_if_unique_id_configured()

                # Create a friendly title from the source entity
                state = self.hass.states.get(source_entity)
                friendly_name = state.attributes.get("friendly_name", source_entity) if state else source_entity
                title = f"{friendly_name} Forecast"

                return self.async_create_entry(
                    title=title,
                    data=user_input,
                )

        # Build the schema for user input
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


class HafoOptionsFlow(OptionsFlow):
    """Handle options flow for Home Assistant Forecaster."""

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle options flow."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Get current config
        entry = self.hass.config_entries.async_get_entry(self.handler)  # type: ignore[arg-type]
        if entry is None:
            return self.async_abort(reason="entry_not_found")

        current_data = entry.data

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
