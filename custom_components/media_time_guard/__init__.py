"""The Media Time Guard integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv, issue_registry as ir
from homeassistant.helpers.start import async_at_started
from homeassistant.helpers.typing import ConfigType
import voluptuous as vol

from .const import (
    ATTR_BLOCKED,
    ATTR_CONFIG_ENTRY_ID,
    ATTR_MINUTES,
    ATTR_PERSON,
    ATTR_SUSPENDED,
    DOMAIN,
    EXTRA_MINUTES_MAX,
    SERVICE_EXTEND_TIME,
    SERVICE_RESET_PERSON,
    SERVICE_SET_BLOCKED,
    SERVICE_SUSPEND_TODAY,
)
from .coordinator import PersonGuard, missing_entities_issue_id

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.SWITCH, Platform.NUMBER, Platform.BUTTON]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

type MediaTimeGuardConfigEntry = ConfigEntry[PersonGuard]

# Every service addresses one person, either by name/slug (``person``) or by
# its config entry (``config_entry_id``, stable across renames).
_TARGET_FIELDS = {
    vol.Optional(ATTR_PERSON): cv.string,
    vol.Optional(ATTR_CONFIG_ENTRY_ID): cv.string,
}
_REQUIRE_TARGET = cv.has_at_least_one_key(ATTR_PERSON, ATTR_CONFIG_ENTRY_ID)

EXTEND_SCHEMA = vol.All(
    vol.Schema(
        {
            **_TARGET_FIELDS,
            vol.Required(ATTR_MINUTES): vol.All(
                vol.Coerce(int), vol.Range(min=1, max=EXTRA_MINUTES_MAX)
            ),
        }
    ),
    _REQUIRE_TARGET,
)
SUSPEND_SCHEMA = vol.All(
    vol.Schema({**_TARGET_FIELDS, vol.Required(ATTR_SUSPENDED): cv.boolean}),
    _REQUIRE_TARGET,
)
BLOCKED_SCHEMA = vol.All(
    vol.Schema({**_TARGET_FIELDS, vol.Required(ATTR_BLOCKED): cv.boolean}),
    _REQUIRE_TARGET,
)
RESET_SCHEMA = vol.All(vol.Schema(_TARGET_FIELDS), _REQUIRE_TARGET)


def _loaded_entries(hass: HomeAssistant) -> list[MediaTimeGuardConfigEntry]:
    return [
        entry
        for entry in hass.config_entries.async_entries(DOMAIN)
        if entry.state is ConfigEntryState.LOADED
    ]


def _find_guard(hass: HomeAssistant, call: ServiceCall) -> PersonGuard:
    """Resolve the service call target to its :class:`PersonGuard`."""
    if entry_id := call.data.get(ATTR_CONFIG_ENTRY_ID):
        entry = hass.config_entries.async_get_entry(entry_id)
        if entry is None or entry.domain != DOMAIN:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="entry_not_found",
                translation_placeholders={"entry_id": entry_id},
            )
        if entry.state is not ConfigEntryState.LOADED:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="entry_not_loaded",
                translation_placeholders={"name": entry.title},
            )
        return entry.runtime_data

    person: str = call.data[ATTR_PERSON]
    needle = person.strip().casefold()
    for entry in _loaded_entries(hass):
        guard = entry.runtime_data
        if needle in (
            guard.person_name.casefold(),
            guard.slug.casefold(),
            entry.title.casefold(),
        ):
            return guard
    raise ServiceValidationError(
        translation_domain=DOMAIN,
        translation_key="person_not_found",
        translation_placeholders={"person": person},
    )


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Register the integration's services (once, independent of entries)."""

    async def _handle_extend(call: ServiceCall) -> None:
        await _find_guard(hass, call).async_extend_time(call.data[ATTR_MINUTES])

    async def _handle_suspend(call: ServiceCall) -> None:
        await _find_guard(hass, call).async_set_suspended(call.data[ATTR_SUSPENDED])

    async def _handle_blocked(call: ServiceCall) -> None:
        await _find_guard(hass, call).async_set_blocked(call.data[ATTR_BLOCKED])

    async def _handle_reset(call: ServiceCall) -> None:
        await _find_guard(hass, call).async_reset_person()

    hass.services.async_register(DOMAIN, SERVICE_EXTEND_TIME, _handle_extend, schema=EXTEND_SCHEMA)
    hass.services.async_register(
        DOMAIN, SERVICE_SUSPEND_TODAY, _handle_suspend, schema=SUSPEND_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_SET_BLOCKED, _handle_blocked, schema=BLOCKED_SCHEMA
    )
    hass.services.async_register(DOMAIN, SERVICE_RESET_PERSON, _handle_reset, schema=RESET_SCHEMA)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: MediaTimeGuardConfigEntry) -> bool:
    """Set up Media Time Guard from a config entry."""
    guard = PersonGuard(hass, entry)
    await guard.async_setup()
    entry.runtime_data = guard

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    @callback
    def _check_missing(_hass: HomeAssistant) -> None:
        guard.async_check_missing_entities()

    entry.async_on_unload(async_at_started(hass, _check_missing))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: MediaTimeGuardConfigEntry) -> bool:
    """Unload a config entry.

    The guard's ``async_shutdown`` (listeners + final save) is registered by
    the coordinator itself via ``entry.async_on_unload``; no manual call here.
    """
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_remove_entry(hass: HomeAssistant, entry: MediaTimeGuardConfigEntry) -> None:
    """Clean up the repair issue when a person is removed."""
    ir.async_delete_issue(hass, DOMAIN, missing_entities_issue_id(entry.entry_id))


async def _async_update_listener(hass: HomeAssistant, entry: MediaTimeGuardConfigEntry) -> None:
    """Reload the entry when its options (or title) change."""
    await hass.config_entries.async_reload(entry.entry_id)
