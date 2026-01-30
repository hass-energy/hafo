"""Tests for the HAFO sensor platform."""

from collections.abc import Iterable
from datetime import UTC, datetime
from unittest.mock import patch

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.hafo.const import (
    ATTR_FORECAST,
    ATTR_LAST_UPDATED,
    ATTR_SOURCE_ENTITY,
    CONF_FORECAST_TYPE,
    CONF_HISTORY_DAYS,
    CONF_SOURCE_DEVICE_CLASS,
    CONF_SOURCE_ENTITY,
    CONF_SOURCE_UNIT,
    DOMAIN,
    FORECAST_TYPE_HISTORICAL_SHIFT,
)
from custom_components.hafo.coordinator import create_forecaster
from custom_components.hafo.forecasters.historical_shift import ForecastPoint, ForecastResult
from custom_components.hafo.sensor import HafoForecastSensor, async_setup_entry


def _create_mock_entry(
    hass: HomeAssistant,
    *,
    source_unit: str | None = None,
    source_device_class: str | None = None,
) -> MockConfigEntry:
    """Create a mock config entry with optional stored source attributes."""
    data = {
        CONF_SOURCE_ENTITY: "sensor.test_power",
        CONF_HISTORY_DAYS: 7,
        CONF_FORECAST_TYPE: FORECAST_TYPE_HISTORICAL_SHIFT,
    }
    if source_unit:
        data[CONF_SOURCE_UNIT] = source_unit
    if source_device_class:
        data[CONF_SOURCE_DEVICE_CLASS] = source_device_class

    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test Forecast",
        data=data,
        entry_id="test_entry_id",
    )
    entry.add_to_hass(hass)
    return entry


async def test_sensor_copies_unit_from_source_entity(hass: HomeAssistant) -> None:
    """Sensor copies unit_of_measurement from source entity."""
    hass.states.async_set(
        "sensor.test_power",
        "100.0",
        {"unit_of_measurement": "W", "device_class": "power"},
    )

    entry = _create_mock_entry(hass)
    coordinator = create_forecaster(hass, entry)
    sensor = HafoForecastSensor(coordinator)

    assert sensor.native_unit_of_measurement == "W"
    assert sensor.device_class == SensorDeviceClass.POWER


async def test_sensor_copies_unit_only_when_no_device_class(hass: HomeAssistant) -> None:
    """Sensor copies unit when source has unit but no device_class."""
    hass.states.async_set("sensor.test_power", "100.0", {"unit_of_measurement": "W"})

    entry = _create_mock_entry(hass)
    coordinator = create_forecaster(hass, entry)
    sensor = HafoForecastSensor(coordinator)

    assert sensor.native_unit_of_measurement == "W"
    assert sensor.device_class is None


async def test_sensor_copies_device_class_only_when_no_unit(hass: HomeAssistant) -> None:
    """Sensor copies device_class when source has device_class but no unit."""
    hass.states.async_set("sensor.test_power", "100.0", {"device_class": "power"})

    entry = _create_mock_entry(hass)
    coordinator = create_forecaster(hass, entry)
    sensor = HafoForecastSensor(coordinator)

    assert sensor.device_class == SensorDeviceClass.POWER
    assert sensor.native_unit_of_measurement is None


async def test_sensor_persists_unit_to_config_entry(hass: HomeAssistant) -> None:
    """Sensor persists unit/device_class to config entry when source entity is available."""
    hass.states.async_set(
        "sensor.test_power",
        "100.0",
        {"unit_of_measurement": "kWh", "device_class": "energy"},
    )

    entry = _create_mock_entry(hass)
    coordinator = create_forecaster(hass, entry)
    HafoForecastSensor(coordinator)

    # Check that the config entry was updated with the source attributes
    assert entry.data.get(CONF_SOURCE_UNIT) == "kWh"
    assert entry.data.get(CONF_SOURCE_DEVICE_CLASS) == "energy"


async def test_sensor_loads_stored_unit_when_source_unavailable(hass: HomeAssistant) -> None:
    """Sensor loads stored unit/device_class when source entity doesn't exist yet."""
    # Source entity does NOT exist
    # But we have stored values from previous run
    entry = _create_mock_entry(
        hass,
        source_unit="W",
        source_device_class="power",
    )
    coordinator = create_forecaster(hass, entry)
    sensor = HafoForecastSensor(coordinator)

    # Should have loaded from stored values
    assert sensor.native_unit_of_measurement == "W"
    assert sensor.device_class == SensorDeviceClass.POWER


async def test_sensor_updates_stored_values_when_source_changes(hass: HomeAssistant) -> None:
    """Sensor updates stored values when source entity attributes change."""
    # Start with stored values
    entry = _create_mock_entry(
        hass,
        source_unit="W",
        source_device_class="power",
    )

    # Source entity has different values now
    hass.states.async_set(
        "sensor.test_power",
        "100.0",
        {"unit_of_measurement": "kW", "device_class": "power"},
    )

    coordinator = create_forecaster(hass, entry)
    sensor = HafoForecastSensor(coordinator)

    # Should have updated to new values
    assert sensor.native_unit_of_measurement == "kW"
    assert entry.data.get(CONF_SOURCE_UNIT) == "kW"


async def test_sensor_handles_invalid_stored_device_class(hass: HomeAssistant) -> None:
    """Sensor gracefully handles invalid stored device_class."""
    # Source entity does NOT exist
    # Stored device_class is invalid
    entry = _create_mock_entry(
        hass,
        source_unit="W",
        source_device_class="invalid_class",
    )
    coordinator = create_forecaster(hass, entry)
    sensor = HafoForecastSensor(coordinator)

    # Unit should still load
    assert sensor.native_unit_of_measurement == "W"
    # Device class should not be set (invalid value ignored)
    assert sensor.device_class is None


async def test_sensor_does_not_update_entry_when_values_unchanged(hass: HomeAssistant) -> None:
    """Sensor doesn't update config entry when values haven't changed."""
    hass.states.async_set(
        "sensor.test_power",
        "100.0",
        {"unit_of_measurement": "W", "device_class": "power"},
    )

    # Entry already has the same values stored
    entry = _create_mock_entry(
        hass,
        source_unit="W",
        source_device_class="power",
    )

    with patch.object(
        hass.config_entries, "async_update_entry", wraps=hass.config_entries.async_update_entry
    ) as mock_update:
        coordinator = create_forecaster(hass, entry)
        HafoForecastSensor(coordinator)

        # Should not have called update since values are the same
        assert mock_update.call_count == 0


async def test_sensor_updates_when_source_becomes_available(hass: HomeAssistant) -> None:
    """Sensor updates source attributes when source entity becomes available."""
    # Initially source doesn't exist
    entry = _create_mock_entry(
        hass,
        source_unit="W",
        source_device_class="power",
    )
    coordinator = create_forecaster(hass, entry)
    sensor = HafoForecastSensor(coordinator)

    assert sensor.native_unit_of_measurement == "W"

    # Now source entity appears with different unit
    hass.states.async_set(
        "sensor.test_power",
        "100.0",
        {"unit_of_measurement": "kW", "device_class": "power"},
    )

    # Simulate the update that happens during coordinator update
    sensor._update_from_source_entity()

    # Should have updated to new value
    assert sensor.native_unit_of_measurement == "kW"
    assert entry.data.get(CONF_SOURCE_UNIT) == "kW"


async def test_sensor_only_persists_non_none_values(hass: HomeAssistant) -> None:
    """Sensor only persists unit/device_class when they have values."""
    # Source entity exists but has no unit or device_class
    hass.states.async_set("sensor.test_power", "100.0", {})

    entry = _create_mock_entry(hass)
    coordinator = create_forecaster(hass, entry)
    HafoForecastSensor(coordinator)

    # Should not have stored None values
    assert CONF_SOURCE_UNIT not in entry.data
    assert CONF_SOURCE_DEVICE_CLASS not in entry.data


async def test_sensor_native_value_none_when_no_data(hass: HomeAssistant) -> None:
    """Sensor native_value is None when coordinator has no data."""
    hass.states.async_set("sensor.test_power", "100.0", {})
    entry = _create_mock_entry(hass)
    coordinator = create_forecaster(hass, entry)
    coordinator.data = None
    sensor = HafoForecastSensor(coordinator)

    assert sensor.native_value is None


async def test_sensor_native_value_none_when_forecast_empty(hass: HomeAssistant) -> None:
    """Sensor native_value is None when forecast list is empty."""
    hass.states.async_set("sensor.test_power", "100.0", {})
    entry = _create_mock_entry(hass)
    coordinator = create_forecaster(hass, entry)
    coordinator.data = ForecastResult(
        forecast=[],
        source_entity="sensor.test_power",
        history_days=7,
        generated_at=dt_util.now(),
    )
    sensor = HafoForecastSensor(coordinator)

    assert sensor.native_value is None


async def test_sensor_native_value_returns_closest_forecast_point(hass: HomeAssistant) -> None:
    """Sensor native_value returns value of forecast point closest to now."""
    hass.states.async_set("sensor.test_power", "100.0", {})
    entry = _create_mock_entry(hass)
    coordinator = create_forecaster(hass, entry)
    now = dt_util.now()
    coordinator.data = ForecastResult(
        forecast=[
            ForecastPoint(time=now, value=2.5),
            ForecastPoint(time=now.replace(hour=now.hour + 1), value=3.0),
        ],
        source_entity="sensor.test_power",
        history_days=7,
        generated_at=now,
    )
    sensor = HafoForecastSensor(coordinator)

    assert sensor.native_value == 2.5


async def test_sensor_extra_state_attributes_includes_forecast(hass: HomeAssistant) -> None:
    """Sensor extra_state_attributes includes forecast and last_updated when data present."""
    hass.states.async_set("sensor.test_power", "100.0", {})
    entry = _create_mock_entry(hass)
    coordinator = create_forecaster(hass, entry)
    now = datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)
    coordinator.data = ForecastResult(
        forecast=[ForecastPoint(time=now, value=1.0)],
        source_entity="sensor.test_power",
        history_days=7,
        generated_at=now,
    )
    sensor = HafoForecastSensor(coordinator)

    attrs = sensor.extra_state_attributes

    assert attrs[ATTR_LAST_UPDATED] == now.isoformat()
    assert attrs[ATTR_FORECAST] == [{"time": now.isoformat(), "value": 1.0}]


async def test_sensor_extra_state_attributes_without_result(hass: HomeAssistant) -> None:
    """Sensor extra_state_attributes omits forecast/last_updated when coordinator has no data."""
    hass.states.async_set("sensor.test_power", "100.0", {})
    entry = _create_mock_entry(hass)
    coordinator = create_forecaster(hass, entry)
    coordinator.data = None
    sensor = HafoForecastSensor(coordinator)

    attrs = sensor.extra_state_attributes

    assert ATTR_LAST_UPDATED not in attrs
    assert ATTR_FORECAST not in attrs
    assert attrs[ATTR_SOURCE_ENTITY] == "sensor.test_power"


async def test_sensor_handle_coordinator_update_refreshes_source_attributes(
    hass: HomeAssistant,
) -> None:
    """_handle_coordinator_update calls _update_from_source_entity before super."""
    hass.states.async_set("sensor.test_power", "100.0", {"unit_of_measurement": "W"})
    entry = _create_mock_entry(hass)
    coordinator = create_forecaster(hass, entry)
    sensor = HafoForecastSensor(coordinator)

    with (
        patch.object(sensor, "_update_from_source_entity") as mock_update,
        patch.object(CoordinatorEntity, "_handle_coordinator_update"),
    ):
        sensor._handle_coordinator_update()

    mock_update.assert_called_once()


async def test_async_setup_entry_adds_sensor_entity(hass: HomeAssistant) -> None:
    """async_setup_entry adds HafoForecastSensor via async_add_entities."""
    hass.states.async_set("sensor.test_power", "100.0", {})
    entry = _create_mock_entry(hass)
    coordinator = create_forecaster(hass, entry)
    entry.runtime_data = coordinator

    add_entities: list[Entity] = []

    def async_add_entities(
        new_entities: Iterable[Entity],
        update_before_add: bool = False,  # noqa: FBT001, FBT002
        *,
        config_subentry_id: str | None = None,
    ) -> None:
        add_entities.extend(new_entities)

    await async_setup_entry(hass, entry, async_add_entities)

    assert len(add_entities) == 1
    assert isinstance(add_entities[0], HafoForecastSensor)
