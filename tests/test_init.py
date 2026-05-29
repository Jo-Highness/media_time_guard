"""Test full setup/unload of the integration."""

from __future__ import annotations

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.media_time_guard.const import (
    DOMAIN,
    SERVICE_EXTEND_TIME,
    SERVICE_RESET_PERSON,
    SERVICE_SUSPEND_TODAY,
)

from .conftest import build_entry_data


async def test_setup_and_unload(hass):
    """The integration sets up entities and services and unloads cleanly."""
    entry = MockConfigEntry(domain=DOMAIN, data=build_entry_data(name="Luke"))
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert hass.states.get("sensor.media_time_luke_remaining") is not None
    assert hass.states.get("switch.media_time_luke_suspend_today") is not None
    assert hass.states.get("number.media_time_luke_extend") is not None
    assert hass.states.get("button.media_time_luke_extend_15") is not None

    for service in (SERVICE_EXTEND_TIME, SERVICE_SUSPEND_TODAY, SERVICE_RESET_PERSON):
        assert hass.services.has_service(DOMAIN, service)

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.entry_id not in hass.data.get(DOMAIN, {})
