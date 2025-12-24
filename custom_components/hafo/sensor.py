"""Sensor platform for Home Assistant Forecaster."""

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import ATTR_FORECAST, ATTR_HISTORY_DAYS, ATTR_LAST_UPDATED, ATTR_SOURCE_ENTITY, DOMAIN
from .coordinator import ForecasterCoordinator
from .forecasters.historical_shift import ForecastResult

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up HAFO sensors based on a config entry."""
    coordinator: ForecasterCoordinator = entry.runtime_data

    entities: list[SensorEntity] = [
        HafoForecastSensor(coordinator),
    ]

    async_add_entities(entities)


class HafoForecastSensor(CoordinatorEntity[ForecasterCoordinator], SensorEntity):
    """Sensor that provides forecast data from historical statistics."""

    _attr_has_entity_name = True
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: ForecasterCoordinator) -> None:
        """Initialize the forecast sensor.

        Args:
            coordinator: The data update coordinator

        """
        super().__init__(coordinator)

        # Set up entity attributes
        self._attr_unique_id = f"{coordinator.entry.entry_id}_forecast"
        self._attr_name = "Forecast"

        # Copy unit of measurement from source entity if available
        self._source_entity = coordinator.source_entity
        self._update_from_source_entity()

    def _update_from_source_entity(self) -> None:
        """Update sensor attributes from the source entity."""
        source_state = self.coordinator.hass.states.get(self._source_entity)
        if source_state:
            # Copy unit of measurement and device class if available
            if unit := source_state.attributes.get("unit_of_measurement"):
                self._attr_native_unit_of_measurement = unit
            if device_class := source_state.attributes.get("device_class"):
                self._attr_device_class = device_class

    @property
    def native_value(self) -> float | None:  # type: ignore[override]
        """Return the current forecast value (first point in forecast)."""
        result = self.coordinator.data
        if result is None or not result.forecast:
            return None

        # Find the forecast point closest to now
        now = dt_util.now()
        closest_point = None
        min_diff = None

        for point in result.forecast:
            diff = abs((point.time - now).total_seconds())
            if min_diff is None or diff < min_diff:
                min_diff = diff
                closest_point = point

        return closest_point.value if closest_point else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:  # type: ignore[override]
        """Return additional state attributes including the full forecast."""
        result = self.coordinator.data

        attrs: dict[str, Any] = {
            ATTR_SOURCE_ENTITY: self._source_entity,
            ATTR_HISTORY_DAYS: self.coordinator.history_days,
        }

        if result is not None:
            attrs[ATTR_LAST_UPDATED] = result.generated_at.isoformat()
            attrs[ATTR_FORECAST] = self._format_forecast(result)

        return attrs

    def _format_forecast(self, result: ForecastResult) -> list[dict[str, Any]]:
        """Format the forecast for the state attribute.

        Returns forecast in HAEO-compatible format:
        [{"time": "ISO8601", "value": float}, ...]
        """
        return [
            {
                "time": point.time.isoformat(),
                "value": point.value,
            }
            for point in result.forecast
        ]

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        # Update attributes from source entity in case they changed
        self._update_from_source_entity()
        super()._handle_coordinator_update()

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.entry.entry_id)},
            name=self.coordinator.entry.title,
            manufacturer="HAFO",
            model="Historical Shift Forecaster",
        )
