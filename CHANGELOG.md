# Changelog

All notable changes to **Media Time Guard** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/Jo-Highness/media_time_guard/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/Jo-Highness/media_time_guard/compare/v1.0.1...v1.1.0
[1.0.1]: https://github.com/Jo-Highness/media_time_guard/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/Jo-Highness/media_time_guard/releases/tag/v1.0.0
