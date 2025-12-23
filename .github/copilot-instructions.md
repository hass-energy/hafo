---
description: HAFO project context and agent behavioral rules - always applied
alwaysApply: true
---

# GitHub Copilot Instructions

This repository contains **HAFO** (Home Assistant Forecaster) - a Python 3.13+ Home Assistant custom component for creating forecast helper sensors from various forecasting engines.

## Project overview

HAFO creates forecast helper sensors by transforming historical data and other sources into future predictions.
It supports multiple forecasting engines that can be selected when creating a forecast helper.

### Core components

The integration follows a simple helper architecture:

- **Forecasters layer** (`forecasters/`): Forecasting engines (historical shift, etc.)
- **Coordinator** (`coordinator.py`): Orchestrates data loading and forecast generation
- **Sensors** (`sensor.py`): Expose forecast results to Home Assistant
- **Config flow** (`config_flow.py`): Helper-based configuration for forecast creation

### Project structure

```
custom_components/hafo/     # Home Assistant integration
├── forecasters/            # Forecasting engines
├── translations/           # i18n strings (en.json)
└── *.py                    # Core integration files
tests/                      # Test suite
├── forecasters/            # Forecaster unit tests
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
- **Typing philosophy**: Type at boundaries, use TypedDict/TypeGuard for narrowing, prefer types over runtime checks
- **Formatting**: Ruff (Python), Prettier (JSON), mdformat (Markdown)
- **Linting**: Ruff
- **Type checking**: Pyright
- **Language**: American English for all code, comments, and documentation
- **Testing**: pytest with coverage enforced by codecov on changed lines

### Forecast format

HAFO uses a consistent forecast format matching HAEO for interoperability:

```python
class ForecastPoint(TypedDict):
    time: datetime  # Timestamp as timezone-aware datetime
    value: float    # Forecast value
```

Forecasts are exposed as sensor attributes in JSON format:

```json
[{"time": "2025-01-15T10:00:00+00:00", "value": 2.5}, ...]
```

### Version matching

The version number must be consistent across:

- `pyproject.toml` (`version = "x.y.z"`)
- `custom_components/hafo/manifest.json` (`"version": "x.y.z"`)

When updating version numbers, update both files together.

## Path-specific instructions

This repository uses path-specific instruction files in `.github/instructions/` that apply additional context based on the files being edited.
See that directory for domain-specific guidelines.

## Documentation

- [Documentation guidelines](../docs/developer-guide/documentation-guidelines.md) - Writing and maintaining docs

## Self-maintenance

When the user provides feedback about systemic corrections (coding patterns, style issues, architectural decisions, or recurring mistakes), update the appropriate instruction file to capture that feedback for future sessions.

See `.github/instructions/meta.instructions.md` for guidance on maintaining both Copilot instructions and Cursor rules in sync.
