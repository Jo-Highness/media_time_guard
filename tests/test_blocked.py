"""Tests for the permanent per-person block (``is_blocked``, v1.3.0)."""

from __future__ import annotations

from freezegun import freeze_time
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.storage import Store
import pytest
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_mock_service,
)
from pytest_homeassistant_custom_component.components.diagnostics import (
    get_diagnostics_for_config_entry,
)
import voluptuous as vol

from custom_components.media_time_guard.const import (
    DOMAIN,
    SERVICE_SET_BLOCKED,
    STORAGE_KEY_PREFIX,
    STORAGE_VERSION,
)
from custom_components.media_time_guard.coordinator import PersonGuard

from .conftest import PLAYER, build_entry_data, setup_person

BLOCKED_SWITCH = "switch.media_time_luke_blocked"


def _stored_state(**overrides) -> dict:
    """Return a persisted state for 2026-05-29, optionally overridden."""
    state = {
        "media_date": "2026-05-29",
        "accumulated_seconds": 120.0,
        "is_locked": False,
        "is_suspended": True,
        "warned_today": True,
        "extra_minutes": 15,
        "last_reset": "2026-05-29T00:00:00+00:00",
    }
    state.update(overrides)
    return state


async def _guard_from_store(hass, stored: dict | None) -> PersonGuard:
    """Create a guard whose store holds ``stored`` and restore it."""
    entry = MockConfigEntry(domain=DOMAIN, data=build_entry_data(budget_minutes=60))
    entry.add_to_hass(hass)
    if stored is not None:
        await Store(hass, STORAGE_VERSION, f"{STORAGE_KEY_PREFIX}{entry.entry_id}").async_save(
            stored
        )
    guard = PersonGuard(hass, entry)
    await guard._async_restore()
    return guard


# --- T1-T3: enforcement and precedence ------------------------------------


async def test_t1_block_stops_players_with_budget_left(hass, make_guard):
    """T1: a block stops a playing player although budget is left (event + poll)."""
    stop_calls = async_mock_service(hass, "media_player", "media_stop")
    with freeze_time("2026-05-29 10:00:00"):
        guard = await make_guard(budget_minutes=60)
        hass.states.async_set(PLAYER, "playing")
        await guard.async_refresh()
        await hass.async_block_till_done(wait_background_tasks=True)
        assert len(stop_calls) == 0

        await guard.async_set_blocked(True)
        await hass.async_block_till_done(wait_background_tasks=True)
        assert guard.data["is_blocked"] is True
        assert len(stop_calls) == 1
        assert stop_calls[0].data["entity_id"] == [PLAYER]

        # State event (speaker started again) -> stopped again.
        await guard._async_event_refresh()
        await hass.async_block_till_done(wait_background_tasks=True)
        assert len(stop_calls) == 2

        # Periodic poll as backup -> stopped again.
        await guard.async_refresh()
        await hass.async_block_till_done(wait_background_tasks=True)
        assert len(stop_calls) == 3

        # Not playing -> nothing to stop.
        hass.states.async_set(PLAYER, "idle")
        await guard.async_refresh()
        await hass.async_block_till_done(wait_background_tasks=True)
        assert len(stop_calls) == 3


async def test_t2_block_beats_suspend(hass, make_guard):
    """T2: a block stops players even while enforcement is suspended for today."""
    stop_calls = async_mock_service(hass, "media_player", "media_stop")
    with freeze_time("2026-05-29 10:00:00"):
        guard = await make_guard(budget_minutes=60)
        await guard.async_set_suspended(True)
        await guard.async_set_blocked(True)
        hass.states.async_set(PLAYER, "playing")
        await guard.async_refresh()
        await hass.async_block_till_done(wait_background_tasks=True)
        assert guard.data["is_suspended"] is True
        assert len(stop_calls) >= 1


async def test_t3_block_beats_extra_minutes(hass, make_guard):
    """T3: extra minutes do not lift a block."""
    stop_calls = async_mock_service(hass, "media_player", "media_stop")
    with freeze_time("2026-05-29 10:00:00"):
        guard = await make_guard(budget_minutes=60)
        await guard.async_set_blocked(True)
        await guard.async_extend_time(30)
        hass.states.async_set(PLAYER, "playing")
        await guard.async_refresh()
        await hass.async_block_till_done(wait_background_tasks=True)
        assert guard.data["is_blocked"] is True
        assert guard.data["extra_minutes_today"] == 30
        assert len(stop_calls) >= 1


# --- T4-T7: counting, warning, is_locked ----------------------------------


async def test_t4_no_counting_while_blocked_and_no_backbilling(hass, make_guard):
    """T4: nothing accrues while blocked; after unblocking counting restarts fresh."""
    async_mock_service(hass, "media_player", "media_stop")
    with freeze_time("2026-05-29 10:00:00") as frozen:
        guard = await make_guard(budget_minutes=60)
        await guard.async_set_blocked(True)

        # The speaker keeps reporting "playing" (stop ignored) for 10 minutes.
        hass.states.async_set(PLAYER, "playing")
        await guard.async_refresh()
        frozen.move_to("2026-05-29 10:10:00")
        await guard.async_refresh()
        assert guard.data["used_minutes"] == 0.0
        assert guard.data["is_playing"] is True  # honest playing flag

        # Unblock while still playing: the blocked 10 minutes are not billed.
        await guard.async_set_blocked(False)
        assert guard.data["used_minutes"] == 0.0
        frozen.move_to("2026-05-29 10:12:00")
        await guard.async_refresh()
        assert guard.data["used_minutes"] == 2.0


async def test_t5_time_before_block_is_booked(hass, make_guard):
    """T5: playback up to the moment of blocking is counted (pre-tick)."""
    async_mock_service(hass, "media_player", "media_stop")
    with freeze_time("2026-05-29 10:00:00") as frozen:
        guard = await make_guard(budget_minutes=60)
        hass.states.async_set(PLAYER, "playing")
        await guard.async_refresh()
        frozen.move_to("2026-05-29 10:03:00")
        await guard.async_set_blocked(True)
        assert guard.data["used_minutes"] == 3.0
        frozen.move_to("2026-05-29 10:20:00")
        await guard.async_refresh()
        assert guard.data["used_minutes"] == 3.0


async def test_t6_no_warning_while_blocked(hass, make_guard):
    """T6: the low-time warning never fires during a block."""
    async_mock_service(hass, "media_player", "media_stop")
    tts_calls = async_mock_service(hass, "tts", "speak")
    with freeze_time("2026-05-29 10:00:00") as frozen:
        guard = await make_guard(budget_minutes=10, warning=True, warning_threshold=5)
        hass.states.async_set(PLAYER, "playing")
        await guard.async_refresh()
        frozen.move_to("2026-05-29 10:05:30")  # 4.5 min left: would warn now
        await guard.async_set_blocked(True)
        await guard.async_refresh()
        await hass.async_block_till_done(wait_background_tasks=True)
        assert guard.data["warned_today"] is False
        assert len(tts_calls) == 0


async def test_t7_block_does_not_touch_is_locked(hass, make_guard):
    """T7: is_locked keeps meaning 'budget exhausted'; locks after unblocking."""
    async_mock_service(hass, "media_player", "media_stop")
    with freeze_time("2026-05-29 10:00:00"):
        guard = await make_guard(budget_minutes=0)
        await guard.async_set_blocked(True)
        hass.states.async_set(PLAYER, "playing")
        await guard.async_refresh()
        assert guard.data["is_locked"] is False

        await guard.async_set_blocked(False)
        assert guard.data["is_blocked"] is False
        assert guard.data["is_locked"] is True


async def test_t7_existing_lock_kept_while_blocked(hass, make_guard):
    """T7: an existing budget lock is neither set nor cleared by the block."""
    async_mock_service(hass, "media_player", "media_stop")
    with freeze_time("2026-05-29 10:00:00") as frozen:
        guard = await make_guard(budget_minutes=1)
        hass.states.async_set(PLAYER, "playing")
        await guard.async_refresh()
        frozen.move_to("2026-05-29 10:01:00")
        await guard.async_refresh()
        assert guard.data["is_locked"] is True

        await guard.async_set_blocked(True)
        assert guard.data["is_locked"] is True
        await guard.async_set_blocked(False)
        assert guard.data["is_locked"] is True


# --- T8-T12: lifecycle and persistence ------------------------------------


async def test_t8_block_survives_daily_reset_and_rollover(hass, make_guard):
    """T8: neither the reset-time trigger nor a day rollover in _tick unblock."""
    async_mock_service(hass, "media_player", "media_stop")
    with freeze_time("2026-05-29 12:00:00") as frozen:
        guard = await make_guard(budget_minutes=60)
        await guard.async_set_blocked(True)

        await guard._async_reset_refresh()
        assert guard.data["is_blocked"] is True

        frozen.move_to("2026-05-30 12:00:00")  # next local media day
        await guard.async_refresh()
        assert guard._media_date.isoformat() == "2026-05-30"
        assert guard.data["is_blocked"] is True


async def test_t9_block_survives_reset_person(hass):
    """T9: reset_person clears the day but keeps the block."""
    hass.states.async_set(PLAYER, "idle")
    entry = await setup_person(hass, name="Luke")
    guard = entry.runtime_data
    await guard.async_set_blocked(True)
    await guard.async_extend_time(20)
    await guard.async_reset_person()
    assert guard.data["is_blocked"] is True
    assert guard.data["extra_minutes_today"] == 0


async def test_t10_restore_same_day(hass):
    """T10: a stored block is restored on the same media day."""
    with freeze_time("2026-05-29 12:00:00"):
        guard = await _guard_from_store(hass, _stored_state(is_blocked=True))
        assert guard._is_blocked is True
        assert guard._accumulated_seconds == 120.0


async def test_t11_restore_across_day_boundary(hass):
    """T11: a restart across the reset boundary resets the day, not the block."""
    with freeze_time("2026-05-30 12:00:00"):
        guard = await _guard_from_store(hass, _stored_state(is_blocked=True))
        assert guard._is_blocked is True
        assert guard._accumulated_seconds == 0.0
        assert guard._is_suspended is False
        assert guard._extra_minutes == 0


async def test_t12_old_store_without_key(hass):
    """T12: a <= 1.2.x store (no is_blocked key) and an empty store load unblocked."""
    with freeze_time("2026-05-29 12:00:00"):
        guard = await _guard_from_store(hass, _stored_state())
        assert guard._is_blocked is False
        assert guard._accumulated_seconds == 120.0

        fresh = await _guard_from_store(hass, None)
        assert fresh._is_blocked is False


async def test_t13_block_saved_immediately(hass, hass_storage, make_guard):
    """T13: set_blocked writes the store at once, not only via delayed save."""
    with freeze_time("2026-05-29 10:00:00"):
        guard = await make_guard(budget_minutes=60)
        key = f"{STORAGE_KEY_PREFIX}{guard.entry.entry_id}"
        await guard.async_set_blocked(True)
        assert hass_storage[key]["data"]["is_blocked"] is True
        await guard.async_set_blocked(True)  # idempotent
        assert guard.data["is_blocked"] is True
        await guard.async_set_blocked(False)
        assert hass_storage[key]["data"]["is_blocked"] is False


async def test_t14_normal_logic_after_unblock(hass, make_guard):
    """T14: after unblocking, suspend and extra minutes of the day apply again."""
    stop_calls = async_mock_service(hass, "media_player", "media_stop")
    with freeze_time("2026-05-29 10:00:00"):
        guard = await make_guard(budget_minutes=0)
        await guard.async_set_blocked(True)
        await guard.async_extend_time(10)
        await guard.async_set_blocked(False)
        hass.states.async_set(PLAYER, "playing")
        await guard.async_refresh()
        await hass.async_block_till_done(wait_background_tasks=True)
        # 0 + 10 extra minutes -> not locked, nothing stopped.
        assert guard.data["is_locked"] is False
        assert len(stop_calls) == 0

        await guard.async_set_suspended(True)
        await guard.async_set_extra_minutes(0)
        await guard.async_refresh()
        await hass.async_block_till_done(wait_background_tasks=True)
        # Budget 0 but suspended -> still not enforced.
        assert len(stop_calls) == 0


# --- T15-T17: entities, service, attributes -------------------------------


async def test_t15_blocked_switch(hass):
    """T15: switch entity id, unique id, name and on/off wiring."""
    hass.states.async_set(PLAYER, "idle")
    entry = await setup_person(hass, name="Luke")
    guard = entry.runtime_data

    state = hass.states.get(BLOCKED_SWITCH)
    assert state is not None
    assert state.state == "off"
    assert state.name == "Luke Blocked"
    reg_entry = er.async_get(hass).async_get(BLOCKED_SWITCH)
    assert reg_entry.unique_id == f"{entry.entry_id}_blocked"
    # Existing entity ids are unchanged.
    for entity_id in (
        "switch.media_time_luke_suspend_today",
        "sensor.media_time_luke_remaining",
        "number.media_time_luke_extend",
        "button.media_time_luke_extend_15",
    ):
        assert hass.states.get(entity_id) is not None

    await hass.services.async_call(
        "switch", "turn_on", {"entity_id": BLOCKED_SWITCH}, blocking=True
    )
    assert guard.data["is_blocked"] is True
    assert hass.states.get(BLOCKED_SWITCH).state == "on"
    await hass.services.async_call(
        "switch", "turn_off", {"entity_id": BLOCKED_SWITCH}, blocking=True
    )
    assert guard.data["is_blocked"] is False
    assert hass.states.get(BLOCKED_SWITCH).state == "off"


async def test_t16_set_blocked_service(hass):
    """T16: set_blocked by person or config entry, with validation."""
    from homeassistant.setup import async_setup_component

    assert await async_setup_component(hass, DOMAIN, {})
    assert hass.services.has_service(DOMAIN, SERVICE_SET_BLOCKED)

    hass.states.async_set(PLAYER, "idle")
    entry = await setup_person(hass, name="Luke")
    await hass.services.async_call(
        DOMAIN, SERVICE_SET_BLOCKED, {"person": "luke", "blocked": True}, blocking=True
    )
    assert entry.runtime_data.data["is_blocked"] is True
    assert hass.states.get(BLOCKED_SWITCH).state == "on"

    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_BLOCKED,
        {"config_entry_id": entry.entry_id, "blocked": "off"},
        blocking=True,
    )
    assert entry.runtime_data.data["is_blocked"] is False

    with pytest.raises(ServiceValidationError) as err:
        await hass.services.async_call(
            DOMAIN, SERVICE_SET_BLOCKED, {"person": "Nobody", "blocked": True}, blocking=True
        )
    assert err.value.translation_key == "person_not_found"

    with pytest.raises(vol.Invalid):
        await hass.services.async_call(
            DOMAIN, SERVICE_SET_BLOCKED, {"person": "Luke"}, blocking=True
        )
    with pytest.raises(vol.Invalid):
        await hass.services.async_call(
            DOMAIN, SERVICE_SET_BLOCKED, {"blocked": True}, blocking=True
        )


async def test_t17_attributes_diagnostics_and_reload(hass, hass_client):
    """T17: is_blocked in sensor attributes and diagnostics; survives a reload."""
    async_mock_service(hass, "media_player", "media_stop")
    hass.states.async_set(PLAYER, "idle")
    entry = await setup_person(hass, name="Luke")
    assert hass.states.get("sensor.media_time_luke_remaining").attributes["is_blocked"] is False

    await entry.runtime_data.async_set_blocked(True)
    assert hass.states.get("sensor.media_time_luke_remaining").attributes["is_blocked"] is True
    diag = await get_diagnostics_for_config_entry(hass, hass_client, entry)
    assert diag["state"]["is_blocked"] is True

    # Options change -> entry reload -> block restored from the store.
    hass.config_entries.async_update_entry(entry, options=build_entry_data(budget_minutes=30))
    await hass.async_block_till_done(wait_background_tasks=True)
    assert entry.runtime_data.data["is_blocked"] is True
    assert hass.states.get(BLOCKED_SWITCH).state == "on"
