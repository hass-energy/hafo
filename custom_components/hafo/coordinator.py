"""Data update coordinator for Home Assistant Forecaster."""

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_FORECAST_TYPE,
    CONF_HISTORY_DAYS,
    CONF_SOURCE_ENTITY,
    DEFAULT_FORECAST_TYPE,
    DEFAULT_HISTORY_DAYS,
    DOMAIN,
    FORECAST_TYPE_HISTORICAL_SHIFT,
)
from .forecasters import HistoricalShiftForecaster
from .forecasters.historical_shift import ForecastResult

_LOGGER = logging.getLogger(__name__)

# Update interval for forecast refresh (hourly)
UPDATE_INTERVAL = timedelta(hours=1)


class HafoDataUpdateCoordinator(DataUpdateCoordinator[ForecastResult | None]):
    """Coordinator to manage forecast data updates."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator.

        Args:
            hass: Home Assistant instance
            entry: Config entry for this forecaster

        """
        self._entry = entry
        self._source_entity = entry.data[CONF_SOURCE_ENTITY]
        self._history_days = entry.data.get(CONF_HISTORY_DAYS, DEFAULT_HISTORY_DAYS)
        self._forecast_type = entry.data.get(CONF_FORECAST_TYPE, DEFAULT_FORECAST_TYPE)

        # Initialize the appropriate forecaster
        self._forecaster = self._create_forecaster()

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=UPDATE_INTERVAL,
            config_entry=entry,
        )

    def _create_forecaster(self) -> HistoricalShiftForecaster:
        """Create the forecaster based on configuration."""
        if self._forecast_type == FORECAST_TYPE_HISTORICAL_SHIFT:
            return HistoricalShiftForecaster(history_days=int(self._history_days))
        # Default to historical shift
        return HistoricalShiftForecaster(history_days=int(self._history_days))

    @property
    def source_entity(self) -> str:
        """Return the source entity ID."""
        return self._source_entity

    @property
    def history_days(self) -> int:
        """Return the number of history days."""
        return int(self._history_days)

    @property
    def entry(self) -> ConfigEntry:
        """Return the config entry."""
        return self._entry

    async def _async_update_data(self) -> ForecastResult | None:
        """Fetch and update forecast data.

        Returns:
            ForecastResult with the latest forecast, or None if unavailable.

        Raises:
            UpdateFailed: If the forecast cannot be generated.

        """
        try:
            # Check if forecaster can generate data for this entity
            if not await self._forecaster.available(self.hass, self._source_entity):
                _LOGGER.warning(
                    "Forecaster not available for entity %s - recorder may not be ready",
                    self._source_entity,
                )
                return None

            # Generate the forecast
            result = await self._forecaster.generate_forecast(
                self.hass,
                self._source_entity,
            )

            _LOGGER.debug(
                "Generated forecast for %s with %d points",
                self._source_entity,
                len(result.forecast),
            )

            return result

        except ValueError as err:
            _LOGGER.warning("Failed to generate forecast: %s", err)
            # Return None instead of raising to allow graceful degradation
            return None
        except Exception as err:
            msg = f"Error generating forecast: {err}"
            raise UpdateFailed(msg) from err

    def cleanup(self) -> None:
        """Clean up coordinator resources."""
        _LOGGER.debug("Cleaning up coordinator for %s", self._source_entity)
