"""Tests for the PersonGuard coordinator logic."""

from __future__ import annotations

from freezegun import freeze_time
from homeassistant.exceptions import HomeAssistantError
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_mock_service,
)

from custom_components.media_time_guard.const import (
    CONF_TTS_MESSAGE,
    CONF_WARNING_MEDIA_ID,
    CONF_WARNING_METHOD,
    DOMAIN,
    STORAGE_KEY_PREFIX,
    STORAGE_VERSION,
    WARNING_METHOD_MEDIA,
    default_tts_message,
)
from custom_components.media_time_guard.coordinator import PersonGuard

from .conftest import PLAYER, build_entry_data, setup_person


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
        await hass.async_block_till_done(wait_background_tasks=True)

        assert guard.data["is_locked"] is True
        assert len(stop_calls) >= 1
        first = len(stop_calls)

        # Power cycle: turn the speaker off then on again -> instant re-stop.
        hass.states.async_set(PLAYER, "off")
        await guard._async_event_refresh()
        hass.states.async_set(PLAYER, "playing")
        await guard._async_event_refresh()
        await hass.async_block_till_done(wait_background_tasks=True)

        assert guard.data["is_locked"] is True
        assert len(stop_calls) > first


async def test_budget_zero_locks_immediately(hass, make_guard):
    """A weekday budget of 0 locks at first play."""
    stop_calls = async_mock_service(hass, "media_player", "media_stop")
    with freeze_time("2026-05-29 10:00:00"):
        guard = await make_guard(budget_minutes=0)
        hass.states.async_set(PLAYER, "playing")
        await guard.async_refresh()
        await hass.async_block_till_done(wait_background_tasks=True)
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
        await hass.async_block_till_done(wait_background_tasks=True)

        assert guard.data["is_suspended"] is True
        assert guard.data["is_locked"] is False
        assert len(stop_calls) == 0


async def test_persistence_restore_same_day(hass):
    """State is restored from storage within the same media day."""
    entry = MockConfigEntry(domain=DOMAIN, data=build_entry_data(budget_minutes=60))
    entry.add_to_hass(hass)
    key = f"{STORAGE_KEY_PREFIX}{entry.entry_id}"
    with freeze_time("2026-05-29 12:00:00"):
        # Inject persisted state for "today".
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
        await hass.async_block_till_done(wait_background_tasks=True)

        assert guard.data["warned_today"] is True
        assert len(tts_calls) == 1
        assert "Minuten" in tts_calls[0].data["message"]

        # Stays at one warning even as more time passes.
        frozen.move_to("2026-05-29 10:06:30")
        await guard.async_refresh()
        await hass.async_block_till_done(wait_background_tasks=True)
        assert len(tts_calls) == 1


async def test_lock_lifted_after_budget_increase_on_restore(hass):
    """A stored lock is lifted when the (new) budget is no longer exhausted."""
    async_mock_service(hass, "media_player", "media_stop")
    entry = MockConfigEntry(domain=DOMAIN, data=build_entry_data(budget_minutes=60))
    entry.add_to_hass(hass)
    with freeze_time("2026-05-29 12:00:00"):
        from homeassistant.helpers.storage import Store

        await Store(hass, STORAGE_VERSION, f"{STORAGE_KEY_PREFIX}{entry.entry_id}").async_save(
            {
                "media_date": "2026-05-29",
                "accumulated_seconds": 120.0,  # 2 of now 60 minutes used
                "is_locked": True,  # locked under the old, smaller budget
                "is_suspended": False,
                "warned_today": False,
                "extra_minutes": 0,
                "last_reset": "2026-05-29T00:00:00+00:00",
            }
        )
        guard = PersonGuard(hass, entry)
        await guard._async_restore()
        await guard.async_refresh()
        assert guard.data["is_locked"] is False
        assert guard.data["remaining_minutes"] == 58.0


async def test_lock_lifted_after_budget_increase_via_options(hass):
    """Raising the weekday budget in the options unlocks after the reload."""
    async_mock_service(hass, "media_player", "media_stop")
    with freeze_time("2026-05-29 10:00:00") as frozen:
        hass.states.async_set(PLAYER, "playing")
        entry = await setup_person(hass, budget_minutes=1)
        frozen.move_to("2026-05-29 10:01:00")
        await entry.runtime_data.async_refresh()
        assert entry.runtime_data.data["is_locked"] is True

        hass.states.async_set(PLAYER, "idle")
        hass.config_entries.async_update_entry(entry, options=build_entry_data(budget_minutes=30))
        await hass.async_block_till_done(wait_background_tasks=True)
        assert entry.runtime_data.data["is_locked"] is False
        assert entry.runtime_data.data["remaining_minutes"] == 29.0


async def test_lock_kept_when_budget_still_exhausted(hass, make_guard):
    """Re-evaluation does not unlock while the budget is still used up."""
    async_mock_service(hass, "media_player", "media_stop")
    with freeze_time("2026-05-29 10:00:00") as frozen:
        guard = await make_guard(budget_minutes=1)
        hass.states.async_set(PLAYER, "playing")
        await guard.async_refresh()
        frozen.move_to("2026-05-29 10:02:00")
        await guard.async_refresh()
        hass.states.async_set(PLAYER, "idle")
        await guard.async_refresh()
        assert guard.data["is_locked"] is True
        await guard.async_set_extra_minutes(0)
        assert guard.data["is_locked"] is True


async def test_warning_rearmed_after_extension(hass, make_guard):
    """After extra minutes push remaining time above the threshold, warn again."""
    tts_calls = async_mock_service(hass, "tts", "speak")
    with freeze_time("2026-05-29 10:00:00") as frozen:
        guard = await make_guard(budget_minutes=10, warning=True, warning_threshold=5)
        hass.states.async_set(PLAYER, "playing")
        await guard.async_refresh()
        frozen.move_to("2026-05-29 10:05:30")
        await guard.async_refresh()
        await hass.async_block_till_done(wait_background_tasks=True)
        assert len(tts_calls) == 1

        await guard.async_extend_time(15)  # 19.5 min left -> re-armed
        assert guard.data["warned_today"] is False

        frozen.move_to("2026-05-29 10:20:30")  # 4.5 min left again
        await guard.async_refresh()
        await hass.async_block_till_done(wait_background_tasks=True)
        assert guard.data["warned_today"] is True
        assert len(tts_calls) == 2


async def test_small_extension_does_not_rearm(hass, make_guard):
    """An extension that stays below the threshold does not warn twice."""
    tts_calls = async_mock_service(hass, "tts", "speak")
    with freeze_time("2026-05-29 10:00:00") as frozen:
        guard = await make_guard(budget_minutes=10, warning=True, warning_threshold=5)
        hass.states.async_set(PLAYER, "playing")
        await guard.async_refresh()
        frozen.move_to("2026-05-29 10:07:00")  # 3 min left
        await guard.async_refresh()
        await guard.async_extend_time(1)  # 4 min left, still below 5
        await hass.async_block_till_done(wait_background_tasks=True)
        assert guard.data["warned_today"] is True
        assert len(tts_calls) == 1


async def test_media_warning_plays_content(hass):
    """The media warning method calls media_player.play_media."""
    play_calls = async_mock_service(hass, "media_player", "play_media")
    data = build_entry_data(budget_minutes=10, warning=True, warning_threshold=5)
    data.update(
        {
            CONF_WARNING_METHOD: WARNING_METHOD_MEDIA,
            CONF_WARNING_MEDIA_ID: "media-source://media_source/local/bell.mp3",
        }
    )
    entry = MockConfigEntry(domain=DOMAIN, data=data)
    entry.add_to_hass(hass)
    with freeze_time("2026-05-29 10:00:00") as frozen:
        guard = PersonGuard(hass, entry)
        await guard._async_restore()
        hass.states.async_set(PLAYER, "playing")
        await guard.async_refresh()
        frozen.move_to("2026-05-29 10:06:00")
        await guard.async_refresh()
        await hass.async_block_till_done(wait_background_tasks=True)

    assert len(play_calls) == 1
    call = play_calls[0].data
    assert call["entity_id"] == [PLAYER]
    assert call["media_content_id"] == "media-source://media_source/local/bell.mp3"
    assert call["media_content_type"] == "music"


async def test_default_tts_message_uses_ui_language(hass):
    """Without a configured text the announcement uses the HA UI language."""
    tts_calls = async_mock_service(hass, "tts", "speak")
    hass.config.language = "en"
    data = build_entry_data(budget_minutes=10, warning=True, warning_threshold=5)
    data.pop(CONF_TTS_MESSAGE)
    entry = MockConfigEntry(domain=DOMAIN, data=data)
    entry.add_to_hass(hass)
    with freeze_time("2026-05-29 10:00:00") as frozen:
        guard = PersonGuard(hass, entry)
        await guard._async_restore()
        hass.states.async_set(PLAYER, "playing")
        await guard.async_refresh()
        frozen.move_to("2026-05-29 10:06:00")
        await guard.async_refresh()
        await hass.async_block_till_done(wait_background_tasks=True)

    assert tts_calls[0].data["message"] == default_tts_message("en").format(minutes=4)
    assert default_tts_message("de-CH").startswith("Achtung")
    assert default_tts_message("no") == default_tts_message("nb")
    assert default_tts_message("xx") == default_tts_message("en")


async def test_failed_stop_call_is_logged(hass, make_guard, caplog):
    """A failing media_stop is logged instead of raising in a stray task."""

    async def _fail(call):
        raise HomeAssistantError("speaker offline")

    hass.services.async_register("media_player", "media_stop", _fail)
    with freeze_time("2026-05-29 10:00:00"):
        guard = await make_guard(budget_minutes=0)
        hass.states.async_set(PLAYER, "playing")
        await guard.async_refresh()
        await hass.async_block_till_done(wait_background_tasks=True)

    assert guard.data["is_locked"] is True
    assert "speaker offline" in caplog.text


async def test_only_playing_state_counts(hass, make_guard):
    """buffering / on / paused do not count as media time."""
    with freeze_time("2026-05-29 10:00:00") as frozen:
        guard = await make_guard(budget_minutes=60)
        for minute, state in enumerate(("buffering", "on", "paused", "idle"), start=1):
            hass.states.async_set(PLAYER, state)
            await guard.async_refresh()
            frozen.move_to(f"2026-05-29 10:0{minute}:00")
            await guard.async_refresh()
        assert guard.data["used_minutes"] == 0.0
