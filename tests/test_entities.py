"""Tests for the entities, repairs and diagnostics."""

from __future__ import annotations

from unittest.mock import patch

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import ATTR_DEVICE_CLASS, ATTR_UNIT_OF_MEASUREMENT
from homeassistant.helpers import device_registry as dr, issue_registry as ir
from pytest_homeassistant_custom_component.components.diagnostics import (
    get_diagnostics_for_config_entry,
)

from custom_components.media_time_guard.const import DOMAIN
from custom_components.media_time_guard.coordinator import (
    PersonGuard,
    missing_entities_issue_id,
)

from .conftest import PLAYER, setup_person


async def test_sensor_state_and_attributes(hass):
    """The remaining sensor is a duration in minutes with rich attributes."""
    hass.states.async_set(PLAYER, "idle")
    await setup_person(hass, name="Luke", budget_minutes=45)
    state = hass.states.get("sensor.media_time_luke_remaining")
    assert float(state.state) == 45.0
    assert state.attributes[ATTR_DEVICE_CLASS] == SensorDeviceClass.DURATION
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == "min"
    assert state.attributes["budget_minutes"] == 45
    assert state.attributes["is_locked"] is False
    assert state.attributes["players"] == [PLAYER]


async def test_number_button_switch(hass):
    """Number, buttons and switch drive the guard."""
    hass.states.async_set(PLAYER, "idle")
    entry = await setup_person(hass, name="Luke", budget_minutes=45)
    guard = entry.runtime_data

    await hass.services.async_call(
        "number",
        "set_value",
        {"entity_id": "number.media_time_luke_extend", "value": 20},
        blocking=True,
    )
    assert guard.data["extra_minutes_today"] == 20
    assert hass.states.get("number.media_time_luke_extend").state == "20"

    await hass.services.async_call(
        "button", "press", {"entity_id": "button.media_time_luke_extend_15"}, blocking=True
    )
    await hass.services.async_call(
        "button", "press", {"entity_id": "button.media_time_luke_extend_30"}, blocking=True
    )
    assert guard.data["extra_minutes_today"] == 65
    assert float(hass.states.get("sensor.media_time_luke_remaining").state) == 110.0

    await hass.services.async_call(
        "switch", "turn_on", {"entity_id": "switch.media_time_luke_suspend_today"}, blocking=True
    )
    assert guard.data["is_suspended"] is True
    await hass.services.async_call(
        "switch", "turn_off", {"entity_id": "switch.media_time_luke_suspend_today"}, blocking=True
    )
    assert guard.data["is_suspended"] is False


async def test_entity_names_and_device(hass):
    """Entities use translated names on a service device named after the person."""
    hass.states.async_set(PLAYER, "idle")
    entry = await setup_person(hass, name="Luke")
    assert hass.states.get("button.media_time_luke_extend_15").name == "Luke Add 15 min"
    assert hass.states.get("sensor.media_time_luke_remaining").name == "Luke Remaining time"
    devices = dr.async_entries_for_config_entry(dr.async_get(hass), entry.entry_id)
    assert len(devices) == 1
    device = devices[0]
    assert device.identifiers == {(DOMAIN, entry.entry_id)}
    assert device.name == "Luke"
    assert device.entry_type is dr.DeviceEntryType.SERVICE


async def test_unload_shuts_down_once(hass):
    """Unload runs the guard shutdown exactly once."""
    entry = await setup_person(hass, name="Luke")
    guard: PersonGuard = entry.runtime_data
    with patch.object(guard._store, "async_save") as save:
        assert await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()
    # The final flush happens in async_shutdown - once, not twice.
    assert save.call_count == 1


async def test_repair_issue_for_missing_player(hass):
    """A missing assigned player raises a repair issue that clears itself."""
    entry = await setup_person(hass, name="Luke")  # PLAYER has no state
    issue_id = missing_entities_issue_id(entry.entry_id)
    issue = ir.async_get(hass).async_get_issue(DOMAIN, issue_id)
    assert issue is not None
    assert issue.translation_key == "missing_entities"
    assert PLAYER in issue.translation_placeholders["entities"]

    hass.states.async_set(PLAYER, "idle")
    await entry.runtime_data.async_refresh()
    assert ir.async_get(hass).async_get_issue(DOMAIN, issue_id) is None


async def test_repair_issue_for_missing_tts_entity(hass):
    """A missing TTS engine is reported when the TTS warning is enabled."""
    hass.states.async_set(PLAYER, "idle")
    entry = await setup_person(hass, name="Luke", warning=True)
    issue = ir.async_get(hass).async_get_issue(DOMAIN, missing_entities_issue_id(entry.entry_id))
    assert issue is not None
    assert issue.translation_placeholders["entities"] == "tts.test_engine"

    await hass.config_entries.async_remove(entry.entry_id)
    await hass.async_block_till_done()
    assert (
        ir.async_get(hass).async_get_issue(DOMAIN, missing_entities_issue_id(entry.entry_id))
        is None
    )


async def test_no_repair_issue_when_all_present(hass):
    """No issue when every assigned entity exists."""
    hass.states.async_set(PLAYER, "idle")
    entry = await setup_person(hass, name="Luke")
    assert (
        ir.async_get(hass).async_get_issue(DOMAIN, missing_entities_issue_id(entry.entry_id))
        is None
    )


async def test_diagnostics_are_redacted(hass, hass_client):
    """Diagnostics contain no names, entity ids or texts."""
    hass.states.async_set(PLAYER, "playing")
    entry = await setup_person(hass, name="Luke")
    diag = await get_diagnostics_for_config_entry(hass, hass_client, entry)
    text = str(diag)
    assert "Luke" not in text
    assert "test_player" not in text
    assert "tts.test_engine" not in text
    assert diag["players"] == [{"index": 0, "state": "playing", "exists": True}]
    assert diag["state"]["budget_minutes"] == 60
