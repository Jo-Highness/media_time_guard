"""QA edge cases for the permanent per-person block (v1.3.0)."""

from __future__ import annotations

import asyncio
import logging

from freezegun import freeze_time
from homeassistant.core import ServiceCall
from homeassistant.exceptions import HomeAssistantError
from pytest_homeassistant_custom_component.common import async_mock_service

from .conftest import PLAYER, setup_person

PLAYER2 = "media_player.test_player_2"
PLAYER3 = "media_player.test_player_3"


async def test_e1_block_stops_all_playing_players_only(hass, make_guard):
    """E1: every playing player of the person is stopped, idle ones are left alone."""
    stop_calls = async_mock_service(hass, "media_player", "media_stop")
    with freeze_time("2026-05-29 10:00:00"):
        guard = await make_guard(budget_minutes=60, players=[PLAYER, PLAYER2, PLAYER3])
        hass.states.async_set(PLAYER, "playing")
        hass.states.async_set(PLAYER2, "idle")
        hass.states.async_set(PLAYER3, "playing")
        await guard.async_set_blocked(True)
        await hass.async_block_till_done(wait_background_tasks=True)
        assert len(stop_calls) == 1
        assert sorted(stop_calls[0].data["entity_id"]) == sorted([PLAYER, PLAYER3])


async def test_e2_real_state_event_stops_player(hass):
    """E2: the registered state listener (not a direct call) stops a player that starts."""
    stop_calls = async_mock_service(hass, "media_player", "media_stop")
    hass.states.async_set(PLAYER, "idle")
    entry = await setup_person(hass, name="Luke", budget_minutes=60)
    await entry.runtime_data.async_set_blocked(True)
    await hass.async_block_till_done(wait_background_tasks=True)
    assert len(stop_calls) == 0

    hass.states.async_set(PLAYER, "playing")
    await hass.async_block_till_done(wait_background_tasks=True)
    assert len(stop_calls) == 1
    assert stop_calls[0].data["entity_id"] == [PLAYER]
    assert entry.runtime_data.data["used_minutes"] == 0.0


async def test_e3_media_stop_failure_keeps_block_and_retries(hass, make_guard, caplog):
    """E3: a failing media_stop is logged, the block stays and the poll retries."""
    calls: list[ServiceCall] = []

    async def _failing_stop(call: ServiceCall) -> None:
        calls.append(call)
        raise HomeAssistantError("speaker offline")

    hass.services.async_register("media_player", "media_stop", _failing_stop)
    with freeze_time("2026-05-29 10:00:00"):
        guard = await make_guard(budget_minutes=60)
        hass.states.async_set(PLAYER, "playing")
        with caplog.at_level(logging.WARNING):
            await guard.async_set_blocked(True)
            await hass.async_block_till_done(wait_background_tasks=True)
        assert guard.data["is_blocked"] is True
        assert len(calls) == 1
        assert "speaker offline" in caplog.text

        await guard.async_refresh()
        await hass.async_block_till_done(wait_background_tasks=True)
        assert guard.last_update_success is True
        assert guard.data["is_blocked"] is True
        assert len(calls) == 2


async def test_e4_unblock_with_exhausted_budget_locks_and_stops(hass, make_guard):
    """E4: unblocking a player whose budget is used up locks and stops at once."""
    stop_calls = async_mock_service(hass, "media_player", "media_stop")
    with freeze_time("2026-05-29 10:00:00") as frozen:
        guard = await make_guard(budget_minutes=5)
        hass.states.async_set(PLAYER, "playing")
        await guard.async_refresh()
        frozen.move_to("2026-05-29 10:04:00")
        await guard.async_set_blocked(True)  # 4 of 5 min booked
        await hass.async_block_till_done(wait_background_tasks=True)
        assert guard.data["used_minutes"] == 4.0
        assert guard.data["is_locked"] is False

        frozen.move_to("2026-05-29 11:00:00")
        await guard.async_set_blocked(False)
        await hass.async_block_till_done(wait_background_tasks=True)
        # Still 1 minute left: counting restarts now, no lock yet.
        assert guard.data["used_minutes"] == 4.0
        assert guard.data["is_locked"] is False
        stops_before = len(stop_calls)

        frozen.move_to("2026-05-29 11:01:00")
        await guard.async_refresh()
        await hass.async_block_till_done(wait_background_tasks=True)
        assert guard.data["is_locked"] is True
        assert guard.data["is_blocked"] is False
        assert len(stop_calls) == stops_before + 1


async def test_e5_block_over_midnight_then_unblock_fresh_day(hass, make_guard):
    """E5: blocked over the day boundary; after unblocking the new day starts clean."""
    async_mock_service(hass, "media_player", "media_stop")
    # Times are UTC; the HA test time zone is US/Pacific (UTC-7 in May), so
    # 06:50 UTC = 23:50 local and 07:05 UTC = 00:05 local on the next day.
    with freeze_time("2026-05-30 06:50:00") as frozen:
        guard = await make_guard(budget_minutes=10)
        hass.states.async_set(PLAYER, "playing")
        await guard.async_refresh()
        frozen.move_to("2026-05-30 06:59:00")
        await guard.async_refresh()
        assert guard.data["is_locked"] is False
        await guard.async_set_suspended(True)
        await guard.async_extend_time(15)
        await guard.async_set_blocked(True)

        frozen.move_to("2026-05-30 07:05:00")  # local midnight passed while blocked + playing
        await guard.async_refresh()
        assert guard._media_date.isoformat() == "2026-05-30"
        assert guard.data["is_blocked"] is True
        assert guard.data["is_suspended"] is False
        assert guard.data["extra_minutes_today"] == 0
        assert guard.data["used_minutes"] == 0.0

        frozen.move_to("2026-05-30 15:00:00")
        await guard.async_set_blocked(False)
        frozen.move_to("2026-05-30 15:03:00")
        await guard.async_refresh()
        assert guard.data["used_minutes"] == 3.0
        assert guard.data["is_locked"] is False


async def test_e6_concurrent_block_and_state_events(hass, make_guard):
    """E6: block racing with state-event refreshes ends consistently blocked, nothing billed."""
    stop_calls = async_mock_service(hass, "media_player", "media_stop")
    with freeze_time("2026-05-29 10:00:00") as frozen:
        guard = await make_guard(budget_minutes=60)
        hass.states.async_set(PLAYER, "playing")
        await guard.async_refresh()
        frozen.move_to("2026-05-29 10:02:00")
        await asyncio.gather(
            guard._async_event_refresh(),
            guard.async_set_blocked(True),
            guard._async_event_refresh(),
            guard._async_event_refresh(),
        )
        await hass.async_block_till_done(wait_background_tasks=True)
        assert guard.data["is_blocked"] is True
        assert guard.data["used_minutes"] == 2.0
        assert len(stop_calls) >= 1

        frozen.move_to("2026-05-29 10:30:00")
        await asyncio.gather(guard._async_event_refresh(), guard.async_refresh())
        assert guard.data["used_minutes"] == 2.0
