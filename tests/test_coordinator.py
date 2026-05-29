"""Tests for the PersonGuard coordinator logic."""

from __future__ import annotations

from freezegun import freeze_time
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_mock_service,
)

from custom_components.media_time_guard.const import (
    DOMAIN,
    STORAGE_KEY_PREFIX,
    STORAGE_VERSION,
)
from custom_components.media_time_guard.coordinator import PersonGuard

from .conftest import PLAYER, build_entry_data


async def test_time_accumulation_only_while_playing(hass, make_guard):
    """Wall-clock time accrues only while a player is 'playing'."""
    with freeze_time("2026-05-29 10:00:00") as frozen:
        guard = await make_guard(budget_minutes=60)

        # idle -> no accumulation
        hass.states.async_set(PLAYER, "idle")
        await guard.async_refresh()
        frozen.move_to("2026-05-29 10:01:00")
        await guard.async_refresh()
        assert guard.data["used_minutes"] == 0.0

        # playing -> accumulate 2 minutes
        hass.states.async_set(PLAYER, "playing")
        await guard.async_refresh()
        frozen.move_to("2026-05-29 10:03:00")
        await guard.async_refresh()
        assert guard.data["used_minutes"] == 2.0
        assert guard.data["is_playing"] is True

        # paused -> stop accumulating
        hass.states.async_set(PLAYER, "paused")
        await guard.async_refresh()
        frozen.move_to("2026-05-29 10:10:00")
        await guard.async_refresh()
        assert guard.data["used_minutes"] == 2.0
        assert guard.data["is_playing"] is False


async def test_no_double_count_two_players(hass):
    """Concurrent playback on two speakers counts as wall-clock time."""
    p1, p2 = "media_player.one", "media_player.two"
    with freeze_time("2026-05-29 10:00:00") as frozen:
        entry = MockConfigEntry(
            domain=DOMAIN, data=build_entry_data(players=[p1, p2], budget_minutes=60)
        )
        entry.add_to_hass(hass)
        guard = PersonGuard(hass, entry)
        await guard._async_restore()

        hass.states.async_set(p1, "playing")
        hass.states.async_set(p2, "playing")
        await guard.async_refresh()
        frozen.move_to("2026-05-29 10:02:00")
        await guard.async_refresh()
        # 2 wall-clock minutes, not 4
        assert guard.data["used_minutes"] == 2.0


async def test_lock_stops_players_and_survives_power_cycle(hass, make_guard):
    """Budget exhaustion locks and re-stops players across a power cycle."""
    stop_calls = async_mock_service(hass, "media_player", "media_stop")
    with freeze_time("2026-05-29 10:00:00") as frozen:
        guard = await make_guard(budget_minutes=1)  # 60 s budget

        hass.states.async_set(PLAYER, "playing")
        await guard.async_refresh()
        frozen.move_to("2026-05-29 10:01:00")
        await guard.async_refresh()
        await hass.async_block_till_done()

        assert guard.data["is_locked"] is True
        assert len(stop_calls) >= 1
        first = len(stop_calls)

        # Power cycle: turn the speaker off then on again -> instant re-stop.
        hass.states.async_set(PLAYER, "off")
        await guard._async_event_refresh()
        hass.states.async_set(PLAYER, "playing")
        await guard._async_event_refresh()
        await hass.async_block_till_done()

        assert guard.data["is_locked"] is True
        assert len(stop_calls) > first


async def test_budget_zero_locks_immediately(hass, make_guard):
    """A weekday budget of 0 locks at first play."""
    stop_calls = async_mock_service(hass, "media_player", "media_stop")
    with freeze_time("2026-05-29 10:00:00"):
        guard = await make_guard(budget_minutes=0)
        hass.states.async_set(PLAYER, "playing")
        await guard.async_refresh()
        await hass.async_block_till_done()
        assert guard.data["is_locked"] is True
        assert len(stop_calls) >= 1


async def test_extend_unlocks(hass, make_guard):
    """Extending the budget releases an active lock."""
    async_mock_service(hass, "media_player", "media_stop")
    with freeze_time("2026-05-29 10:00:00") as frozen:
        guard = await make_guard(budget_minutes=1)
        hass.states.async_set(PLAYER, "playing")
        await guard.async_refresh()
        frozen.move_to("2026-05-29 10:01:00")
        await guard.async_refresh()
        assert guard.data["is_locked"] is True

        await guard.async_extend_time(10)
        assert guard.data["is_locked"] is False
        assert guard.data["extra_minutes_today"] == 10
        assert guard.data["remaining_minutes"] > 0


async def test_suspend_does_not_enforce(hass, make_guard):
    """While suspended the budget is not enforced."""
    stop_calls = async_mock_service(hass, "media_player", "media_stop")
    with freeze_time("2026-05-29 10:00:00") as frozen:
        guard = await make_guard(budget_minutes=1)
        await guard.async_set_suspended(True)

        hass.states.async_set(PLAYER, "playing")
        await guard.async_refresh()
        frozen.move_to("2026-05-29 10:05:00")
        await guard.async_refresh()
        await hass.async_block_till_done()

        assert guard.data["is_suspended"] is True
        assert guard.data["is_locked"] is False
        assert len(stop_calls) == 0


async def test_persistence_restore_same_day(hass):
    """State is restored from storage within the same media day."""
    entry = MockConfigEntry(domain=DOMAIN, data=build_entry_data(budget_minutes=60))
    entry.add_to_hass(hass)
    key = f"{STORAGE_KEY_PREFIX}{entry.entry_id}"
    with freeze_time("2026-05-29 12:00:00"):
        hass.data.setdefault("hass_storage", {})
        # Inject persisted state for "today".
        hass.config.set_time_zone("UTC")
        from homeassistant.helpers.storage import Store

        store = Store(hass, STORAGE_VERSION, key)
        await store.async_save(
            {
                "media_date": "2026-05-29",
                "accumulated_seconds": 120.0,
                "is_locked": True,
                "is_suspended": False,
                "warned_today": True,
                "extra_minutes": 15,
                "last_reset": "2026-05-29T00:00:00+00:00",
            }
        )

        guard = PersonGuard(hass, entry)
        await guard._async_restore()
        assert guard._accumulated_seconds == 120.0
        assert guard._is_locked is True
        assert guard._warned_today is True
        assert guard._extra_minutes == 15


async def test_persistence_resets_on_new_day(hass):
    """A stored state from a previous day is reset on restore."""
    entry = MockConfigEntry(domain=DOMAIN, data=build_entry_data(budget_minutes=60))
    entry.add_to_hass(hass)
    key = f"{STORAGE_KEY_PREFIX}{entry.entry_id}"
    with freeze_time("2026-05-29 12:00:00"):
        from homeassistant.helpers.storage import Store

        store = Store(hass, STORAGE_VERSION, key)
        await store.async_save(
            {
                "media_date": "2026-05-28",
                "accumulated_seconds": 999.0,
                "is_locked": True,
                "is_suspended": True,
                "warned_today": True,
                "extra_minutes": 30,
                "last_reset": "2026-05-28T00:00:00+00:00",
            }
        )

        guard = PersonGuard(hass, entry)
        await guard._async_restore()
        assert guard._accumulated_seconds == 0.0
        assert guard._is_locked is False
        assert guard._is_suspended is False
        assert guard._extra_minutes == 0


async def test_daily_reset(hass, make_guard):
    """The reset clears counters and the lock."""
    async_mock_service(hass, "media_player", "media_stop")
    with freeze_time("2026-05-29 10:00:00") as frozen:
        guard = await make_guard(budget_minutes=1)
        hass.states.async_set(PLAYER, "playing")
        await guard.async_refresh()
        frozen.move_to("2026-05-29 10:01:00")
        await guard.async_refresh()
        assert guard.data["is_locked"] is True

        hass.states.async_set(PLAYER, "idle")
        await guard._async_reset_refresh()
        assert guard.data["is_locked"] is False
        assert guard.data["used_minutes"] == 0.0
        assert guard.data["extra_minutes_today"] == 0


async def test_warning_emitted_once(hass, make_guard):
    """A single TTS warning fires when remaining time hits the threshold."""
    tts_calls = async_mock_service(hass, "tts", "speak")
    with freeze_time("2026-05-29 10:00:00") as frozen:
        guard = await make_guard(budget_minutes=10, warning=True, warning_threshold=5)
        hass.states.async_set(PLAYER, "playing")
        await guard.async_refresh()

        # 5.5 minutes in -> 4.5 min remaining (below the 5 min threshold).
        frozen.move_to("2026-05-29 10:05:30")
        await guard.async_refresh()
        await hass.async_block_till_done()

        assert guard.data["warned_today"] is True
        assert len(tts_calls) == 1
        assert "Minuten" in tts_calls[0].data["message"]

        # Stays at one warning even as more time passes.
        frozen.move_to("2026-05-29 10:06:30")
        await guard.async_refresh()
        await hass.async_block_till_done()
        assert len(tts_calls) == 1
