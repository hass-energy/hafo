```instructions
---
description: HAFO project context and agent behavioral rules - always applied
alwaysApply: true
---

# GitHub Copilot Instructions

This repository contains **HAFO** (Home Assistant Forecaster) - a Python 3.13+ Home Assistant custom component for creating forecast helpers from entity history.

## Project overview

HAFO creates forecast sensor helpers that transform historical entity data into future predictions.
The integration works with Home Assistant's recorder/statistics to shift historical patterns forward in time.

### Core components

The integration follows a simple architecture:

- **Forecasters** (`forecasters/`): Core forecasting logic (historical shift, etc.)
- **Coordinator** (`coordinator.py`): Orchestrates data loading and forecast updates
- **Sensors** (`sensor.py`): Expose forecast data to Home Assistant
- **Config flows** (`config_flow.py`): Helper-based configuration

### Project structure

```
custom_components/hafo/     # Home Assistant integration
├── forecasters/            # Forecasting algorithms
├── translations/           # i18n strings (en.json)
tests/                      # Test suite
docs/                       # Documentation
```

## Development tools

- **Package manager**: uv (use `uv sync` for dependencies, `uv run` to execute tools)
- **Testing**: pytest
- **Linting/Formatting**: Ruff (Python), Prettier (JSON), mdformat (Markdown)
- **Type checking**: Pyright

## Agent behavioral rules

These rules apply to all AI agent interactions with this codebase:

### Clean changes

When making changes, don't leave behind comments describing what was once there.
Comments should always describe code as it exists without reference to former code.

### API evolution

When making changes, don't leave behind backwards-compatible interfaces for internal APIs.
There should always be a complete clean changeover.

### Error context

The main branch is always clean with no errors or warnings.
Any errors, warnings, or test failures you encounter are directly related to recent changes in the current branch/PR.
These issues must be fixed as part of the work - they indicate problems introduced by the changes being made.

### Property access

Always assume that accessed properties/fields which should exist do exist directly.
Rely on errors occurring if they do not when they indicate a coding error and not a possibly None value.
This is especially true in tests where you have added entities and then must access them later.
Having None checks there reduces readability and makes the test more fragile to passing unexpectedly.

## Universal code standards

- **Python**: 3.13+ with modern features (pattern matching, `str | None` syntax, f-strings, dataclasses)
- **Type hints**: Required on all functions, methods, and variables
- **Formatting**: Ruff (Python), Prettier (JSON), mdformat (Markdown)
- **Linting**: Ruff
- **Type checking**: Pyright
- **Language**: American English for all code, comments, and documentation
- **Testing**: pytest with coverage enforced by codecov on changed lines

### Units

HAFO uses Home Assistant conventions:

- Time: seconds (timestamps)
- Power: watts (W) or kilowatts (kW) depending on source entity
- Energy: watt-hours (Wh) or kilowatt-hours (kWh) depending on source entity

### Version matching

The version number must be consistent across:

- `pyproject.toml` (`version = "x.y.z"`)
- `custom_components/hafo/manifest.json` (`"version": "x.y.z"`)

When updating version numbers, update both files together.

```
