"""The Media Time Guard integration."""

from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv

from .const import (
    ATTR_MINUTES,
    ATTR_PERSON,
    ATTR_SUSPENDED,
    DOMAIN,
    SERVICE_EXTEND_TIME,
    SERVICE_RESET_PERSON,
    SERVICE_SUSPEND_TODAY,
)
from .coordinator import PersonGuard

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "switch", "number", "button"]

EXTEND_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_PERSON): cv.string,
        vol.Required(ATTR_MINUTES): vol.All(vol.Coerce(int), vol.Range(min=1)),
    }
)
SUSPEND_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_PERSON): cv.string,
        vol.Required(ATTR_SUSPENDED): cv.boolean,
    }
)
RESET_SCHEMA = vol.Schema({vol.Required(ATTR_PERSON): cv.string})


def _find_guard(hass: HomeAssistant, person: str) -> PersonGuard:
    """Resolve a person string to its :class:`PersonGuard`."""
    needle = person.strip().casefold()
    for guard in hass.data.get(DOMAIN, {}).values():
        if not isinstance(guard, PersonGuard):
            continue
        if needle in (guard.person_name.casefold(), guard.slug.casefold()):
            return guard
    raise ServiceValidationError(
        f"No Media Time Guard person matches '{person}'"
    )


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Media Time Guard from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    guard = PersonGuard(hass, entry)
    await guard.async_setup()
    hass.data[DOMAIN][entry.entry_id] = guard

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    _async_register_services(hass)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        guard: PersonGuard = hass.data[DOMAIN].pop(entry.entry_id)
        await guard.async_shutdown()

    # Remove the shared services once the last entry is gone.
    if not hass.data.get(DOMAIN):
        for service in (
            SERVICE_EXTEND_TIME,
            SERVICE_SUSPEND_TODAY,
            SERVICE_RESET_PERSON,
        ):
            hass.services.async_remove(DOMAIN, service)

    return unload_ok


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the entry when its options change."""
    await hass.config_entries.async_reload(entry.entry_id)


def _async_register_services(hass: HomeAssistant) -> None:
    """Register integration services (idempotent)."""
    if hass.services.has_service(DOMAIN, SERVICE_EXTEND_TIME):
        return

    async def _handle_extend(call: ServiceCall) -> None:
        guard = _find_guard(hass, call.data[ATTR_PERSON])
        await guard.async_extend_time(call.data[ATTR_MINUTES])

    async def _handle_suspend(call: ServiceCall) -> None:
        guard = _find_guard(hass, call.data[ATTR_PERSON])
        await guard.async_set_suspended(call.data[ATTR_SUSPENDED])

    async def _handle_reset(call: ServiceCall) -> None:
        guard = _find_guard(hass, call.data[ATTR_PERSON])
        await guard.async_reset_person()

    hass.services.async_register(
        DOMAIN, SERVICE_EXTEND_TIME, _handle_extend, schema=EXTEND_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_SUSPEND_TODAY, _handle_suspend, schema=SUSPEND_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_RESET_PERSON, _handle_reset, schema=RESET_SCHEMA
    )
