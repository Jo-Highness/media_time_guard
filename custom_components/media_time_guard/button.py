"""Button platform for Media Time Guard (convenient quick-extend buttons)."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, EXTEND_BUTTON_PRESETS
from .coordinator import PersonGuard
from .entity import MediaTimeGuardEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the quick-extend buttons."""
    guard: PersonGuard = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(ExtendButton(guard, minutes) for minutes in EXTEND_BUTTON_PRESETS)


class ExtendButton(MediaTimeGuardEntity, ButtonEntity):
    """Adds a fixed number of extra minutes for today."""

    _attr_icon = "mdi:timer-plus"

    def __init__(self, coordinator: PersonGuard, minutes: int) -> None:
        super().__init__(coordinator, f"extend_{minutes}")
        self._minutes = minutes
        self._attr_name = f"Media Time {coordinator.person_name} +{minutes} min"
        self.entity_id = f"button.media_time_{coordinator.slug}_extend_{minutes}"

    async def async_press(self) -> None:
        await self.coordinator.async_extend_time(self._minutes)
