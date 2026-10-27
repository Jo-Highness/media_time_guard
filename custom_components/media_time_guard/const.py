"""Constants for the Media Time Guard integration."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "media_time_guard"

# --- Config / Options keys -------------------------------------------------
CONF_NAME = "name"
# Legacy key from <= 1.1.x. It was never used by the runtime logic and is no
# longer offered in the flows, but existing entries may still contain it.
CONF_PERSON_ENTITY = "person_entity"
CONF_PLAYERS = "players"
CONF_BUDGETS = "budgets"  # dict weekday-index(str) -> minutes(int)
CONF_RESET_TIME = "reset_time"  # "HH:MM:SS"

CONF_WARNING_ENABLED = "warning_enabled"
CONF_WARNING_THRESHOLD = "warning_threshold"  # minutes
CONF_WARNING_METHOD = "warning_method"  # "tts" | "media"
CONF_TTS_ENTITY = "tts_entity"
CONF_TTS_MESSAGE = "tts_message"
CONF_WARNING_MEDIA_ID = "warning_media_id"
CONF_WARNING_MEDIA_TYPE = "warning_media_type"

WARNING_METHOD_TTS = "tts"
WARNING_METHOD_MEDIA = "media"
WARNING_METHODS = [WARNING_METHOD_TTS, WARNING_METHOD_MEDIA]

# --- Defaults --------------------------------------------------------------
DEFAULT_RESET_TIME = "00:00:00"
DEFAULT_WARNING_THRESHOLD = 10
DEFAULT_DAILY_MINUTES = 60
# Default announcement per UI language (``hass.config.language``); English is
# the fallback for languages without an entry.
DEFAULT_TTS_MESSAGES: dict[str, str] = {
    "de": "Achtung: Du hast nur noch {minutes} Minuten Medienzeit.",
    "el": "Προσοχή: σου απομένουν μόνο {minutes} λεπτά χρόνου πολυμέσων.",
    "en": "Heads-up: you only have {minutes} minutes of media time left.",
    "es": "Atención: solo te quedan {minutes} minutos de tiempo multimedia.",
    "fr": "Attention : il ne te reste que {minutes} minutes de temps multimédia.",
    "ja": "お知らせ：メディアの時間はあと{minutes}分です。",
    "nb": "Obs: Du har bare {minutes} minutter medietid igjen.",
}
DEFAULT_TTS_LANGUAGE = "en"
DEFAULT_WARNING_MEDIA_TYPE = "music"

# Weekday indices follow datetime.weekday(): Monday=0 .. Sunday=6.
WEEKDAYS = ["0", "1", "2", "3", "4", "5", "6"]

# Quick-extend button presets (minutes).
EXTEND_BUTTON_PRESETS = [15, 30]

# Bounds for the "extra minutes" number entity.
EXTRA_MINUTES_MIN = 0
EXTRA_MINUTES_MAX = 600
EXTRA_MINUTES_STEP = 5

# --- Player states ---------------------------------------------------------
STATE_PLAYING = "playing"

# --- Timing ----------------------------------------------------------------
# Periodic poll/checkpoint interval. Keeps the sensor live and acts as a
# redundant backup for both time accumulation and lock enforcement.
POLL_INTERVAL = timedelta(seconds=20)

# --- Storage ---------------------------------------------------------------
STORAGE_VERSION = 1
STORAGE_KEY_PREFIX = f"{DOMAIN}."

# --- Services --------------------------------------------------------------
SERVICE_EXTEND_TIME = "extend_time"
SERVICE_SUSPEND_TODAY = "suspend_today"
SERVICE_RESET_PERSON = "reset_person"
SERVICE_SET_BLOCKED = "set_blocked"

ATTR_PERSON = "person"
ATTR_CONFIG_ENTRY_ID = "config_entry_id"
ATTR_MINUTES = "minutes"
ATTR_SUSPENDED = "suspended"
ATTR_BLOCKED = "blocked"

# --- Dispatcher ------------------------------------------------------------
SIGNAL_UPDATE = f"{DOMAIN}_update"

# --- Entity attribute keys -------------------------------------------------
ATTR_BUDGET_MINUTES = "budget_minutes"
ATTR_USED_MINUTES = "used_minutes"
ATTR_REMAINING_MINUTES = "remaining_minutes"
ATTR_WEEKDAY = "weekday"
ATTR_IS_PLAYING = "is_playing"
ATTR_IS_LOCKED = "is_locked"
ATTR_IS_SUSPENDED = "is_suspended"
ATTR_IS_BLOCKED = "is_blocked"
ATTR_EXTRA_MINUTES_TODAY = "extra_minutes_today"
ATTR_WARNED_TODAY = "warned_today"
ATTR_LAST_RESET = "last_reset"
ATTR_EFFECTIVE_BUDGET_MINUTES = "effective_budget_minutes"
ATTR_PLAYERS = "players"


def default_tts_message(language: str | None) -> str:
    """Return the default warning text for a Home Assistant UI language."""
    lang = (language or DEFAULT_TTS_LANGUAGE).replace("_", "-").split("-")[0].casefold()
    if lang in ("no", "nn"):
        lang = "nb"
    return DEFAULT_TTS_MESSAGES.get(lang, DEFAULT_TTS_MESSAGES[DEFAULT_TTS_LANGUAGE])
