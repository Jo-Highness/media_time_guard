# Media Time Guard — Technical Documentation

This document describes the internal architecture of the `media_time_guard` custom
integration. It targets developers and advanced users. The end-user guide lives in
[`user/`](user).

## 1. Goal

Limit and **enforce** the daily media (listening) time of a person across one or more
`media_player` entities. Enforcement must survive children actively trying to bypass it:
power-cycling speakers, restarting Home Assistant, "unavailable" phases, etc.

## 2. Component overview

```
custom_components/media_time_guard/
├── __init__.py        # setup/unload, service registration
├── manifest.json      # integration metadata (config_flow, iot_class=calculated)
├── const.py           # keys, defaults, timings
├── config_flow.py     # 4-step config flow + mirrored options flow
├── coordinator.py     # PersonGuard: ALL runtime logic (the heart)
├── entity.py          # shared CoordinatorEntity base + DeviceInfo
├── sensor.py          # sensor.media_time_<person>_remaining
├── switch.py          # switch.media_time_<person>_suspend_today
├── number.py          # number.media_time_<person>_extend (absolute extra minutes)
├── button.py          # button.media_time_<person>_extend_15 / _extend_30
├── services.yaml      # service descriptions + selectors
├── strings.json       # base (English) UI strings
└── translations/      # de, en, es, fr, nb, el, ja
```

**One config entry == one person.** Multiple people = multiple entries. Each entry owns one
`PersonGuard` (a `DataUpdateCoordinator[dict]`) plus its entities, grouped under one device.

## 3. PersonGuard runtime state

Persisted (via `homeassistant.helpers.storage.Store`, key `media_time_guard.<entry_id>`):

| field | meaning |
|---|---|
| `media_date` | the current "media day" (ISO date) |
| `accumulated_seconds` | wall-clock seconds spent in `playing` today |
| `is_locked` | budget exhausted, enforcement active |
| `is_suspended` | enforcement suspended for today |
| `warned_today` | low-time warning already emitted |
| `extra_minutes` | extra budget granted today |
| `last_reset` | UTC ISO timestamp of the last reset |

Transient:

| field | meaning |
|---|---|
| `_active` | at least one assigned player is currently `playing` |
| `_checkpoint` | UTC timestamp from which un-accounted play time is measured |

## 4. Time accounting (wall-clock, no double counting)

Counting is **wall-clock time during which at least one** assigned player is `playing`.
Simultaneous playback on several speakers is **not** double counted — `_active` is a single
boolean for the person.

Three redundant drivers update the state, all funnelling through `_collect(now)` while holding
a per-person `asyncio.Lock`:

1. **`async_track_state_change_event`** on every assigned player → `_async_event_refresh`.
   Reacts instantly to start/stop and to the player re-appearing.
2. **`DataUpdateCoordinator` poll** every `POLL_INTERVAL` (20 s) → `_async_update_data`.
   Advances accumulation incrementally (keeps the sensor live) and is a redundant backup that
   re-stops a player if an event was ever missed.
3. **`async_track_time_change`** at the reset time → `_async_reset_refresh`.

`_tick(now)`:

1. Compute the media day for `now`. If it differs from `media_date`, the reset boundary was
   crossed while running → `_do_reset` (the small pre-boundary fragment is discarded).
2. Otherwise, if `_active` with a `_checkpoint`, add `now - checkpoint` to `accumulated_seconds`
   and move the checkpoint to `now` (checkpointing prevents double counting).
3. Recompute `_active` from the live player states; (re)arm or clear `_checkpoint`.

Only the literal state `playing` counts. `paused`, `idle`, `buffering`, `off`, `unavailable`
do **not** — so a Sonos rebooting or going unavailable never accrues time and resumes
correctly afterwards.

## 5. Enforcement (`_enforce`, tamper resistance)

After every `_tick`:

- If **not suspended** and (`effective_budget <= 0` **or** `used >= effective_budget`) →
  set `is_locked = True`. `effective_budget = (weekday_budget + extra_minutes) * 60`.
  A weekday budget of `0` therefore locks immediately at first play.
- While `is_locked` and not suspended, **all currently playing assigned players are stopped**
  (`media_player.media_stop`).

Because enforcement runs on *every* state-change event **and** on the periodic poll:

- Turning a speaker off does **not** reset `used` (it just stops counting).
- `is_locked` is persisted, so it survives power cycles, `unavailable` phases and HA restarts.
- A locked speaker that is switched off and on again and starts playing is **immediately
  re-stopped** — the event listener fires, and the poll is a backup.

The lock is only released by: the daily reset, `extend_time`/setting extra minutes such that
`used < new effective budget`, or `suspend_today = True`.

## 6. Warning (`_maybe_warn`)

When `warning_enabled`, not locked, not suspended, `not warned_today`, a player is playing and
`0 < remaining <= threshold`: emit the warning **once** and set `warned_today = True`.

- **TTS:** `tts.speak` with the configured TTS entity, the playing players as
  `media_player_entity_id`, and the message template formatted with `{minutes}`.
- **Media:** `media_player.play_media` with the configured `media_content_id` / type on the
  playing players.

## 7. Reset (`_do_reset`)

At the configured reset time (default `00:00`) `async_track_time_change` zeroes
`accumulated_seconds`, clears `is_locked`, `warned_today`, `is_suspended`, sets
`extra_minutes = 0`, records `last_reset`, and selects the new weekday budget.

**Downtime across the reset:** on startup `_async_restore` compares the stored `media_date`
with the current media day (`_current_media_date`, honouring the reset time). If they differ
the day is reset; if they match, full state is restored and — if a player is already playing —
counting resumes on the first evaluation.

## 8. Concurrency

Every mutating path (`_async_update_data`, event refresh, reset, `extend_time`,
`set_extra_minutes`, `set_suspended`, `reset_person`) runs inside the per-person
`asyncio.Lock`, eliminating races between the event listener, the poll and the reset. Service
calls issued from the synchronous `_collect` path are scheduled via `hass.async_create_task`
with `blocking=False`.

## 9. Validation

- `manifest.json`: `config_flow: true`, `iot_class: "calculated"`,
  `integration_type: "service"`, `after_dependencies: ["media_player", "tts"]`.
- Player-uniqueness across entries is validated in both the config flow (`async_step_user`) and
  the options flow (`async_step_init`).
- Translations cover all config/options steps, errors, the `warning_method` selector and the
  services. Norwegian uses the canonical HA code `nb` (Bokmål).
