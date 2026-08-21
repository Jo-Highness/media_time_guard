# Contributing to Media Time Guard

Thanks for your interest in improving **Media Time Guard**! This is a custom
[Home Assistant](https://www.home-assistant.io/) integration distributed through
[HACS](https://hacs.xyz/). Contributions of all kinds — bug reports, fixes,
features, translations and documentation — are welcome.

## Repository layout

```
media_time_guard/
├─ custom_components/media_time_guard/   # the integration
│  ├─ __init__.py                        # setup / unload
│  ├─ config_flow.py                     # UI configuration flow
│  ├─ coordinator.py                     # budget accounting logic
│  ├─ entity.py                          # base entity
│  ├─ sensor.py / switch.py / number.py / button.py
│  ├─ const.py
│  ├─ services.yaml                      # service definitions
│  ├─ strings.json                       # source UI strings (English)
│  ├─ translations/                      # de, en, es, fr, nb, el, ja
│  └─ brand/                             # local brand images (HA 2026.3+)
├─ tests/                                # pytest suite
├─ docs/                                 # additional documentation
├─ README.md                            # multilingual (DE / EN / ES)
└─ hacs.json / manifest.json
```

## Development environment

Create a virtual environment and install the tooling:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install ruff pytest pytest-homeassistant-custom-component
```

## Linting and formatting

We use [ruff](https://docs.astral.sh/ruff/) for both linting and formatting:

```bash
ruff check .
ruff format --check .
```

Run `ruff check --fix .` and `ruff format .` to apply fixes automatically.

## Tests

```bash
pytest
```

The test suite is built on
[`pytest-homeassistant-custom-component`](https://github.com/MatthewFlamm/pytest-homeassistant-custom-component).
Please add or update tests for any behavioural change and make sure the suite is
green before opening a pull request.

## Translations

The integration is multilingual:

- **UI strings** live in `custom_components/media_time_guard/translations/`
  (`de`, `en`, `es`, `fr`, `nb`, `el`, `ja`).
- The English source of truth is `custom_components/media_time_guard/strings.json`.

When you add a new user-facing string, add it to `strings.json` **and** to every
language file under `translations/`. Keep the key structure identical across all
files. Entity names are translatable too — follow the existing `entity` blocks.

## Commit messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add per-weekday bonus scheduling
fix: prevent double counting on grouped players
docs: clarify sick-day override
chore: bump dev dependencies
```

Common types: `feat`, `fix`, `docs`, `chore`, `ci`, `refactor`, `test`.
These prefixes drive the automatic release notes and version resolution.

## Pull request process

1. Fork the repository and create a feature branch off `main`.
2. Make your change; keep it focused and small where possible.
3. Run `ruff check .`, `ruff format --check .` and `pytest` — all must pass.
4. Update `CHANGELOG.md` under `## [Unreleased]`.
5. Update documentation (`README.md` and its language sections) and translations
   where relevant.
6. Open a pull request against `main` and fill in the pull request template.

A maintainer will review your change. Thank you for contributing!
