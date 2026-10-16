"""Sensor platform for Media Time Guard."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import Platform, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import MediaTimeGuardConfigEntry
from .const import (
    ATTR_BUDGET_MINUTES,
    ATTR_EFFECTIVE_BUDGET_MINUTES,
    ATTR_EXTRA_MINUTES_TODAY,
    ATTR_IS_LOCKED,
    ATTR_IS_PLAYING,
    ATTR_IS_SUSPENDED,
    ATTR_LAST_RESET,
    ATTR_PLAYERS,
    ATTR_REMAINING_MINUTES,
    ATTR_USED_MINUTES,
    ATTR_WARNED_TODAY,
    ATTR_WEEKDAY,
)
from .coordinator import PersonGuard
from .entity import MediaTimeGuardEntity

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MediaTimeGuardConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the remaining-time sensor."""
    async_add_entities([RemainingSensor(entry.runtime_data)])


class RemainingSensor(MediaTimeGuardEntity, SensorEntity):
    """Remaining media minutes for today (main variable)."""

    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_translation_key = "remaining"

    def __init__(self, coordinator: PersonGuard) -> None:
        super().__init__(coordinator, "remaining", Platform.SENSOR, "remaining")

    @property
    def native_value(self) -> float | None:
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get(ATTR_REMAINING_MINUTES)

    @property
    def extra_state_attributes(self) -> dict:
        data = self.coordinator.data or {}
        return {
            ATTR_BUDGET_MINUTES: data.get(ATTR_BUDGET_MINUTES),
            ATTR_USED_MINUTES: data.get(ATTR_USED_MINUTES),
            ATTR_REMAINING_MINUTES: data.get(ATTR_REMAINING_MINUTES),
            ATTR_EFFECTIVE_BUDGET_MINUTES: data.get(ATTR_EFFECTIVE_BUDGET_MINUTES),
            ATTR_WEEKDAY: data.get(ATTR_WEEKDAY),
            ATTR_IS_PLAYING: data.get(ATTR_IS_PLAYING),
            ATTR_IS_LOCKED: data.get(ATTR_IS_LOCKED),
            ATTR_IS_SUSPENDED: data.get(ATTR_IS_SUSPENDED),
            ATTR_EXTRA_MINUTES_TODAY: data.get(ATTR_EXTRA_MINUTES_TODAY),
            ATTR_WARNED_TODAY: data.get(ATTR_WARNED_TODAY),
            ATTR_LAST_RESET: data.get(ATTR_LAST_RESET),
            ATTR_PLAYERS: data.get(ATTR_PLAYERS),
        }
