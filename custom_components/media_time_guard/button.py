"""Button platform for Media Time Guard (convenient quick-extend buttons)."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import MediaTimeGuardConfigEntry
from .const import EXTEND_BUTTON_PRESETS
from .coordinator import PersonGuard
from .entity import MediaTimeGuardEntity

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MediaTimeGuardConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the quick-extend buttons."""
    async_add_entities(
        ExtendButton(entry.runtime_data, minutes) for minutes in EXTEND_BUTTON_PRESETS
    )


class ExtendButton(MediaTimeGuardEntity, ButtonEntity):
    """Adds a fixed number of extra minutes for today."""

    _attr_translation_key = "extend"

    def __init__(self, coordinator: PersonGuard, minutes: int) -> None:
        super().__init__(coordinator, f"extend_{minutes}", Platform.BUTTON, f"extend_{minutes}")
        self._minutes = minutes
        self._attr_translation_placeholders = {"minutes": str(minutes)}

    async def async_press(self) -> None:
        await self.coordinator.async_extend_time(self._minutes)
