"""Tests for the Media Time Guard config flow."""

from __future__ import annotations

from homeassistant.config_entries import SOURCE_USER
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.media_time_guard.const import (
    CONF_BUDGETS,
    CONF_NAME,
    CONF_PLAYERS,
    CONF_RESET_TIME,
    CONF_WARNING_ENABLED,
    CONF_WARNING_METHOD,
    CONF_WARNING_THRESHOLD,
    DOMAIN,
    WARNING_METHOD_TTS,
)

from .conftest import build_entry_data


async def _advance_full_flow(hass, name="Luke", players=None):
    players = players or ["media_player.test_player"]
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_NAME: name, CONF_PLAYERS: players},
    )
    assert result["step_id"] == "budgets"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {f"budget_{i}": 60 for i in range(7)},
    )
    assert result["step_id"] == "warning"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_WARNING_ENABLED: False,
            CONF_WARNING_THRESHOLD: 5,
            CONF_WARNING_METHOD: WARNING_METHOD_TTS,
        },
    )
    assert result["step_id"] == "reset"

    return await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_RESET_TIME: "00:00:00"},
    )


async def test_full_config_flow(hass):
    """A complete flow creates an entry with all the collected data."""
    result = await _advance_full_flow(hass)
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "Luke"
    data = result["data"]
    assert data[CONF_NAME] == "Luke"
    assert data[CONF_PLAYERS] == ["media_player.test_player"]
    assert data[CONF_BUDGETS] == {str(i): 60 for i in range(7)}
    assert data[CONF_RESET_TIME] == "00:00:00"


async def test_player_already_assigned(hass):
    """Selecting a player owned by another person raises an error."""
    existing = MockConfigEntry(
        domain=DOMAIN,
        data=build_entry_data(name="Leo", players=["media_player.test_player"]),
    )
    existing.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_NAME: "Luke", CONF_PLAYERS: ["media_player.test_player"]},
    )
    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "player_in_use"}
