"""Access control (1.4.0): only admins, allowed users and automations may change."""

from __future__ import annotations

import asyncio
import logging

from homeassistant.auth.const import GROUP_ID_ADMIN, GROUP_ID_USER
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import Context
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.exceptions import Unauthorized
from homeassistant.setup import async_setup_component
import pytest

from custom_components.media_time_guard.const import (
    ATTR_EXTRA_MINUTES_TODAY,
    ATTR_IS_BLOCKED,
    ATTR_IS_SUSPENDED,
    CONF_ALLOWED_USERS,
    CONF_NAME,
    CONF_PLAYERS,
    CONF_RESET_TIME,
    CONF_RESTRICT_CHANGES,
    CONF_WARNING_ENABLED,
    CONF_WARNING_METHOD,
    CONF_WARNING_THRESHOLD,
    DOMAIN,
    WARNING_METHOD_TTS,
)

from .conftest import setup_person

BUTTON = "button.media_time_luke_extend_15"
NUMBER = "number.media_time_luke_extend"
SUSPEND = "switch.media_time_luke_suspend_today"
BLOCKED = "switch.media_time_luke_blocked"


@pytest.fixture(autouse=True)
def _owner_exists(hass_owner_user):
    """The first user created becomes owner (= admin); create the owner first."""
    return hass_owner_user


async def _user(hass, name: str, *, admin: bool = False, active: bool = True):
    user = await hass.auth.async_create_user(
        name, group_ids=[GROUP_ID_ADMIN if admin else GROUP_ID_USER]
    )
    if not active:
        await hass.auth.async_deactivate_user(user)
    return user


async def _restricted(hass, allowed: list[str] | None = None):
    return await setup_person(
        hass,
        options={CONF_RESTRICT_CHANGES: True, CONF_ALLOWED_USERS: allowed or []},
    )


def _ctx(user=None) -> Context:
    return Context(user_id=user.id if user is not None else None)


# Every mutating path: (domain, service, data). Entity actions + domain services.
WRITE_CALLS = [
    ("button", "press", {"entity_id": BUTTON}),
    ("number", "set_value", {"entity_id": NUMBER, "value": 45}),
    ("switch", "turn_on", {"entity_id": SUSPEND}),
    ("switch", "turn_on", {"entity_id": BLOCKED}),
    (DOMAIN, "extend_time", {"person": "Luke", "minutes": 20}),
    (DOMAIN, "suspend_today", {"person": "Luke", "suspended": True}),
    (DOMAIN, "set_blocked", {"person": "Luke", "blocked": True}),
    (DOMAIN, "reset_person", {"person": "Luke"}),
]
IDS = [f"{d}.{s}:{v.get('entity_id', '')}" for d, s, v in WRITE_CALLS]


def _snapshot(entry) -> tuple:
    data = entry.runtime_data.data
    return (
        data[ATTR_EXTRA_MINUTES_TODAY],
        data[ATTR_IS_SUSPENDED],
        data[ATTR_IS_BLOCKED],
        entry.runtime_data._accumulated_seconds,
    )


@pytest.mark.parametrize(("domain", "service", "data"), WRITE_CALLS, ids=IDS)
async def test_non_admin_refused_everywhere(hass, domain, service, data, caplog):
    """A non-admin, non-allowed user is refused and nothing changes."""
    entry = await _restricted(hass)
    entry.runtime_data._accumulated_seconds = 600.0
    tablet = await _user(hass, "Tablet")
    before = _snapshot(entry)

    caplog.set_level(logging.WARNING)
    with pytest.raises(Unauthorized):
        await hass.services.async_call(domain, service, data, blocking=True, context=_ctx(tablet))
    await hass.async_block_till_done()

    assert _snapshot(entry) == before
    assert "refused for user Tablet" in caplog.text


@pytest.mark.parametrize(("domain", "service", "data"), WRITE_CALLS, ids=IDS)
@pytest.mark.parametrize("who", ["admin", "allowed", "system"])
async def test_permitted_callers(hass, domain, service, data, who):
    """Admins, explicitly allowed users and user-less contexts may change."""
    caller = None
    if who == "admin":
        caller = await _user(hass, "Mum", admin=True)
    elif who == "allowed":
        caller = await _user(hass, "Nanny")
    entry = await _restricted(hass, allowed=[caller.id] if who == "allowed" else [])
    entry.runtime_data._accumulated_seconds = 600.0
    before = _snapshot(entry)

    await hass.services.async_call(domain, service, data, blocking=True, context=_ctx(caller))
    await hass.async_block_till_done()

    assert _snapshot(entry) != before


async def test_switch_turn_off_refused(hass):
    """Lifting a block is guarded just like setting it."""
    entry = await _restricted(hass)
    await entry.runtime_data.async_set_blocked(True, context=Context())
    await entry.runtime_data.async_set_suspended(True, context=Context())
    tablet = await _user(hass, "Tablet")
    for entity_id in (BLOCKED, SUSPEND):
        with pytest.raises(Unauthorized):
            await hass.services.async_call(
                "switch", "turn_off", {"entity_id": entity_id}, blocking=True, context=_ctx(tablet)
            )
    assert entry.runtime_data.data[ATTR_IS_BLOCKED] is True
    assert entry.runtime_data.data[ATTR_IS_SUSPENDED] is True


async def test_restriction_off_allows_everyone(hass):
    """Default (and entries from <= 1.3.0 without the keys): unchanged behaviour."""
    entry = await setup_person(hass)
    tablet = await _user(hass, "Tablet")
    await hass.services.async_call(
        "button", "press", {"entity_id": BUTTON}, blocking=True, context=_ctx(tablet)
    )
    assert entry.runtime_data.data[ATTR_EXTRA_MINUTES_TODAY] == 15


async def test_inactive_allowed_user_refused(hass):
    """A deactivated user is refused even if listed (fail closed)."""
    nanny = await _user(hass, "Nanny", active=False)
    entry = await _restricted(hass, allowed=[nanny.id])
    with pytest.raises(Unauthorized):
        await entry.runtime_data.async_extend_time(15, context=_ctx(nanny))
    assert entry.runtime_data.data[ATTR_EXTRA_MINUTES_TODAY] == 0


async def test_unknown_user_refused(hass):
    """A user id that does not exist (deleted user) is refused."""
    entry = await _restricted(hass, allowed=["deadbeef"])
    with pytest.raises(Unauthorized):
        await entry.runtime_data.async_extend_time(15, context=Context(user_id="deadbeef"))


async def test_unauthorized_carries_details(hass):
    """The exception names user, entry and action (for logs / websocket)."""
    entry = await _restricted(hass)
    tablet = await _user(hass, "Tablet")
    with pytest.raises(Unauthorized) as err:
        await entry.runtime_data.async_set_blocked(False, context=_ctx(tablet))
    assert err.value.user_id == tablet.id
    assert err.value.config_entry_id == entry.entry_id
    assert err.value.permission == "set_blocked"


async def test_script_started_by_tablet_is_refused(hass):
    """A script run by the tablet user carries its user -> refused."""
    entry = await _restricted(hass)
    tablet = await _user(hass, "Tablet")
    assert await async_setup_component(
        hass,
        "script",
        {
            "script": {
                "more_time": {
                    "sequence": [
                        {"action": "button.press", "target": {"entity_id": BUTTON}},
                    ]
                }
            }
        },
    )
    await hass.async_block_till_done()
    with pytest.raises(Unauthorized):
        await hass.services.async_call("script", "more_time", blocking=True, context=_ctx(tablet))
    assert entry.runtime_data.data[ATTR_EXTRA_MINUTES_TODAY] == 0


async def test_automation_trigger_runs_without_user(hass):
    """Documented residual risk: automations run without the user's id."""
    entry = await _restricted(hass)
    tablet = await _user(hass, "Tablet")
    assert await async_setup_component(
        hass,
        "automation",
        {
            "automation": {
                "id": "more_time",
                "alias": "more time",
                "triggers": [{"trigger": "event", "event_type": "never_fired"}],
                "actions": [{"action": "button.press", "target": {"entity_id": BUTTON}}],
            }
        },
    )
    await hass.async_block_till_done()
    await hass.services.async_call(
        "automation",
        "trigger",
        {"entity_id": "automation.more_time"},
        blocking=True,
        context=_ctx(tablet),
    )
    await hass.async_block_till_done()
    assert entry.runtime_data.data[ATTR_EXTRA_MINUTES_TODAY] == 15


async def test_parallel_calls_keep_their_own_context(hass):
    """Admin and tablet pressing at the same time: only the admin's press counts."""
    entry = await _restricted(hass)
    tablet = await _user(hass, "Tablet")
    admin = await _user(hass, "Mum", admin=True)

    async def press(user):
        await hass.services.async_call(
            "button", "press", {"entity_id": BUTTON}, blocking=True, context=_ctx(user)
        )

    results = await asyncio.gather(
        press(tablet), press(admin), press(tablet), press(admin), return_exceptions=True
    )
    assert [type(r) for r in results] == [Unauthorized, type(None), Unauthorized, type(None)]
    assert entry.runtime_data.data[ATTR_EXTRA_MINUTES_TODAY] == 30


async def test_entity_action_without_context_fails_closed(hass):
    """Should an entity method ever run without a service context: refuse."""
    await _restricted(hass)
    button = next(
        e for e in hass.data["entity_components"]["button"].entities if e.entity_id == BUTTON
    )
    button._context = None
    with pytest.raises(Unauthorized):
        await button.async_press()


# --------------------------------------------------------------------------
# Config / options flow
# --------------------------------------------------------------------------


def _access_options(result) -> list[str]:
    for marker, sel in result["data_schema"].schema.items():
        if str(marker) == CONF_ALLOWED_USERS:
            return [option["value"] for option in sel.config["options"]]
    raise AssertionError("allowed_users missing")


def _default(result, key):
    for marker in result["data_schema"].schema:
        if str(marker) == key:
            return marker.default()
    raise AssertionError(key)


async def test_config_flow_access_step(hass):
    """The access step lists only active, real, non-admin users and stores the choice."""
    tablet = await _user(hass, "Tablet")
    nanny = await _user(hass, "Nanny")
    admin = await _user(hass, "Mum", admin=True)
    gone = await _user(hass, "Old", active=False)

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
            CONF_WARNING_ENABLED: False,
            CONF_WARNING_THRESHOLD: 5,
            CONF_WARNING_METHOD: WARNING_METHOD_TTS,
        },
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_RESET_TIME: "00:00:00"}
    )
    assert result["step_id"] == "access"
    offered = _access_options(result)
    assert tablet.id in offered
    assert nanny.id in offered
    assert admin.id not in offered
    assert gone.id not in offered
    assert _default(result, CONF_RESTRICT_CHANGES) is False

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_RESTRICT_CHANGES: True, CONF_ALLOWED_USERS: [nanny.id]}
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_RESTRICT_CHANGES] is True
    assert result["data"][CONF_ALLOWED_USERS] == [nanny.id]


async def test_options_flow_drops_deleted_users_from_default(hass):
    """A since-deleted allowed user must not break the options form."""
    nanny = await _user(hass, "Nanny")
    entry = await _restricted(hass, allowed=[nanny.id, "deleted-user-id"])

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_NAME: "Luke", CONF_PLAYERS: ["media_player.test_player"]}
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {f"budget_{i}": 60 for i in range(7)}
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_WARNING_ENABLED: False,
            CONF_WARNING_THRESHOLD: 5,
            CONF_WARNING_METHOD: WARNING_METHOD_TTS,
        },
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_RESET_TIME: "00:00:00"}
    )
    assert result["step_id"] == "access"
    assert _default(result, CONF_RESTRICT_CHANGES) is True
    assert _default(result, CONF_ALLOWED_USERS) == [nanny.id]

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_RESTRICT_CHANGES: False, CONF_ALLOWED_USERS: []}
    )
    await hass.async_block_till_done()
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert entry.options[CONF_RESTRICT_CHANGES] is False
    assert entry.options[CONF_ALLOWED_USERS] == []
