"""Sensor platform for Home Assistant Forecaster."""

from datetime import datetime
import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import ATTR_FORECAST, ATTR_HISTORY_DAYS, ATTR_LAST_UPDATED, ATTR_SOURCE_ENTITY
from .coordinator import ForecasterCoordinator
from .forecasters.historical_shift import ForecastPoint, ForecastResult

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


class HafoForecastSensor(CoordinatorEntity[ForecasterCoordinator], RestoreEntity, SensorEntity):
    """Sensor that provides forecast data from historical statistics."""

    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: ForecasterCoordinator) -> None:
        """Initialize the forecast sensor.

        Args:
            coordinator: The data update coordinator

        """
        super().__init__(coordinator)

        # Set up entity attributes
        self._attr_unique_id = f"{coordinator.entry.entry_id}_forecast"
        self._attr_name = f"{coordinator.entry.title} Forecast"
        self._attr_icon = "mdi:crystal-ball"

        # Restored state from before restart (used until fresh data is fetched)
        self._restored_result: ForecastResult | None = None

        # Copy unit of measurement from source entity if available
        self._source_entity = coordinator.source_entity
        self._update_from_source_entity()

    async def async_added_to_hass(self) -> None:
        """Restore state when entity is added to hass."""
        await super().async_added_to_hass()

        # Try to restore previous state
        if (last_state := await self.async_get_last_state()) is None:
            return

        # Restore forecast from attributes
        if (forecast_data := last_state.attributes.get(ATTR_FORECAST)) is None:
            return

        if (last_updated := last_state.attributes.get(ATTR_LAST_UPDATED)) is None:
            return

        try:
            # Parse the forecast data back into ForecastResult
            forecast_points = [
                ForecastPoint(
                    time=datetime.fromisoformat(point["time"]),
                    value=float(point["value"]),
                )
                for point in forecast_data
                if "time" in point and "value" in point
            ]

            if forecast_points:
                self._restored_result = ForecastResult(
                    forecast=forecast_points,
                    source_entity=self._source_entity,
                    history_days=self.coordinator.history_days,
                    generated_at=datetime.fromisoformat(last_updated),
                )
                _LOGGER.debug(
                    "Restored forecast for %s with %d points from before restart",
                    self._source_entity,
                    len(forecast_points),
                )
        except (KeyError, ValueError, TypeError) as err:
            _LOGGER.warning("Failed to restore forecast state: %s", err)

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
    def _effective_result(self) -> ForecastResult | None:
        """Return the best available forecast result.

        Uses coordinator data if available, otherwise falls back to restored state.
        """
        if self.coordinator.data is not None:
            # Clear restored data once we have fresh data
            self._restored_result = None
            return self.coordinator.data
        return self._restored_result

    @property
    def native_value(self) -> float | None:  # type: ignore[override]
        """Return the current forecast value (first point in forecast)."""
        result = self._effective_result
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
        result = self._effective_result

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
