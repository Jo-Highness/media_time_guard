# Changelog

All notable changes to **Media Time Guard** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.3.0] - 2026-10-27

### Added

- **Permanent block per person:** new switch `switch.media_time_<person>_blocked` ("Blocked" /
  "Gesperrt") and action `media_time_guard.set_blocked` (`person` / `config_entry_id`, `blocked`).
  While on, every playback on the person's players is stopped right away, regardless of the
  remaining time. It takes precedence over *Suspend today* and extra minutes, counts no media time,
  sends no warning, leaves `is_locked` untouched and survives the daily reset, `reset_person` and
  restarts (saved immediately). Only switching it off ends it; afterwards the normal daily logic
  applies again.
- `is_blocked` attribute on the remaining-time sensor and in diagnostics.

### Fixed

- hassfest: English action error messages no longer wrap placeholders in single quotes
  (`strings.json`, `en.json`); the current hassfest rejects that.

## [1.2.0] - 2026-10-16

> **Upgrade notes:** minimum Home Assistant version is now **2025.2.0**. Existing entities keep
> their entity IDs. Existing entries keep their stored announcement text; the language-dependent
> default only applies to new entries or when the text is cleared.

### Fixed

- An active lock is now lifted whenever the budget is no longer exhausted — also after the
  weekday budget was raised in the options (previously the lock restored after the reload
  stayed until the next day). Only extra minutes lifted it before.
- The one-time warning is re-armed when extra minutes push the remaining time above the
  threshold again, so it plays once more before the new end.
- Options flow: optional fields (TTS engine, text, media ID/type) can be cleared; previously the
  old values were kept.
- Options flow: renaming a person now updates the entry title, refuses names used by another
  person and keeps the entry's unique ID. Actions also match the entry title, and a new entry
  can reuse a name that was freed by a rename.
- `media_stop`, `play_media` and `tts.speak` calls run as config-entry background tasks and
  failures are logged instead of being lost in fire-and-forget tasks.
- The guard was shut down twice on unload (state saved twice).

### Added

- Optional `config_entry_id` field for all actions (stays valid after a rename); `person` is now
  optional, one of both is required.
- Repair issue when an assigned media player or the TTS entity no longer exists.
- Diagnostics download (names, entity IDs and texts redacted).
- Help texts in the setup/options forms.

### Changed

- Removed the unused "Person entity (optional)" field from setup and options (it was never used
  by the logic; entries that contain it keep working).
- The default TTS announcement follows the Home Assistant UI language (de, el, en, es, fr, ja,
  nb; English otherwise) instead of always German.
- Remaining-time sensor and extra-minutes number use the `duration` device class; device is a
  service device; icons moved to `icons.json`.
- Modernised internals: `entry.runtime_data`, actions registered in `async_setup` with
  translated errors, `Platform` enum, `AddConfigEntryEntitiesCallback`, options flow without
  custom `__init__`.
- Docs: quick start, modern automation syntax, example dashboard card, which player states
  count and what the integration cannot control, entity-ID behaviour on renames; German and
  Spanish READMEs synced with the English one.

### CI

- Test requirements pinned (`pytest-homeassistant-custom-component==0.13.316`), coverage
  report, Ruff target `py313`, Dependabot for pip.

## [1.1.2] - 2026-10-09

> **Note:** this patch release raises the minimum Home Assistant version to **2024.11.0** (see Fixed). Older versions could not set up the integration anyway.

### Fixed

- `hacs.json` declared Home Assistant 2024.1.0 as minimum, but the integration uses
  `ConfigFlowResult` (2024.4) and `DataUpdateCoordinator(config_entry=...)` (2024.11) and
  fails to set up on older versions. Minimum raised to **2024.11.0** (README badge updated).
- `extend_time` now rejects more than 600 minutes per call (same limit as the service UI
  and the extra-minutes number entity) instead of accepting unbounded values.
- The guard's `async_shutdown` now also stops the base coordinator's periodic poll.

## [1.1.1] - 2026-08-21

### Added
- Continuous integration: `Validate` (HACS + hassfest) and `Test` (ruff + pytest) GitHub Actions workflows.
- Ruff configuration for linting and formatting.
- Completed entity-name translations for Greek (`el`), Japanese (`ja`) and Norwegian Bokmål (`nb`).
- Repository meta files: `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`, issue templates, pull request template, Dependabot config and Release Drafter.

### Changed
- Sorted the `manifest.json` keys to satisfy hassfest.

## [1.1.0] - 2026-07-29

### Added
- Translatable entity names — the person/player entities now follow the Home Assistant UI language.
- Multilingual README (German, English, Spanish) and full interface localisation (DE, EN, ES, FR, NB, EL, JA).

## [1.0.1] - 2026-05-31

### Added
- Integration icon (SVG plus 256/512 PNG) embedded in the README.
- Local brand images shipped via the `brand/` directory, served through the HA 2026.3+ proxy API (no `home-assistant/brands` PR required).

## [1.0.0] - 2026-05-29

### Added
- Initial release of Media Time Guard — a per-child daily media-time budget enforcer for Home Assistant.
- Per-weekday budgets, tamper-resistant wall-clock accounting that survives restarts, and no double-counting across multiple players.
- TTS pre-warning, bonus minutes (button/slider/service) and a per-day "sick day" override switch.
- Full config-flow setup (no YAML), coordinator, and test suite (passing on HA 2026.2).

[Unreleased]: https://github.com/Jo-Highness/media_time_guard/compare/v1.3.0...HEAD
[1.3.0]: https://github.com/Jo-Highness/media_time_guard/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/Jo-Highness/media_time_guard/compare/v1.1.2...v1.2.0
[1.1.2]: https://github.com/Jo-Highness/media_time_guard/compare/v1.1.1...v1.1.2
[1.1.1]: https://github.com/Jo-Highness/media_time_guard/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/Jo-Highness/media_time_guard/compare/v1.0.1...v1.1.0
[1.0.1]: https://github.com/Jo-Highness/media_time_guard/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/Jo-Highness/media_time_guard/releases/tag/v1.0.0
