"""Common fixtures for Media Time Guard tests."""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from typing import Any

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.media_time_guard.const import (
    CONF_BUDGETS,
    CONF_NAME,
    CONF_PLAYERS,
    CONF_RESET_TIME,
    CONF_TTS_ENTITY,
    CONF_TTS_MESSAGE,
    CONF_WARNING_ENABLED,
    CONF_WARNING_METHOD,
    CONF_WARNING_THRESHOLD,
    DOMAIN,
    WARNING_METHOD_TTS,
)
from custom_components.media_time_guard.coordinator import PersonGuard

PLAYER = "media_player.test_player"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable loading of the custom integration in every test."""
    yield


def build_entry_data(
    *,
    name: str = "Luke",
    players: list[str] | None = None,
    budget_minutes: int = 60,
    reset_time: str = "00:00:00",
    warning: bool = False,
    warning_threshold: int = 5,
) -> dict[str, Any]:
    """Return config-entry data for a person."""
    return {
        CONF_NAME: name,
        CONF_PLAYERS: players if players is not None else [PLAYER],
        CONF_BUDGETS: {str(i): budget_minutes for i in range(7)},
        CONF_RESET_TIME: reset_time,
        CONF_WARNING_ENABLED: warning,
        CONF_WARNING_THRESHOLD: warning_threshold,
        CONF_WARNING_METHOD: WARNING_METHOD_TTS,
        CONF_TTS_ENTITY: "tts.test_engine",
        CONF_TTS_MESSAGE: "Noch {minutes} Minuten",
    }


@pytest.fixture
def make_guard(
    hass,
) -> Callable[..., Coroutine[Any, Any, PersonGuard]]:
    """Return a coroutine factory creating a restored PersonGuard."""

    async def _factory(**kwargs: Any) -> PersonGuard:
        entry = MockConfigEntry(domain=DOMAIN, data=build_entry_data(**kwargs))
        entry.add_to_hass(hass)
        guard = PersonGuard(hass, entry)
        await guard._async_restore()
        return guard

    return _factory
