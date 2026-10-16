"""Tests for the Media Time Guard config flow."""

from __future__ import annotations

from homeassistant.config_entries import SOURCE_USER, ConfigEntryState
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.media_time_guard.const import (
    CONF_BUDGETS,
    CONF_NAME,
    CONF_PERSON_ENTITY,
    CONF_PLAYERS,
    CONF_RESET_TIME,
    CONF_TTS_ENTITY,
    CONF_TTS_MESSAGE,
    CONF_WARNING_ENABLED,
    CONF_WARNING_MEDIA_ID,
    CONF_WARNING_MEDIA_TYPE,
    CONF_WARNING_METHOD,
    CONF_WARNING_THRESHOLD,
    DOMAIN,
    WARNING_METHOD_MEDIA,
    WARNING_METHOD_TTS,
    default_tts_message,
)

from .conftest import build_entry_data, setup_person


async def _advance_full_flow(hass, name="Luke", players=None):
    players = players or ["media_player.test_player"]
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
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

    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_NAME: "Luke", CONF_PLAYERS: ["media_player.test_player"]},
    )
    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "player_in_use"}


async def test_duplicate_name_aborts(hass):
    """A second person with the same name (any case) is rejected."""
    MockConfigEntry(
        domain=DOMAIN, title="Luke", data=build_entry_data(name="Luke", players=["media_player.a"])
    ).add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_NAME: " luke ", CONF_PLAYERS: ["media_player.b"]}
    )
    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_name_freed_by_rename_can_be_reused(hass):
    """After 'Luke' was renamed to 'Lukas', a new 'Luke' can be created."""
    MockConfigEntry(
        domain=DOMAIN,
        title="Lukas",
        unique_id=f"{DOMAIN}_luke",
        data=build_entry_data(name="Luke", players=["media_player.a"]),
        options=build_entry_data(name="Lukas", players=["media_player.a"]),
    ).add_to_hass(hass)
    result = await _advance_full_flow(hass, name="Luke", players=["media_player.b"])
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["result"].unique_id.startswith(f"{DOMAIN}_luke_")


async def test_user_step_has_no_person_entity_field(hass):
    """The unused 'person entity' field is no longer offered."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    assert CONF_PERSON_ENTITY not in {str(key) for key in result["data_schema"].schema}


async def test_warning_requires_tts_entity_or_media_id(hass):
    """The warning step validates the fields for the chosen method."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_NAME: "Luke", CONF_PLAYERS: ["media_player.test_player"]}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {f"budget_{i}": 60 for i in range(7)}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_WARNING_ENABLED: True,
            CONF_WARNING_THRESHOLD: 5,
            CONF_WARNING_METHOD: WARNING_METHOD_TTS,
        },
    )
    assert result["errors"] == {"base": "tts_entity_required"}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_WARNING_ENABLED: True,
            CONF_WARNING_THRESHOLD: 5,
            CONF_WARNING_METHOD: WARNING_METHOD_MEDIA,
        },
    )
    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "media_id_required"}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_WARNING_ENABLED: True,
            CONF_WARNING_THRESHOLD: 5,
            CONF_WARNING_METHOD: WARNING_METHOD_MEDIA,
            CONF_WARNING_MEDIA_ID: "media-source://media_source/local/bell.mp3",
        },
    )
    assert result["step_id"] == "reset"


async def test_default_tts_message_follows_ui_language(hass):
    """The suggested announcement is in the Home Assistant UI language."""
    hass.config.language = "es"
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_NAME: "Luke", CONF_PLAYERS: ["media_player.test_player"]}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {f"budget_{i}": 60 for i in range(7)}
    )
    assert result["step_id"] == "warning"
    suggested = _suggested(result, CONF_TTS_MESSAGE)
    assert suggested == default_tts_message("es")
    assert "minutos" in suggested


def _suggested(result, key):
    for marker in result["data_schema"].schema:
        if str(marker) == key:
            return (marker.description or {}).get("suggested_value")
    raise AssertionError(key)


# --------------------------------------------------------------------------
# Options flow
# --------------------------------------------------------------------------


async def _run_options_flow(hass, entry, *, user=None, warning=None, reset="00:00:00"):
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["step_id"] == "init"
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user or {CONF_NAME: "Luke", CONF_PLAYERS: ["media_player.test_player"]},
    )
    if result["type"] == FlowResultType.FORM and result["step_id"] == "init":
        return result
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {f"budget_{i}": 90 for i in range(7)}
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        warning
        or {
            CONF_WARNING_ENABLED: False,
            CONF_WARNING_THRESHOLD: 5,
            CONF_WARNING_METHOD: WARNING_METHOD_TTS,
        },
    )
    if result["type"] == FlowResultType.FORM and result["step_id"] == "warning":
        return result
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_RESET_TIME: reset}
    )
    await hass.async_block_till_done()
    return result


async def test_options_flow_updates_everything(hass):
    """The options flow stores all values and reloads the entry."""
    entry = await setup_person(hass, name="Luke")
    result = await _run_options_flow(hass, entry, reset="05:00:00")
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert entry.options[CONF_BUDGETS] == {str(i): 90 for i in range(7)}
    assert entry.options[CONF_RESET_TIME] == "05:00:00"
    assert entry.state is ConfigEntryState.LOADED
    assert entry.runtime_data.budget_minutes_for(0) == 90


async def test_options_flow_can_clear_optional_fields(hass):
    """Cleared optional fields are removed instead of keeping old values."""
    entry = await setup_person(
        hass,
        name="Luke",
        options={
            **build_entry_data(name="Luke"),
            CONF_PERSON_ENTITY: "person.luke",
            CONF_WARNING_MEDIA_ID: "http://example.invalid/bell.mp3",
            CONF_WARNING_MEDIA_TYPE: "music",
        },
    )
    result = await _run_options_flow(hass, entry)
    assert result["type"] == FlowResultType.CREATE_ENTRY
    for key in (
        CONF_TTS_ENTITY,
        CONF_TTS_MESSAGE,
        CONF_WARNING_MEDIA_ID,
        CONF_WARNING_MEDIA_TYPE,
        CONF_PERSON_ENTITY,
    ):
        assert key not in entry.options, key


async def test_options_flow_rename_updates_title_keeps_unique_id(hass):
    """Renaming updates the entry title; the unique_id stays unchanged."""
    entry = await setup_person(hass, name="Luke")
    unique_id = entry.unique_id
    result = await _run_options_flow(
        hass, entry, user={CONF_NAME: "Lukas", CONF_PLAYERS: ["media_player.test_player"]}
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert entry.title == "Lukas"
    assert entry.unique_id == unique_id
    assert entry.runtime_data.person_name == "Lukas"
    # Existing entity ids are kept (registry wins).
    assert hass.states.get("sensor.media_time_luke_remaining") is not None


async def test_options_flow_rejects_duplicate_name(hass):
    """Renaming to another person's name is refused."""
    await setup_person(hass, name="Leo", players=["media_player.leo"])
    entry = await setup_person(hass, name="Luke")
    result = await _run_options_flow(
        hass, entry, user={CONF_NAME: "leo", CONF_PLAYERS: ["media_player.test_player"]}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "name_in_use"}


async def test_options_flow_rejects_player_of_other_person(hass):
    """A player owned by another person cannot be added in the options."""
    await setup_person(hass, name="Leo", players=["media_player.leo"])
    entry = await setup_person(hass, name="Luke")
    result = await _run_options_flow(
        hass, entry, user={CONF_NAME: "Luke", CONF_PLAYERS: ["media_player.leo"]}
    )
    assert result["errors"] == {"base": "player_in_use"}


async def test_options_flow_validates_warning(hass):
    """The options warning step validates like the config flow."""
    entry = await setup_person(hass, name="Luke")
    result = await _run_options_flow(
        hass,
        entry,
        warning={
            CONF_WARNING_ENABLED: True,
            CONF_WARNING_THRESHOLD: 5,
            CONF_WARNING_METHOD: WARNING_METHOD_MEDIA,
        },
    )
    assert result["errors"] == {"base": "media_id_required"}


async def test_user_step_requires_name_and_players(hass):
    """Blank names and empty player lists are rejected."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_NAME: "  ", CONF_PLAYERS: ["media_player.test_player"]}
    )
    assert result["errors"] == {"base": "name_required"}
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_NAME: "Luke", CONF_PLAYERS: []}
    )
    assert result["errors"] == {"base": "no_players"}
