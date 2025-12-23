---
applyTo: custom_components/hafo/**
description: Home Assistant integration development standards
globs: [custom_components/hafo/**]
alwaysApply: false
---

# Home Assistant integration development

## Coordinator pattern

HAFO uses DataUpdateCoordinator for forecast scheduling.
The coordinator loads data from the recorder, runs forecasters, and exposes results.

- Pass `config_entry` to coordinator constructor
- Use `UpdateFailed` for data loading or forecast generation errors
- Integration determines update interval (not user-configurable)

## Entity development

### Unique IDs

Every entity must have a unique ID constructed from stable identifiers:

```python
self._attr_unique_id = f"{entry.entry_id}_forecast"
```

Acceptable sources: config entry ID, subentry ID.
Never use: IP addresses, hostnames, user-provided names.

### Entity naming

Use translation keys for all entity names:

```python
class MySensor(SensorEntity):
    _attr_has_entity_name = True
    _attr_translation_key = "forecast"
```

### State handling

- Use `None` for unknown values (not "unknown" string)
- Implement `available` property for availability

### Event lifecycle

```python
async def async_added_to_hass(self) -> None:
    """Subscribe to events."""
    self.async_on_remove(self.coordinator.async_add_listener(self._handle_update))
```

## Device registry

Group related entities under devices using translation keys:

```python
_attr_device_info = DeviceInfo(
    identifiers={(DOMAIN, device_id)},
    translation_key="forecaster",
)
```

## Exception handling

All exceptions that may reach the user must use Home Assistant exception types with translations.
Never raise generic exceptions that would show "unknown error" in the UI.

- `ConfigEntryNotReady`: Device offline or temporary failure
- `ConfigEntryError`: Unresolvable setup problems
- `UpdateFailed`: Data loading or forecast generation errors
- `HomeAssistantError`: User-facing errors with translation support

For service calls and user actions, use `HomeAssistantError` with a translation key:

```python
raise HomeAssistantError(
    translation_domain=DOMAIN,
    translation_key="forecast_failed",
)
```

## Diagnostics

Implement diagnostic data collection with redaction:

```python
TO_REDACT = [CONF_API_KEY, CONF_LATITUDE, CONF_LONGITUDE]


async def async_get_config_entry_diagnostics(hass: HomeAssistant, entry: ConfigEntry) -> dict[str, Any]:
    return async_redact_data(entry.data, TO_REDACT)
```

Never expose passwords, tokens, or sensitive coordinates.

## Setup and unload

```python
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up from config entry."""
    coordinator = MyCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
```
