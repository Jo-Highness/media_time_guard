"""QA (1.4.0 access control): adversarial checks beyond test_access.py.

Covers ADR f1d19c22 / review 8bc49284 (A1-A6): scenes, forced races,
partial effects, reload/restart, entries without the new keys, real
websocket/REST callers, per-person scope and toggle paths.
"""

from __future__ import annotations

import asyncio
from http import HTTPStatus
import inspect
from unittest.mock import patch

from homeassistant.auth.const import GROUP_ID_ADMIN, GROUP_ID_USER
from homeassistant.core import Context
from homeassistant.exceptions import Unauthorized
from homeassistant.setup import async_setup_component
import pytest
from pytest_homeassistant_custom_component.common import CLIENT_ID, MockConfigEntry
from pytest_homeassistant_custom_component.components.diagnostics import (
    get_diagnostics_for_config_entry,
)

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
from custom_components.media_time_guard.coordinator import PersonGuard

from .conftest import PLAYER, build_entry_data, setup_person

BUTTON = "button.media_time_luke_extend_15"
NUMBER = "number.media_time_luke_extend"
SUSPEND = "switch.media_time_luke_suspend_today"
BLOCKED = "switch.media_time_luke_blocked"
LEIA_SUSPEND = "switch.media_time_leia_suspend_today"
LEIA_PLAYER = "media_player.leia_player"


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


async def _restricted(hass, allowed: list[str] | None = None, **kwargs):
    return await setup_person(
        hass,
        options={CONF_RESTRICT_CHANGES: True, CONF_ALLOWED_USERS: allowed or []},
        **kwargs,
    )


def _ctx(user=None) -> Context:
    return Context(user_id=user.id if user is not None else None)


def _entity(hass, domain: str, entity_id: str):
    return next(
        e for e in hass.data["entity_components"][domain].entities if e.entity_id == entity_id
    )


async def _issue_token(hass, user) -> str:
    refresh = await hass.auth.async_create_refresh_token(user, CLIENT_ID)
    return hass.auth.async_create_access_token(refresh)


# --------------------------------------------------------------------------
# A1: mandatory keyword-only context on every public action
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "name",
    [
        "async_extend_time",
        "async_set_extra_minutes",
        "async_set_suspended",
        "async_set_blocked",
        "async_reset_person",
    ],
)
def test_public_actions_require_keyword_context(name):
    """``context`` is keyword-only and has no default (A1)."""
    param = inspect.signature(getattr(PersonGuard, name)).parameters["context"]
    assert param.kind is inspect.Parameter.KEYWORD_ONLY
    assert param.default is inspect.Parameter.empty


# --------------------------------------------------------------------------
# Scenes (A6): scene.apply and scene.turn_on run in the caller's context
# --------------------------------------------------------------------------


async def test_scene_apply_by_tablet_refused(hass):
    entry = await _restricted(hass)
    tablet = await _user(hass, "Tablet")
    assert await async_setup_component(hass, "scene", {})
    await hass.async_block_till_done()

    with pytest.raises(Unauthorized):
        await hass.services.async_call(
            "scene",
            "apply",
            {"entities": {SUSPEND: "on", BLOCKED: "off"}},
            blocking=True,
            context=_ctx(tablet),
        )
    assert entry.runtime_data.data[ATTR_IS_SUSPENDED] is False


async def test_scene_apply_unblock_by_tablet_refused(hass):
    """The child's real goal: lift a block via scene.apply."""
    entry = await _restricted(hass)
    await entry.runtime_data.async_set_blocked(True, context=Context())
    await hass.async_block_till_done()
    tablet = await _user(hass, "Tablet")
    assert await async_setup_component(hass, "scene", {})

    with pytest.raises(Unauthorized):
        await hass.services.async_call(
            "scene", "apply", {"entities": {BLOCKED: "off"}}, blocking=True, context=_ctx(tablet)
        )
    assert entry.runtime_data.data[ATTR_IS_BLOCKED] is True


async def test_scene_turn_on_by_tablet_refused_admin_allowed(hass):
    """A configured scene: refused for the tablet, works for an admin (control)."""
    entry = await _restricted(hass)
    tablet = await _user(hass, "Tablet")
    admin = await _user(hass, "Mum", admin=True)
    assert await async_setup_component(
        hass, "scene", {"scene": [{"name": "Freizeit", "entities": {SUSPEND: "on"}}]}
    )
    await hass.async_block_till_done()

    with pytest.raises(Unauthorized):
        await hass.services.async_call(
            "scene", "turn_on", {"entity_id": "scene.freizeit"}, blocking=True, context=_ctx(tablet)
        )
    assert entry.runtime_data.data[ATTR_IS_SUSPENDED] is False

    await hass.services.async_call(
        "scene", "turn_on", {"entity_id": "scene.freizeit"}, blocking=True, context=_ctx(admin)
    )
    await hass.async_block_till_done()
    assert entry.runtime_data.data[ATTR_IS_SUSPENDED] is True


async def test_script_calling_domain_service_by_tablet_refused(hass):
    """Script -> media_time_guard.set_blocked keeps the tablet's user id."""
    entry = await _restricted(hass)
    await entry.runtime_data.async_set_blocked(True, context=Context())
    tablet = await _user(hass, "Tablet")
    assert await async_setup_component(
        hass,
        "script",
        {
            "script": {
                "unblock": {
                    "sequence": [
                        {
                            "action": f"{DOMAIN}.set_blocked",
                            "data": {"person": "Luke", "blocked": False},
                        }
                    ]
                }
            }
        },
    )
    await hass.async_block_till_done()
    with pytest.raises(Unauthorized):
        await hass.services.async_call("script", "unblock", blocking=True, context=_ctx(tablet))
    await hass.async_block_till_done()
    assert entry.runtime_data.data[ATTR_IS_BLOCKED] is True


# --------------------------------------------------------------------------
# Other generic write paths
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("domain", "service"),
    [("switch", "toggle"), ("homeassistant", "turn_on"), ("homeassistant", "toggle")],
)
async def test_toggle_and_generic_paths_refused(hass, domain, service):
    entry = await _restricted(hass)
    tablet = await _user(hass, "Tablet")
    assert await async_setup_component(hass, "homeassistant", {})
    with pytest.raises(Unauthorized):
        await hass.services.async_call(
            domain, service, {"entity_id": SUSPEND}, blocking=True, context=_ctx(tablet)
        )
    assert entry.runtime_data.data[ATTR_IS_SUSPENDED] is False


async def test_service_by_config_entry_id_refused(hass):
    entry = await _restricted(hass)
    tablet = await _user(hass, "Tablet")
    with pytest.raises(Unauthorized):
        await hass.services.async_call(
            DOMAIN,
            "extend_time",
            {"config_entry_id": entry.entry_id, "minutes": 30},
            blocking=True,
            context=_ctx(tablet),
        )
    assert entry.runtime_data.data[ATTR_EXTRA_MINUTES_TODAY] == 0


async def test_websocket_call_service_as_tablet_returns_unauthorized(hass, hass_ws_client):
    """Real websocket client authenticated as the tablet user."""
    entry = await _restricted(hass)
    tablet = await _user(hass, "Tablet")
    client = await hass_ws_client(hass, await _issue_token(hass, tablet))
    await client.send_json_auto_id(
        {
            "type": "call_service",
            "domain": "button",
            "service": "press",
            "target": {"entity_id": BUTTON},
        }
    )
    msg = await client.receive_json()
    assert msg["success"] is False
    # QA finding vs. ADR f1d19c22 (4): HA 2026.10.1 maps Unauthorized raised
    # inside a service call to "home_assistant_error" (message "Unauthorized"),
    # not to the "unauthorized" code; the refusal itself holds.
    assert msg["error"]["code"] in ("unauthorized", "home_assistant_error")
    assert msg["error"]["message"] == "Unauthorized"
    assert entry.runtime_data.data[ATTR_EXTRA_MINUTES_TODAY] == 0


async def test_rest_call_service_as_tablet_returns_401(hass, hass_client):
    entry = await _restricted(hass)
    await entry.runtime_data.async_set_blocked(True, context=Context())
    tablet = await _user(hass, "Tablet")
    assert await async_setup_component(hass, "api", {})
    client = await hass_client(await _issue_token(hass, tablet))
    resp = await client.post(
        f"/api/services/{DOMAIN}/set_blocked", json={"person": "Luke", "blocked": False}
    )
    assert resp.status == HTTPStatus.UNAUTHORIZED
    assert entry.runtime_data.data[ATTR_IS_BLOCKED] is True


# --------------------------------------------------------------------------
# A4: no partial effect before the check
# --------------------------------------------------------------------------

REFUSED_CALLS = [
    ("number", "set_value", {"entity_id": NUMBER, "value": 45}),
    ("switch", "turn_on", {"entity_id": SUSPEND}),
    ("switch", "turn_on", {"entity_id": BLOCKED}),
    (DOMAIN, "extend_time", {"person": "Luke", "minutes": 20}),
    (DOMAIN, "set_blocked", {"person": "Luke", "blocked": True}),
    (DOMAIN, "reset_person", {"person": "Luke"}),
]


@pytest.mark.parametrize(("domain", "service", "data"), REFUSED_CALLS)
async def test_refused_call_has_no_side_effect(hass, domain, service, data):
    """No store write, no tick, no state change of any guard entity."""
    entry = await _restricted(hass)
    guard = entry.runtime_data
    tablet = await _user(hass, "Tablet")
    changed: list[str] = []
    hass.bus.async_listen("state_changed", lambda ev: changed.append(ev.data["entity_id"]))
    with (
        patch.object(guard._store, "async_delay_save") as delay_save,
        patch.object(guard._store, "async_save") as save,
        patch.object(guard, "_tick") as tick,
    ):
        with pytest.raises(Unauthorized):
            await hass.services.async_call(
                domain, service, data, blocking=True, context=_ctx(tablet)
            )
        await hass.async_block_till_done()
    delay_save.assert_not_called()
    save.assert_not_called()
    tick.assert_not_called()
    assert changed == []


async def test_refused_button_press_only_touches_button_state(hass):
    """Documented residual risk (b): the button timestamp moves, the guard does not."""
    entry = await _restricted(hass)
    tablet = await _user(hass, "Tablet")
    before = hass.states.get(BUTTON).state
    changed: list[str] = []
    hass.bus.async_listen("state_changed", lambda ev: changed.append(ev.data["entity_id"]))
    with pytest.raises(Unauthorized):
        await hass.services.async_call(
            "button", "press", {"entity_id": BUTTON}, blocking=True, context=_ctx(tablet)
        )
    await hass.async_block_till_done()
    assert set(changed) == {BUTTON}
    assert hass.states.get(BUTTON).state != before
    assert entry.runtime_data.data[ATTR_EXTRA_MINUTES_TODAY] == 0


# --------------------------------------------------------------------------
# A2: forced interleaving - the context is captured before the first await
# --------------------------------------------------------------------------


async def _race(hass, slow_user, fast_user, slow_value, fast_value):
    """Run a slow and a fast number.set_value; the fast one overwrites the
    entity's _context while the slow one is inside the permission check."""
    reached = asyncio.Event()
    gate = asyncio.Event()
    original = hass.auth.async_get_user

    lookups: list[str] = []

    async def slow_get_user(user_id):
        # HA's service layer looks the user up once before the entity method
        # runs (no context set yet); stall the slow caller's *second* lookup,
        # i.e. the one after the entity received its context.
        lookups.append(user_id)
        if user_id == slow_user.id and lookups.count(user_id) == 2:
            reached.set()
            await gate.wait()
        return await original(user_id)

    async def call(user, value):
        await hass.services.async_call(
            "number",
            "set_value",
            {"entity_id": NUMBER, "value": value},
            blocking=True,
            context=_ctx(user),
        )

    with patch.object(hass.auth, "async_get_user", slow_get_user):
        slow = asyncio.ensure_future(call(slow_user, slow_value))
        await asyncio.wait_for(reached.wait(), 2)
        fast_error: BaseException | None = None
        try:
            await call(fast_user, fast_value)
        except Unauthorized as err:
            fast_error = err
        # Proof the race happened: the entity now carries the fast caller's context.
        assert _entity(hass, "number", NUMBER)._context.user_id == fast_user.id
        gate.set()
        slow_result = await asyncio.gather(slow, return_exceptions=True)
    return slow_result[0], fast_error


async def test_race_slow_tablet_fast_admin(hass):
    entry = await _restricted(hass)
    tablet = await _user(hass, "Tablet")
    admin = await _user(hass, "Mum", admin=True)
    slow_result, fast_error = await _race(hass, tablet, admin, 99, 30)
    assert isinstance(slow_result, Unauthorized)
    assert slow_result.user_id == tablet.id
    assert fast_error is None
    assert entry.runtime_data.data[ATTR_EXTRA_MINUTES_TODAY] == 30


async def test_race_slow_admin_fast_tablet(hass):
    entry = await _restricted(hass)
    tablet = await _user(hass, "Tablet")
    admin = await _user(hass, "Mum", admin=True)
    slow_result, fast_error = await _race(hass, admin, tablet, 30, 99)
    assert slow_result is None
    assert isinstance(fast_error, Unauthorized)
    assert entry.runtime_data.data[ATTR_EXTRA_MINUTES_TODAY] == 30


# --------------------------------------------------------------------------
# Reload / restart
# --------------------------------------------------------------------------


async def test_restriction_and_block_survive_reload(hass):
    entry = await _restricted(hass)
    tablet = await _user(hass, "Tablet")
    admin = await _user(hass, "Mum", admin=True)
    await hass.services.async_call(
        "switch", "turn_on", {"entity_id": BLOCKED}, blocking=True, context=_ctx(admin)
    )
    old_guard = entry.runtime_data

    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.runtime_data is not old_guard
    assert entry.runtime_data.data[ATTR_IS_BLOCKED] is True
    with pytest.raises(Unauthorized):
        await hass.services.async_call(
            "switch", "turn_off", {"entity_id": BLOCKED}, blocking=True, context=_ctx(tablet)
        )
    assert entry.runtime_data.data[ATTR_IS_BLOCKED] is True


async def test_restriction_survives_unload_and_setup(hass):
    """Restart-like cycle: unload (final save) + fresh setup from the store."""
    entry = await _restricted(hass)
    tablet = await _user(hass, "Tablet")
    await entry.runtime_data.async_set_extra_minutes(25, context=Context())
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.runtime_data.data[ATTR_EXTRA_MINUTES_TODAY] == 25
    with pytest.raises(Unauthorized):
        await hass.services.async_call(
            "number",
            "set_value",
            {"entity_id": NUMBER, "value": 0},
            blocking=True,
            context=_ctx(tablet),
        )
    assert entry.runtime_data.data[ATTR_EXTRA_MINUTES_TODAY] == 25


async def test_options_change_applies_after_reload(hass):
    """Turning the restriction off/on and removing an allowed user take effect."""
    nanny = await _user(hass, "Nanny")
    tablet = await _user(hass, "Tablet")
    entry = await _restricted(hass, allowed=[nanny.id])
    await entry.runtime_data.async_extend_time(5, context=_ctx(nanny))

    hass.config_entries.async_update_entry(
        entry, options={**entry.options, CONF_RESTRICT_CHANGES: False}
    )
    await hass.async_block_till_done()
    await entry.runtime_data.async_extend_time(5, context=_ctx(tablet))

    hass.config_entries.async_update_entry(
        entry, options={**entry.options, CONF_RESTRICT_CHANGES: True, CONF_ALLOWED_USERS: []}
    )
    await hass.async_block_till_done()
    for who in (tablet, nanny):
        with pytest.raises(Unauthorized):
            await entry.runtime_data.async_extend_time(5, context=_ctx(who))
    assert entry.runtime_data.data[ATTR_EXTRA_MINUTES_TODAY] == 10


# --------------------------------------------------------------------------
# Entries without the new keys / keys only in data (A6: 1.3.0 behaviour)
# --------------------------------------------------------------------------


async def _old_entry(hass, *, data_extra=None, options=None) -> MockConfigEntry:
    data = {**build_entry_data(), **(data_extra or {})}
    entry = MockConfigEntry(
        domain=DOMAIN, title="Luke", data=data, options=options or {}, unique_id=f"{DOMAIN}_luke"
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_old_entry_with_130_options_behaves_like_130(hass):
    """1.3.0 options (no access keys) -> everyone may change, nothing raises."""
    entry = await _old_entry(hass, options={CONF_RESET_TIME: "00:00:00"})
    tablet = await _user(hass, "Tablet")
    for domain, service, data in [
        ("button", "press", {"entity_id": BUTTON}),
        ("switch", "turn_on", {"entity_id": BLOCKED}),
        (DOMAIN, "reset_person", {"person": "Luke"}),
    ]:
        await hass.services.async_call(domain, service, data, blocking=True, context=_ctx(tablet))
    assert entry.runtime_data.data[ATTR_IS_BLOCKED] is True
    assert entry.runtime_data.restrict_changes is False
    assert entry.runtime_data.allowed_users == frozenset()


async def test_restriction_off_ignores_unknown_user(hass):
    entry = await setup_person(hass)
    await entry.runtime_data.async_extend_time(5, context=Context(user_id="nonexistent"))
    assert entry.runtime_data.data[ATTR_EXTRA_MINUTES_TODAY] == 5


async def test_keys_only_in_data_are_honoured(hass):
    """Entry created by the 1.4.0 config flow (keys in data, no options yet)."""
    entry = await _old_entry(hass, data_extra={CONF_RESTRICT_CHANGES: True, CONF_ALLOWED_USERS: []})
    tablet = await _user(hass, "Tablet")
    with pytest.raises(Unauthorized):
        await entry.runtime_data.async_extend_time(5, context=_ctx(tablet))


async def test_old_entry_options_flow_enables_restriction(hass):
    """Old entry -> options flow shows defaults off/[], enabling it really refuses."""
    entry = await _old_entry(hass)
    tablet = await _user(hass, "Tablet")
    flow = hass.config_entries.options
    result = await flow.async_init(entry.entry_id)
    result = await flow.async_configure(
        result["flow_id"], {CONF_NAME: "Luke", CONF_PLAYERS: [PLAYER]}
    )
    result = await flow.async_configure(result["flow_id"], {f"budget_{i}": 60 for i in range(7)})
    result = await flow.async_configure(
        result["flow_id"],
        {
            CONF_WARNING_ENABLED: False,
            CONF_WARNING_THRESHOLD: 5,
            CONF_WARNING_METHOD: WARNING_METHOD_TTS,
        },
    )
    result = await flow.async_configure(result["flow_id"], {CONF_RESET_TIME: "00:00:00"})
    assert result["step_id"] == "access"
    defaults = {str(m): m.default() for m in result["data_schema"].schema}
    assert defaults[CONF_RESTRICT_CHANGES] is False
    assert defaults[CONF_ALLOWED_USERS] == []

    await flow.async_configure(result["flow_id"], {CONF_RESTRICT_CHANGES: True})
    await hass.async_block_till_done()
    assert entry.options[CONF_RESTRICT_CHANGES] is True
    with pytest.raises(Unauthorized):
        await hass.services.async_call(
            "button", "press", {"entity_id": BUTTON}, blocking=True, context=_ctx(tablet)
        )
    assert entry.runtime_data.data[ATTR_EXTRA_MINUTES_TODAY] == 0


# --------------------------------------------------------------------------
# Scope: per person, inactive admin, multi-entity calls, diagnostics
# --------------------------------------------------------------------------


async def test_allow_list_is_per_person(hass):
    nanny = await _user(hass, "Nanny")
    luke = await _restricted(hass, allowed=[nanny.id])
    leia = await _restricted(hass, name="Leia", players=[LEIA_PLAYER])
    await luke.runtime_data.async_extend_time(5, context=_ctx(nanny))
    with pytest.raises(Unauthorized):
        await leia.runtime_data.async_extend_time(5, context=_ctx(nanny))
    assert luke.runtime_data.data[ATTR_EXTRA_MINUTES_TODAY] == 5
    assert leia.runtime_data.data[ATTR_EXTRA_MINUTES_TODAY] == 0


async def test_multi_entity_call_refuses_only_restricted_person(hass):
    luke = await _restricted(hass)
    leia = await setup_person(hass, name="Leia", players=[LEIA_PLAYER])
    tablet = await _user(hass, "Tablet")
    with pytest.raises(Unauthorized):
        await hass.services.async_call(
            "switch",
            "turn_on",
            {"entity_id": [SUSPEND, LEIA_SUSPEND]},
            blocking=True,
            context=_ctx(tablet),
        )
    await hass.async_block_till_done()
    assert luke.runtime_data.data[ATTR_IS_SUSPENDED] is False
    assert leia.runtime_data.data[ATTR_IS_SUSPENDED] is True


async def test_inactive_admin_refused(hass):
    admin = await _user(hass, "Ex-Admin", admin=True, active=False)
    entry = await _restricted(hass)
    with pytest.raises(Unauthorized):
        await entry.runtime_data.async_set_blocked(True, context=_ctx(admin))
    assert entry.runtime_data.data[ATTR_IS_BLOCKED] is False


async def test_owner_allowed(hass, hass_owner_user):
    entry = await _restricted(hass)
    await entry.runtime_data.async_set_blocked(True, context=_ctx(hass_owner_user))
    assert entry.runtime_data.data[ATTR_IS_BLOCKED] is True


async def test_diagnostics_show_flag_but_not_user_ids(hass, hass_client):
    nanny = await _user(hass, "Nanny")
    entry = await _restricted(hass, allowed=[nanny.id])
    diag = await get_diagnostics_for_config_entry(hass, hass_client, entry)
    assert diag["entry"]["options"][CONF_RESTRICT_CHANGES] is True
    assert nanny.id not in str(diag)
