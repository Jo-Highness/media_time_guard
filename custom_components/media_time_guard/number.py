"""Number platform for Media Time Guard."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    ATTR_EXTRA_MINUTES_TODAY,
    DOMAIN,
    EXTRA_MINUTES_MAX,
    EXTRA_MINUTES_MIN,
    EXTRA_MINUTES_STEP,
)
from .coordinator import PersonGuard
from .entity import MediaTimeGuardEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the extra-minutes number."""
    guard: PersonGuard = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ExtendNumber(guard)])


class ExtendNumber(MediaTimeGuardEntity, NumberEntity):
    """Extra minutes granted for today (raises the effective budget)."""

    _attr_icon = "mdi:timer-plus-outline"
    _attr_native_min_value = EXTRA_MINUTES_MIN
    _attr_native_max_value = EXTRA_MINUTES_MAX
    _attr_native_step = EXTRA_MINUTES_STEP
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES
    _attr_mode = NumberMode.BOX

    def __init__(self, coordinator: PersonGuard) -> None:
        super().__init__(coordinator, "extend")
        self._attr_translation_key = "extra_minutes"
        self.entity_id = f"number.media_time_{coordinator.slug}_extend"

    @property
    def native_value(self) -> float | None:
        data = self.coordinator.data or {}
        return data.get(ATTR_EXTRA_MINUTES_TODAY)

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_extra_minutes(int(value))
