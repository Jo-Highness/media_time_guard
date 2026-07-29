"""Switch platform for Media Time Guard."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import ATTR_IS_SUSPENDED, DOMAIN
from .coordinator import PersonGuard
from .entity import MediaTimeGuardEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the suspend switch."""
    guard: PersonGuard = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SuspendTodaySwitch(guard)])


class SuspendTodaySwitch(MediaTimeGuardEntity, SwitchEntity):
    """Suspend enforcement for today (e.g. the child is ill)."""

    _attr_icon = "mdi:account-clock"

    def __init__(self, coordinator: PersonGuard) -> None:
        super().__init__(coordinator, "suspend_today")
        self._attr_translation_key = "suspend_today"
        self.entity_id = f"switch.media_time_{coordinator.slug}_suspend_today"

    @property
    def is_on(self) -> bool:
        data = self.coordinator.data or {}
        return bool(data.get(ATTR_IS_SUSPENDED, False))

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_suspended(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_suspended(False)
