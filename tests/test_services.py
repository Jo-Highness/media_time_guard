"""Tests for the integration services (actions)."""

from __future__ import annotations

from homeassistant.exceptions import ServiceValidationError
import pytest
from pytest_homeassistant_custom_component.common import async_mock_service
import voluptuous as vol

from custom_components.media_time_guard.const import (
    DOMAIN,
    SERVICE_EXTEND_TIME,
    SERVICE_RESET_PERSON,
    SERVICE_SUSPEND_TODAY,
)

from .conftest import setup_person


async def test_services_registered_without_entries(hass):
    """Services exist as soon as the integration is set up (async_setup)."""
    from homeassistant.setup import async_setup_component

    assert await async_setup_component(hass, DOMAIN, {})
    for service in (SERVICE_EXTEND_TIME, SERVICE_SUSPEND_TODAY, SERVICE_RESET_PERSON):
        assert hass.services.has_service(DOMAIN, service)


async def test_suspend_today_service(hass):
    """suspend_today toggles the suspension for the person."""
    entry = await setup_person(hass, name="Luke")
    await hass.services.async_call(
        DOMAIN, SERVICE_SUSPEND_TODAY, {"person": "luke", "suspended": True}, blocking=True
    )
    assert entry.runtime_data.data["is_suspended"] is True
    assert hass.states.get("switch.media_time_luke_suspend_today").state == "on"

    await hass.services.async_call(
        DOMAIN, SERVICE_SUSPEND_TODAY, {"person": "Luke", "suspended": False}, blocking=True
    )
    assert entry.runtime_data.data["is_suspended"] is False


async def test_reset_person_service(hass):
    """reset_person clears extra minutes, suspension and lock."""
    entry = await setup_person(hass, name="Luke")
    guard = entry.runtime_data
    await guard.async_extend_time(20)
    await guard.async_set_suspended(True)

    await hass.services.async_call(DOMAIN, SERVICE_RESET_PERSON, {"person": "Luke"}, blocking=True)
    assert guard.data["extra_minutes_today"] == 0
    assert guard.data["is_suspended"] is False
    assert guard.data["used_minutes"] == 0.0


async def test_service_by_config_entry_id(hass):
    """config_entry_id addresses a person independent of its name."""
    await setup_person(hass, name="Leo", players=["media_player.leo"])
    entry = await setup_person(hass, name="Luke")
    await hass.services.async_call(
        DOMAIN,
        SERVICE_EXTEND_TIME,
        {"config_entry_id": entry.entry_id, "minutes": 10},
        blocking=True,
    )
    assert entry.runtime_data.data["extra_minutes_today"] == 10


async def test_service_unknown_person(hass):
    """An unknown person raises a translated validation error."""
    await setup_person(hass, name="Luke")
    with pytest.raises(ServiceValidationError) as err:
        await hass.services.async_call(
            DOMAIN, SERVICE_RESET_PERSON, {"person": "Nobody"}, blocking=True
        )
    assert err.value.translation_key == "person_not_found"
    assert err.value.translation_domain == DOMAIN


async def test_service_unknown_and_unloaded_entry(hass):
    """Bad or unloaded config entries are rejected."""
    entry = await setup_person(hass, name="Luke")
    with pytest.raises(ServiceValidationError) as err:
        await hass.services.async_call(
            DOMAIN, SERVICE_RESET_PERSON, {"config_entry_id": "nope"}, blocking=True
        )
    assert err.value.translation_key == "entry_not_found"

    assert await hass.config_entries.async_unload(entry.entry_id)
    with pytest.raises(ServiceValidationError) as err:
        await hass.services.async_call(
            DOMAIN, SERVICE_RESET_PERSON, {"config_entry_id": entry.entry_id}, blocking=True
        )
    assert err.value.translation_key == "entry_not_loaded"


async def test_service_requires_a_target(hass):
    """Either person or config_entry_id must be given."""
    await setup_person(hass, name="Luke")
    with pytest.raises(vol.Invalid):
        await hass.services.async_call(DOMAIN, SERVICE_RESET_PERSON, {}, blocking=True)


async def test_service_after_rename(hass):
    """After renaming, the new name resolves the person."""
    async_mock_service(hass, "media_player", "media_stop")
    entry = await setup_person(hass, name="Luke")
    options = {**entry.data, "name": "Lukas"}
    hass.config_entries.async_update_entry(entry, title="Lukas", options=options)
    await hass.async_block_till_done()

    await hass.services.async_call(
        DOMAIN, SERVICE_EXTEND_TIME, {"person": "Lukas", "minutes": 5}, blocking=True
    )
    assert entry.runtime_data.data["extra_minutes_today"] == 5
