"""Base entity for Media Time Guard."""

from __future__ import annotations

from homeassistant.core import Context
from homeassistant.exceptions import Unauthorized
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import PersonGuard


class MediaTimeGuardEntity(CoordinatorEntity[PersonGuard]):
    """Base class wiring entities to a person's :class:`PersonGuard`."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: PersonGuard, key: str, platform: str, object_suffix: str
    ) -> None:
        super().__init__(coordinator)
        self._key = key
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{key}"
        # Suggested entity_id only. Home Assistant uses it when the entity is
        # first registered; afterwards the entity registry wins, so existing
        # IDs (and IDs renamed by the user) never change - not even when the
        # person is renamed. Kept so every person gets the same, documented,
        # language-independent pattern: <platform>.media_time_<slug>_<suffix>.
        self.entity_id = f"{platform}.media_time_{coordinator.slug}_{object_suffix}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.entry.entry_id)},
            name=coordinator.person_name,
            manufacturer="Media Time Guard",
            model="Per-person media time budget",
            entry_type=DeviceEntryType.SERVICE,
        )

    def _action_context(self) -> Context:
        """Return the context of the service call that triggered this action.

        Home Assistant sets it via ``async_set_context`` right before calling
        the entity method. It must be read before the first ``await``
        (``PARALLEL_UPDATES = 0`` lets calls for this entity interleave).
        Without a context the caller is unknown -> refuse (fail closed).
        """
        context = self._context
        if context is None:
            raise Unauthorized(config_entry_id=self.coordinator.entry.entry_id)
        return context
