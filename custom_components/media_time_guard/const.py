"""Constants for the Media Time Guard integration."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "media_time_guard"

# --- Config / Options keys -------------------------------------------------
CONF_NAME = "name"
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
DEFAULT_TTS_MESSAGE = "Achtung: Du hast nur noch {minutes} Minuten Medienzeit."
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

ATTR_PERSON = "person"
ATTR_MINUTES = "minutes"
ATTR_SUSPENDED = "suspended"

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
ATTR_EXTRA_MINUTES_TODAY = "extra_minutes_today"
ATTR_WARNED_TODAY = "warned_today"
ATTR_LAST_RESET = "last_reset"
ATTR_EFFECTIVE_BUDGET_MINUTES = "effective_budget_minutes"
ATTR_PLAYERS = "players"
