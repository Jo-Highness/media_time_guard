"""Switch platform for Media Time Guard."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import MediaTimeGuardConfigEntry
from .const import ATTR_IS_SUSPENDED
from .coordinator import PersonGuard
from .entity import MediaTimeGuardEntity

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MediaTimeGuardConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the suspend switch."""
    async_add_entities([SuspendTodaySwitch(entry.runtime_data)])


class SuspendTodaySwitch(MediaTimeGuardEntity, SwitchEntity):
    """Suspend enforcement for today (e.g. the child is ill)."""

    _attr_translation_key = "suspend_today"

    def __init__(self, coordinator: PersonGuard) -> None:
        super().__init__(coordinator, "suspend_today", Platform.SWITCH, "suspend_today")

    @property
    def is_on(self) -> bool:
        data = self.coordinator.data or {}
        return bool(data.get(ATTR_IS_SUSPENDED, False))

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_suspended(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_suspended(False)
