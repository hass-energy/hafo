"""Tests for the HAFO sensor platform."""

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.hafo.const import (
    CONF_FORECAST_TYPE,
    CONF_HISTORY_DAYS,
    CONF_SOURCE_DEVICE_CLASS,
    CONF_SOURCE_ENTITY,
    CONF_SOURCE_UNIT,
    DOMAIN,
    FORECAST_TYPE_HISTORICAL_SHIFT,
)
from custom_components.hafo.coordinator import create_forecaster
from custom_components.hafo.sensor import HafoForecastSensor


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

    # Track calls to async_update_entry
    original_update = hass.config_entries.async_update_entry
    update_calls: list[MockConfigEntry] = []

    def tracking_update(entry: MockConfigEntry, **kwargs: dict) -> None:
        update_calls.append(entry)
        original_update(entry, **kwargs)

    hass.config_entries.async_update_entry = tracking_update  # type: ignore[method-assign]

    coordinator = create_forecaster(hass, entry)
    HafoForecastSensor(coordinator)

    # Should not have called update since values are the same
    assert len(update_calls) == 0


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
