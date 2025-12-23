"""Test configuration and fixtures for HAFO."""

from logging import config as logging_config_module

import pytest

# Enable custom component for testing
pytest_plugins = ["pytest_homeassistant_custom_component"]


@pytest.fixture(autouse=True, scope="session")
def configure_logging() -> None:
    """Configure logging to suppress verbose Home Assistant DEBUG messages during tests."""
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "brief": {"format": "%(levelname)s: %(name)s: %(message)s"},
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "brief",
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            # Suppress verbose DEBUG logs from Home Assistant core
            "homeassistant.core": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False,
            },
            # Keep our custom component logs at INFO level for debugging
            "custom_components.hafo": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
        },
        "root": {
            "level": "WARNING",
            "handlers": ["console"],
        },
    }
    logging_config_module.dictConfig(logging_config)
