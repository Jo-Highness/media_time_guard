"""Config and options flow for Media Time Guard."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import selector
import voluptuous as vol

from .const import (
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
    DEFAULT_DAILY_MINUTES,
    DEFAULT_RESET_TIME,
    DEFAULT_WARNING_MEDIA_TYPE,
    DEFAULT_WARNING_THRESHOLD,
    DOMAIN,
    WARNING_METHOD_MEDIA,
    WARNING_METHOD_TTS,
    WEEKDAYS,
    default_tts_message,
)

# Keys owned by each step. When a step is submitted these keys are dropped
# first and then re-filled from the user input, so optional fields that the
# user cleared really disappear (instead of keeping their old value).
# CONF_PERSON_ENTITY is a legacy key (<= 1.1.x) that is dropped on edit.
USER_STEP_KEYS = (CONF_NAME, CONF_PLAYERS, CONF_PERSON_ENTITY)
WARNING_STEP_KEYS = (
    CONF_WARNING_ENABLED,
    CONF_WARNING_THRESHOLD,
    CONF_WARNING_METHOD,
    CONF_TTS_ENTITY,
    CONF_TTS_MESSAGE,
    CONF_WARNING_MEDIA_ID,
    CONF_WARNING_MEDIA_TYPE,
)
RESET_STEP_KEYS = (CONF_RESET_TIME,)

# Shown literally in the labels/help texts of the warning step.
WARNING_PLACEHOLDERS = {"minutes": "{minutes}"}

BUDGET_FIELD_PREFIX = "budget_"


def _budget_field(index: int) -> str:
    return f"{BUDGET_FIELD_PREFIX}{index}"


def _apply_step(data: dict[str, Any], user_input: dict[str, Any], keys: tuple[str, ...]) -> None:
    """Replace the keys owned by a step with the submitted values."""
    for key in keys:
        data.pop(key, None)
    for key, value in user_input.items():
        if value is None or value == "":
            continue
        data[key] = value.strip() if key == CONF_NAME and isinstance(value, str) else value


def _name_in_use(hass: HomeAssistant, name: str, exclude_entry_id: str | None = None) -> bool:
    """Return True if another entry already uses ``name`` (case-insensitive)."""
    needle = name.strip().casefold()
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.entry_id == exclude_entry_id:
            continue
        merged = {**entry.data, **entry.options}
        names = {str(merged.get(CONF_NAME, "")).strip().casefold(), entry.title.casefold()}
        if needle in names:
            return True
    return False


def _players_in_use(hass: HomeAssistant, exclude_entry_id: str | None = None) -> set[str]:
    """Collect media players already assigned to other persons."""
    used: set[str] = set()
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.entry_id == exclude_entry_id:
            continue
        merged = {**entry.data, **entry.options}
        used.update(merged.get(CONF_PLAYERS, []))
    return used


def _user_schema(defaults: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=defaults.get(CONF_NAME, "")): (selector.TextSelector()),
            vol.Required(
                CONF_PLAYERS, default=defaults.get(CONF_PLAYERS, [])
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="media_player", multiple=True)
            ),
        }
    )


def _budgets_schema(defaults: dict[str, int]) -> vol.Schema:
    fields: dict[Any, Any] = {}
    for index in WEEKDAYS:
        i = int(index)
        default = defaults.get(index, DEFAULT_DAILY_MINUTES)
        fields[vol.Required(_budget_field(i), default=default)] = selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=0, max=1440, step=5, mode="box", unit_of_measurement="min"
            )
        )
    return vol.Schema(fields)


def _warning_schema(defaults: dict[str, Any]) -> vol.Schema:
    # Optional fields use suggested values (not defaults) so they can be cleared.
    return vol.Schema(
        {
            vol.Required(
                CONF_WARNING_ENABLED,
                default=defaults.get(CONF_WARNING_ENABLED, False),
            ): selector.BooleanSelector(),
            vol.Required(
                CONF_WARNING_THRESHOLD,
                default=defaults.get(CONF_WARNING_THRESHOLD, DEFAULT_WARNING_THRESHOLD),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=1, max=120, step=1, mode="box", unit_of_measurement="min"
                )
            ),
            vol.Required(
                CONF_WARNING_METHOD,
                default=defaults.get(CONF_WARNING_METHOD, WARNING_METHOD_TTS),
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[WARNING_METHOD_TTS, WARNING_METHOD_MEDIA],
                    translation_key="warning_method",
                    mode="dropdown",
                )
            ),
            vol.Optional(
                CONF_TTS_ENTITY,
                description={"suggested_value": defaults.get(CONF_TTS_ENTITY)},
            ): selector.EntitySelector(selector.EntitySelectorConfig(domain="tts")),
            vol.Optional(
                CONF_TTS_MESSAGE,
                description={"suggested_value": defaults.get(CONF_TTS_MESSAGE)},
            ): selector.TextSelector(selector.TextSelectorConfig(multiline=True)),
            vol.Optional(
                CONF_WARNING_MEDIA_ID,
                description={"suggested_value": defaults.get(CONF_WARNING_MEDIA_ID)},
            ): selector.TextSelector(),
            vol.Optional(
                CONF_WARNING_MEDIA_TYPE,
                description={"suggested_value": defaults.get(CONF_WARNING_MEDIA_TYPE)},
            ): selector.TextSelector(),
        }
    )


def _reset_schema(defaults: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(
                CONF_RESET_TIME,
                default=defaults.get(CONF_RESET_TIME, DEFAULT_RESET_TIME),
            ): selector.TimeSelector(),
        }
    )


def _validate_warning(data: dict[str, Any]) -> dict[str, str]:
    """Return form errors for the warning step."""
    errors: dict[str, str] = {}
    if not data.get(CONF_WARNING_ENABLED):
        return errors
    method = data.get(CONF_WARNING_METHOD, WARNING_METHOD_TTS)
    if method == WARNING_METHOD_TTS and not data.get(CONF_TTS_ENTITY):
        errors["base"] = "tts_entity_required"
    if method == WARNING_METHOD_MEDIA and not data.get(CONF_WARNING_MEDIA_ID):
        errors["base"] = "media_id_required"
    return errors


def _collect_budgets(user_input: dict[str, Any]) -> dict[str, int]:
    return {index: int(user_input[_budget_field(int(index))]) for index in WEEKDAYS}


class MediaTimeGuardConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the initial configuration of a person."""

    VERSION = 1

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            name = user_input[CONF_NAME].strip()
            used = _players_in_use(self.hass)
            if not name:
                errors["base"] = "name_required"
            elif set(user_input[CONF_PLAYERS]) & used:
                errors["base"] = "player_in_use"
            elif not user_input[CONF_PLAYERS]:
                errors["base"] = "no_players"
            else:
                if _name_in_use(self.hass, name):
                    return self.async_abort(reason="already_configured")
                unique_id = f"{DOMAIN}_{name.casefold()}"
                if self.hass.config_entries.async_entry_for_domain_unique_id(DOMAIN, unique_id):
                    # The unique_id is never changed on rename, so a renamed
                    # person can still hold the id derived from this name.
                    unique_id = f"{unique_id}_{uuid4().hex[:8]}"
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()
                _apply_step(self._data, user_input, USER_STEP_KEYS)
                return await self.async_step_budgets()
        return self.async_show_form(
            step_id="user", data_schema=_user_schema(self._data), errors=errors
        )

    async def async_step_budgets(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            self._data[CONF_BUDGETS] = _collect_budgets(user_input)
            return await self.async_step_warning()
        return self.async_show_form(
            step_id="budgets",
            data_schema=_budgets_schema(self._data.get(CONF_BUDGETS, {})),
        )

    async def async_step_warning(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            errors = _validate_warning(user_input)
            if not errors:
                _apply_step(self._data, user_input, WARNING_STEP_KEYS)
                return await self.async_step_reset()
        defaults = {
            CONF_TTS_MESSAGE: default_tts_message(self.hass.config.language),
            CONF_WARNING_MEDIA_TYPE: DEFAULT_WARNING_MEDIA_TYPE,
            **self._data,
        }
        return self.async_show_form(
            step_id="warning",
            data_schema=_warning_schema(defaults),
            errors=errors,
            description_placeholders=WARNING_PLACEHOLDERS,
        )

    async def async_step_reset(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            _apply_step(self._data, user_input, RESET_STEP_KEYS)
            return self.async_create_entry(title=self._data[CONF_NAME], data=dict(self._data))
        return self.async_show_form(step_id="reset", data_schema=_reset_schema(self._data))

    @staticmethod
    @callback
    def async_get_options_flow(entry: ConfigEntry) -> MediaTimeGuardOptionsFlow:
        return MediaTimeGuardOptionsFlow()


class MediaTimeGuardOptionsFlow(OptionsFlow):
    """Allow editing every setting of an existing person."""

    _data: dict[str, Any]

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        entry = self.config_entry
        if not hasattr(self, "_data"):
            self._data = {**entry.data, **entry.options}
        errors: dict[str, str] = {}
        if user_input is not None:
            name = user_input[CONF_NAME].strip()
            used = _players_in_use(self.hass, exclude_entry_id=entry.entry_id)
            if not name:
                errors["base"] = "name_required"
            elif _name_in_use(self.hass, name, exclude_entry_id=entry.entry_id):
                errors["base"] = "name_in_use"
            elif set(user_input[CONF_PLAYERS]) & used:
                errors["base"] = "player_in_use"
            elif not user_input[CONF_PLAYERS]:
                errors["base"] = "no_players"
            else:
                _apply_step(self._data, user_input, USER_STEP_KEYS)
                return await self.async_step_budgets()
        return self.async_show_form(
            step_id="init", data_schema=_user_schema(self._data), errors=errors
        )

    async def async_step_budgets(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            self._data[CONF_BUDGETS] = _collect_budgets(user_input)
            return await self.async_step_warning()
        return self.async_show_form(
            step_id="budgets",
            data_schema=_budgets_schema(self._data.get(CONF_BUDGETS, {})),
        )

    async def async_step_warning(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            errors = _validate_warning(user_input)
            if not errors:
                _apply_step(self._data, user_input, WARNING_STEP_KEYS)
                return await self.async_step_reset()
        return self.async_show_form(
            step_id="warning",
            data_schema=_warning_schema(self._data),
            errors=errors,
            description_placeholders=WARNING_PLACEHOLDERS,
        )

    async def async_step_reset(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            _apply_step(self._data, user_input, RESET_STEP_KEYS)
            # Keep the entry title in sync with the (possibly renamed) person so
            # the UI and name-based service calls match. Title and options are
            # written in one update -> exactly one reload. The unique_id stays.
            self.hass.config_entries.async_update_entry(
                self.config_entry, title=self._data[CONF_NAME], options=dict(self._data)
            )
            return self.async_create_entry(data=dict(self._data))
        return self.async_show_form(step_id="reset", data_schema=_reset_schema(self._data))
