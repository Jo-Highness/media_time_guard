"""Diagnostics support for Media Time Guard."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from . import MediaTimeGuardConfigEntry
from .const import (
    CONF_NAME,
    CONF_PERSON_ENTITY,
    CONF_PLAYERS,
    CONF_TTS_ENTITY,
    CONF_TTS_MESSAGE,
    CONF_WARNING_MEDIA_ID,
)

# Names of children, entity ids (which often contain names or rooms), the
# announcement text and media URLs are personal - never include them.
TO_REDACT = {
    CONF_NAME,
    CONF_PERSON_ENTITY,
    CONF_PLAYERS,
    CONF_TTS_ENTITY,
    CONF_TTS_MESSAGE,
    CONF_WARNING_MEDIA_ID,
    "title",
    "unique_id",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: MediaTimeGuardConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    guard = entry.runtime_data
    players = []
    for index, entity_id in enumerate(guard.players):
        state = hass.states.get(entity_id)
        players.append(
            {
                "index": index,
                "state": state.state if state else None,
                "exists": state is not None,
            }
        )
    snapshot = dict(guard.data or {})
    snapshot.pop(CONF_PLAYERS, None)
    return {
        "entry": async_redact_data(
            {
                "version": entry.version,
                "title": entry.title,
                "unique_id": entry.unique_id,
                "data": dict(entry.data),
                "options": dict(entry.options),
            },
            TO_REDACT,
        ),
        "players": players,
        "tts_entity_configured": guard.tts_entity is not None,
        "state": snapshot,
        "last_update_success": guard.last_update_success,
    }
