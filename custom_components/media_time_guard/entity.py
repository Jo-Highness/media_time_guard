"""Base entity for Media Time Guard."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import PersonGuard


class MediaTimeGuardEntity(CoordinatorEntity[PersonGuard]):
    """Base class wiring entities to a person's :class:`PersonGuard`."""

    _attr_has_entity_name = False

    def __init__(self, coordinator: PersonGuard, key: str) -> None:
        super().__init__(coordinator)
        self._key = key
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.entry.entry_id)},
            name=coordinator.person_name,
            manufacturer="Media Time Guard",
            model="Per-person media time budget",
        )
