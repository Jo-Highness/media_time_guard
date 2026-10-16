"""Number platform for Media Time Guard."""

from __future__ import annotations

from homeassistant.components.number import NumberDeviceClass, NumberEntity, NumberMode
from homeassistant.const import Platform, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import MediaTimeGuardConfigEntry
from .const import (
    ATTR_EXTRA_MINUTES_TODAY,
    EXTRA_MINUTES_MAX,
    EXTRA_MINUTES_MIN,
    EXTRA_MINUTES_STEP,
)
from .coordinator import PersonGuard
from .entity import MediaTimeGuardEntity

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MediaTimeGuardConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the extra-minutes number."""
    async_add_entities([ExtendNumber(entry.runtime_data)])


class ExtendNumber(MediaTimeGuardEntity, NumberEntity):
    """Extra minutes granted for today (raises the effective budget)."""

    _attr_device_class = NumberDeviceClass.DURATION
    _attr_native_min_value = EXTRA_MINUTES_MIN
    _attr_native_max_value = EXTRA_MINUTES_MAX
    _attr_native_step = EXTRA_MINUTES_STEP
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES
    _attr_mode = NumberMode.BOX
    _attr_translation_key = "extra_minutes"

    def __init__(self, coordinator: PersonGuard) -> None:
        super().__init__(coordinator, "extend", Platform.NUMBER, "extend")

    @property
    def native_value(self) -> float | None:
        data = self.coordinator.data or {}
        return data.get(ATTR_EXTRA_MINUTES_TODAY)

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_extra_minutes(int(value))
