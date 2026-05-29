"""Central logic for Media Time Guard.

The :class:`PersonGuard` owns all runtime state for a single person:
time accumulation, lock enforcement, warnings, daily reset and persistence.

It is implemented as a :class:`DataUpdateCoordinator` so the entities can use
the lightweight ``CoordinatorEntity`` plumbing.  The coordinator is driven by
three redundant sources:

* ``async_track_state_change_event`` on every assigned media player – reacts
  instantly when a player starts/stops playing (and re-stops it while locked).
* ``DataUpdateCoordinator`` periodic poll (:data:`POLL_INTERVAL`) – keeps the
  sensor live, advances accumulation incrementally and acts as a backup that
  re-stops a player should an event ever be missed.
* ``async_track_time_change`` at the configured reset time – performs the
  precise daily reset.

All mutating paths run under a per-person ``asyncio.Lock`` to avoid races
between events, the poll and the reset.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import date, datetime, time, timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.event import (
    async_track_state_change_event,
    async_track_time_change,
)
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util, slugify

from .const import (
    ATTR_BUDGET_MINUTES,
    ATTR_EFFECTIVE_BUDGET_MINUTES,
    ATTR_EXTRA_MINUTES_TODAY,
    ATTR_IS_LOCKED,
    ATTR_IS_PLAYING,
    ATTR_IS_SUSPENDED,
    ATTR_LAST_RESET,
    ATTR_PLAYERS,
    ATTR_REMAINING_MINUTES,
    ATTR_USED_MINUTES,
    ATTR_WARNED_TODAY,
    ATTR_WEEKDAY,
    CONF_BUDGETS,
    CONF_NAME,
    CONF_PLAYERS,
    CONF_RESET_TIME,
    CONF_TTS_ENTITY,
    CONF_TTS_MESSAGE,
    CONF_WARNING_ENABLED,
    CONF_WARNING_MEDIA_ID,
    CONF_WARNING_MEDIA_TYPE,
    CONF_WARNING_METHOD,
    CONF_WARNING_THRESHOLD,
    DEFAULT_RESET_TIME,
    DEFAULT_TTS_MESSAGE,
    DEFAULT_WARNING_MEDIA_TYPE,
    DEFAULT_WARNING_THRESHOLD,
    DOMAIN,
    POLL_INTERVAL,
    STATE_PLAYING,
    STORAGE_KEY_PREFIX,
    STORAGE_VERSION,
    WARNING_METHOD_MEDIA,
    WARNING_METHOD_TTS,
)

_LOGGER = logging.getLogger(__name__)

MP_DOMAIN = "media_player"
SERVICE_MEDIA_STOP = "media_stop"
SERVICE_PLAY_MEDIA = "play_media"
ATTR_MEDIA_CONTENT_ID = "media_content_id"
ATTR_MEDIA_CONTENT_TYPE = "media_content_type"

TTS_DOMAIN = "tts"
SERVICE_TTS_SPEAK = "speak"
ATTR_MEDIA_PLAYER_ENTITY_ID = "media_player_entity_id"
ATTR_MESSAGE = "message"


def _parse_reset_time(value: str) -> time:
    """Parse a ``HH:MM[:SS]`` string into a :class:`datetime.time`."""
    try:
        parts = [int(p) for p in value.split(":")]
        while len(parts) < 3:
            parts.append(0)
        return time(parts[0], parts[1], parts[2])
    except (ValueError, IndexError):
        _LOGGER.warning("Invalid reset_time %r, falling back to midnight", value)
        return time(0, 0, 0)


class PersonGuard(DataUpdateCoordinator[dict]):
    """Track and enforce media time for a single person."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialise the guard for ``entry``."""
        self.entry = entry
        self._config = {**entry.data, **entry.options}
        name = self._config.get(CONF_NAME, entry.title or entry.entry_id)
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN} {name}",
            update_interval=POLL_INTERVAL,
        )
        self._store: Store = Store(
            hass, STORAGE_VERSION, f"{STORAGE_KEY_PREFIX}{entry.entry_id}"
        )
        self._lock = asyncio.Lock()
        self._unsubs: list = []

        # --- runtime state (persisted) ---
        self._media_date: date | None = None
        self._accumulated_seconds: float = 0.0
        self._is_locked: bool = False
        self._is_suspended: bool = False
        self._warned_today: bool = False
        self._extra_minutes: int = 0
        self._last_reset: str | None = None

        # --- runtime state (transient) ---
        self._active: bool = False
        self._checkpoint: datetime | None = None

    # ------------------------------------------------------------------
    # Config accessors
    # ------------------------------------------------------------------
    @property
    def person_name(self) -> str:
        return self._config.get(CONF_NAME, self.entry.title or self.entry.entry_id)

    @property
    def slug(self) -> str:
        return slugify(self.person_name)

    @property
    def players(self) -> list[str]:
        return list(self._config.get(CONF_PLAYERS, []))

    @property
    def reset_time(self) -> time:
        return _parse_reset_time(self._config.get(CONF_RESET_TIME, DEFAULT_RESET_TIME))

    @property
    def warning_enabled(self) -> bool:
        return bool(self._config.get(CONF_WARNING_ENABLED, False))

    @property
    def warning_threshold(self) -> int:
        return int(self._config.get(CONF_WARNING_THRESHOLD, DEFAULT_WARNING_THRESHOLD))

    @property
    def warning_method(self) -> str:
        return self._config.get(CONF_WARNING_METHOD, WARNING_METHOD_TTS)

    def budget_minutes_for(self, weekday_index: int) -> int:
        budgets = self._config.get(CONF_BUDGETS, {}) or {}
        return int(budgets.get(str(weekday_index), 0))

    # ------------------------------------------------------------------
    # Derived values
    # ------------------------------------------------------------------
    @property
    def _budget_minutes_today(self) -> int:
        media_date = self._media_date or dt_util.now().date()
        return self.budget_minutes_for(media_date.weekday())

    @property
    def _effective_budget_seconds(self) -> float:
        return (self._budget_minutes_today + self._extra_minutes) * 60.0

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    async def async_setup(self) -> None:
        """Restore persisted state and start listeners."""
        await self._async_restore()

        # React to player state changes (instant enforcement).
        self._unsubs.append(
            async_track_state_change_event(
                self.hass, self.players, self._handle_state_event
            )
        )
        # Precise daily reset.
        reset = self.reset_time
        self._unsubs.append(
            async_track_time_change(
                self.hass,
                self._handle_reset,
                hour=reset.hour,
                minute=reset.minute,
                second=reset.second,
            )
        )

        # Initial evaluation: this picks up a player that is already playing
        # at startup so counting resumes immediately.
        await self.async_config_entry_first_refresh()

    async def async_shutdown(self) -> None:
        """Cancel listeners and flush state to disk."""
        for unsub in self._unsubs:
            unsub()
        self._unsubs.clear()
        async with self._lock:
            await self._store.async_save(self._build_storage_data())

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def _build_storage_data(self) -> dict:
        return {
            "media_date": self._media_date.isoformat() if self._media_date else None,
            "accumulated_seconds": round(self._accumulated_seconds, 3),
            "is_locked": self._is_locked,
            "is_suspended": self._is_suspended,
            "warned_today": self._warned_today,
            "extra_minutes": self._extra_minutes,
            "last_reset": self._last_reset,
        }

    async def _async_restore(self) -> None:
        """Load persisted state, resetting if we crossed a day boundary."""
        now_local = dt_util.now()
        current_media_date = self._current_media_date(now_local)

        stored = await self._store.async_load()
        if not stored:
            self._do_reset(current_media_date)
            _LOGGER.debug("%s: no stored state, starting fresh", self.person_name)
            return

        stored_date_raw = stored.get("media_date")
        stored_date = (
            date.fromisoformat(stored_date_raw) if stored_date_raw else None
        )

        if stored_date == current_media_date:
            # Same media day: restore everything and keep counting.
            self._media_date = stored_date
            self._accumulated_seconds = float(stored.get("accumulated_seconds", 0.0))
            self._is_locked = bool(stored.get("is_locked", False))
            self._is_suspended = bool(stored.get("is_suspended", False))
            self._warned_today = bool(stored.get("warned_today", False))
            self._extra_minutes = int(stored.get("extra_minutes", 0))
            self._last_reset = stored.get("last_reset")
            _LOGGER.debug(
                "%s: restored %.0fs used, locked=%s, suspended=%s",
                self.person_name,
                self._accumulated_seconds,
                self._is_locked,
                self._is_suspended,
            )
        else:
            # HA was off across the reset boundary -> start a clean day.
            self._do_reset(current_media_date)
            _LOGGER.debug(
                "%s: stored day %s != current %s, reset",
                self.person_name,
                stored_date,
                current_media_date,
            )

    # ------------------------------------------------------------------
    # Media-day helpers
    # ------------------------------------------------------------------
    def _current_media_date(self, now_local: datetime) -> date:
        """Return the media day for ``now_local`` honouring the reset time."""
        reset = self.reset_time
        if now_local.time() < reset:
            return (now_local - timedelta(days=1)).date()
        return now_local.date()

    def _do_reset(self, new_media_date: date) -> None:
        """Reset all daily counters for ``new_media_date``."""
        self._media_date = new_media_date
        self._accumulated_seconds = 0.0
        self._is_locked = False
        self._is_suspended = False
        self._warned_today = False
        self._extra_minutes = 0
        self._last_reset = dt_util.utcnow().isoformat()
        self._checkpoint = None

    # ------------------------------------------------------------------
    # Player helpers
    # ------------------------------------------------------------------
    def _playing_players(self) -> list[str]:
        playing = []
        for entity_id in self.players:
            state = self.hass.states.get(entity_id)
            if state is not None and state.state == STATE_PLAYING:
                playing.append(entity_id)
        return playing

    def _any_player_playing(self) -> bool:
        return bool(self._playing_players())

    # ------------------------------------------------------------------
    # Core evaluation (must be called while holding self._lock)
    # ------------------------------------------------------------------
    def _collect(self, now: datetime) -> dict:
        """Advance state and return the snapshot for the entities."""
        self._tick(now)
        self._enforce()
        self._maybe_warn()
        self._store.async_delay_save(self._build_storage_data, 1)
        return self._snapshot()

    def _tick(self, now: datetime) -> None:
        """Advance accumulation and active membership up to ``now``."""
        now_local = dt_util.as_local(now)
        media_date = self._current_media_date(now_local)

        if media_date != self._media_date:
            # Crossed the reset boundary while running; discard the small
            # pre-boundary fragment and start the new day cleanly.
            _LOGGER.info(
                "%s: media day rolled over to %s, resetting", self.person_name, media_date
            )
            self._do_reset(media_date)
        elif self._active and self._checkpoint is not None:
            delta = (now - self._checkpoint).total_seconds()
            if delta > 0:
                self._accumulated_seconds += delta
            self._checkpoint = now

        # Recompute whether at least one player is currently playing.
        if self._any_player_playing():
            if not self._active or self._checkpoint is None:
                self._checkpoint = now
            self._active = True
        else:
            self._active = False
            self._checkpoint = None

    def _enforce(self) -> None:
        """Lock and stop players once the budget is exhausted."""
        if self._is_suspended:
            return

        effective = self._effective_budget_seconds
        if effective <= 0 or self._accumulated_seconds >= effective:
            if not self._is_locked:
                self._is_locked = True
                _LOGGER.info(
                    "%s: budget exhausted (used=%.0fs, budget=%.0fs) -> locked",
                    self.person_name,
                    self._accumulated_seconds,
                    effective,
                )

        if self._is_locked:
            playing = self._playing_players()
            if playing:
                _LOGGER.info(
                    "%s: locked, stopping players %s", self.person_name, playing
                )
                self.hass.async_create_task(
                    self.hass.services.async_call(
                        MP_DOMAIN,
                        SERVICE_MEDIA_STOP,
                        {ATTR_ENTITY_ID: playing},
                        blocking=False,
                    )
                )

    def _maybe_warn(self) -> None:
        """Emit the one-time low-time warning when appropriate."""
        if (
            not self.warning_enabled
            or self._is_locked
            or self._is_suspended
            or self._warned_today
        ):
            return

        effective = self._effective_budget_seconds
        remaining = effective - self._accumulated_seconds
        threshold = self.warning_threshold * 60
        playing = self._playing_players()

        if 0 < remaining <= threshold and playing:
            self._warned_today = True
            remaining_minutes = max(1, int(round(remaining / 60)))
            _LOGGER.info(
                "%s: %d min left -> warning on %s",
                self.person_name,
                remaining_minutes,
                playing,
            )
            self._send_warning(playing, remaining_minutes)

    def _send_warning(self, players: list[str], remaining_minutes: int) -> None:
        """Play the configured warning on the given players."""
        if self.warning_method == WARNING_METHOD_MEDIA:
            media_id = self._config.get(CONF_WARNING_MEDIA_ID)
            if not media_id:
                _LOGGER.warning("%s: warning media id not configured", self.person_name)
                return
            media_type = self._config.get(
                CONF_WARNING_MEDIA_TYPE, DEFAULT_WARNING_MEDIA_TYPE
            )
            self.hass.async_create_task(
                self.hass.services.async_call(
                    MP_DOMAIN,
                    SERVICE_PLAY_MEDIA,
                    {
                        ATTR_ENTITY_ID: players,
                        ATTR_MEDIA_CONTENT_ID: media_id,
                        ATTR_MEDIA_CONTENT_TYPE: media_type,
                    },
                    blocking=False,
                )
            )
            return

        # TTS path
        tts_entity = self._config.get(CONF_TTS_ENTITY)
        if not tts_entity:
            _LOGGER.warning("%s: TTS entity not configured", self.person_name)
            return
        message_template = self._config.get(CONF_TTS_MESSAGE, DEFAULT_TTS_MESSAGE)
        try:
            message = message_template.format(minutes=remaining_minutes)
        except (KeyError, IndexError, ValueError):
            message = message_template
        self.hass.async_create_task(
            self.hass.services.async_call(
                TTS_DOMAIN,
                SERVICE_TTS_SPEAK,
                {
                    ATTR_ENTITY_ID: tts_entity,
                    ATTR_MEDIA_PLAYER_ENTITY_ID: players,
                    ATTR_MESSAGE: message,
                },
                blocking=False,
            )
        )

    # ------------------------------------------------------------------
    # Snapshot for entities
    # ------------------------------------------------------------------
    def _snapshot(self) -> dict:
        effective = self._effective_budget_seconds
        remaining = max(0.0, effective - self._accumulated_seconds)
        return {
            ATTR_BUDGET_MINUTES: self._budget_minutes_today,
            ATTR_EFFECTIVE_BUDGET_MINUTES: self._budget_minutes_today
            + self._extra_minutes,
            ATTR_USED_MINUTES: round(self._accumulated_seconds / 60, 1),
            ATTR_REMAINING_MINUTES: round(remaining / 60, 1),
            ATTR_WEEKDAY: (self._media_date or dt_util.now().date()).weekday(),
            ATTR_IS_PLAYING: self._active,
            ATTR_IS_LOCKED: self._is_locked,
            ATTR_IS_SUSPENDED: self._is_suspended,
            ATTR_EXTRA_MINUTES_TODAY: self._extra_minutes,
            ATTR_WARNED_TODAY: self._warned_today,
            ATTR_LAST_RESET: self._last_reset,
            ATTR_PLAYERS: self.players,
        }

    # ------------------------------------------------------------------
    # DataUpdateCoordinator hook (periodic poll)
    # ------------------------------------------------------------------
    async def _async_update_data(self) -> dict:
        async with self._lock:
            return self._collect(dt_util.utcnow())

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------
    @callback
    def _handle_state_event(self, event: Event) -> None:
        self.hass.async_create_task(self._async_event_refresh())

    async def _async_event_refresh(self) -> None:
        async with self._lock:
            data = self._collect(dt_util.utcnow())
        self.async_set_updated_data(data)

    @callback
    def _handle_reset(self, now: datetime) -> None:
        self.hass.async_create_task(self._async_reset_refresh())

    async def _async_reset_refresh(self) -> None:
        async with self._lock:
            now = dt_util.utcnow()
            self._do_reset(self._current_media_date(dt_util.as_local(now)))
            data = self._collect(now)
        _LOGGER.info("%s: daily reset performed", self.person_name)
        self.async_set_updated_data(data)

    # ------------------------------------------------------------------
    # Public actions (services / entities)
    # ------------------------------------------------------------------
    async def async_extend_time(self, minutes: int) -> None:
        """Add ``minutes`` of extra budget for today."""
        async with self._lock:
            self._extra_minutes = max(0, self._extra_minutes + int(minutes))
            self._reevaluate_locked()
            data = self._collect(dt_util.utcnow())
        _LOGGER.info(
            "%s: extended by %d min (extra now %d)",
            self.person_name,
            minutes,
            self._extra_minutes,
        )
        self.async_set_updated_data(data)

    async def async_set_extra_minutes(self, minutes: int) -> None:
        """Set the absolute number of extra minutes for today."""
        async with self._lock:
            self._extra_minutes = max(0, int(minutes))
            self._reevaluate_locked()
            data = self._collect(dt_util.utcnow())
        self.async_set_updated_data(data)

    async def async_set_suspended(self, suspended: bool) -> None:
        """Suspend or resume enforcement for today."""
        async with self._lock:
            self._is_suspended = bool(suspended)
            data = self._collect(dt_util.utcnow())
        _LOGGER.info("%s: suspended=%s", self.person_name, suspended)
        self.async_set_updated_data(data)

    async def async_reset_person(self) -> None:
        """Manually reset the daily counters."""
        async with self._lock:
            now = dt_util.utcnow()
            self._do_reset(self._current_media_date(dt_util.as_local(now)))
            data = self._collect(now)
        _LOGGER.info("%s: manual reset", self.person_name)
        self.async_set_updated_data(data)

    def _reevaluate_locked(self) -> None:
        """Drop the lock if the (new) budget is no longer exhausted."""
        if (
            self._is_locked
            and self._effective_budget_seconds > self._accumulated_seconds
        ):
            self._is_locked = False
            _LOGGER.info("%s: budget available again -> unlocked", self.person_name)
