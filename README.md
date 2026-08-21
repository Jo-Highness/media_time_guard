> 🇬🇧 English (this page) · 🇩🇪 [Deutsch](README.de.md) · 🇪🇸 [Español](README.es.md)

<p align="center">
  <img src="icon.png" alt="Media Time Guard" width="160" height="160">
</p>

<h1 align="center">Media Time Guard</h1>

<p align="center">
  <b>Screen &amp; speaker time for kids — set it once, and it just holds.</b>
</p>

<p align="center">
  <a href="https://github.com/hacs/integration"><img src="https://img.shields.io/badge/HACS-Custom-41BDF5.svg" alt="HACS Custom"></a>
  <a href="https://github.com/Jo-Highness/media_time_guard/actions/workflows/validate.yml"><img src="https://github.com/Jo-Highness/media_time_guard/actions/workflows/validate.yml/badge.svg" alt="Validate"></a>
  <a href="https://github.com/Jo-Highness/media_time_guard/actions/workflows/test.yml"><img src="https://github.com/Jo-Highness/media_time_guard/actions/workflows/test.yml/badge.svg" alt="Tests"></a>
  <a href="https://github.com/Jo-Highness/media_time_guard/releases"><img src="https://img.shields.io/github/v/release/Jo-Highness/media_time_guard" alt="Release"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green.svg" alt="MIT"></a>
  <img src="https://img.shields.io/badge/Home%20Assistant-2024.1%2B-41BDF5.svg" alt="Home Assistant 2024.1+">
</p>

Every parent knows the scene: *"Just five more minutes!"* — for the third time.
**Media Time Guard** gives every child a **daily media-time budget** and enforces it
**automatically and tamper-resistantly** across your Sonos and any other Home Assistant
`media_player`. No nagging, no timers on your phone, no loopholes. When the budget is up,
the music stops — and turning the speaker off and on again won't buy more time.

## Why this exists

- ⏱️ **A budget per weekday** – short on school days, generous on weekends (`0` = blocked that day).
- 🛡️ **Genuinely tamper-resistant** – counts real wall-clock playback and survives restarts, power cuts and off/on tricks.
- 🔀 **No double counting** – the same child on several speakers still spends time only once.
- 🔔 **A fair heads-up** – a friendly **TTS announcement** ("10 minutes left…") or your own sound just before time's up.
- ➕ **Easy to reward** – extra minutes via buttons (+15/+30), a slider, or a service call.
- 🤒 **Exceptions** – child is ill? Suspend enforcement for today with one switch.
- 🌍 **Multilingual** – UI **and entities** in English, German, Spanish, French, Norwegian, Greek and Japanese.
- 🧩 **100 % UI-configured, fully local** – no YAML, no automations required, no cloud.

One config entry per child: bind it to a `person` entity (or simply enter a name) and assign
that person's `media_player` entities. The integration counts media time on those players
and, once the day's budget is used up, keeps the assigned players stopped.

## Installation

### HACS (recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Jo-Highness&repository=media_time_guard&category=integration)

1. In **HACS** open **⋮ → Custom repositories** and add `https://github.com/Jo-Highness/media_time_guard` as category **Integration** (skip this step once the integration is in the default store — just use the button above).
2. Search for **Media Time Guard** in HACS and **download** it.
3. **Restart** Home Assistant.
4. Go to **Settings → Devices & Services → Add Integration** and pick **Media Time Guard**.

### Manual

1. Copy `custom_components/media_time_guard/` into your `<config>/custom_components/` folder.
2. **Restart** Home Assistant.
3. Add the integration from **Settings → Devices & Services**.

## Configuration

Setup and later editing use the same four config-flow steps. Everything is editable afterwards
via **Configure** (Options). Add one integration entry **per child**.

| Step | What you set |
|---|---|
| **1 · Person** | A **name** (e.g. `Luke`), an optional **`person` entity**, and the assigned **media players**. Each player can belong to only one person. |
| **2 · Daily budgets** | Minutes for each weekday **Mon–Sun**. `0` blocks media entirely that day. |
| **3 · Warning** | Enable/disable the one-time warning, its **remaining-minutes threshold** (default `10`), and the **method**: either a **TTS** announcement (choose a TTS engine + a message, where `{minutes}` is substituted) **or** playing a **media** content id (with content type). |
| **4 · Reset** | The daily **reset time** (default `00:00:00`) at which counters and the one-time warning clear. |

## Entities

Each configured person gets its own **device** with these entities (`<person>` = the name slug):

| Entity | Type | Purpose |
|---|---|---|
| `sensor.media_time_<person>_remaining` | sensor (measurement, minutes) | Remaining media minutes today, with rich attributes (budget, used, weekday, locked/suspended, extra minutes, last reset). |
| `switch.media_time_<person>_suspend_today` | switch | **Suspend today** — pause enforcement for the rest of the day (e.g. the child is ill). |
| `number.media_time_<person>_extend` | number (0–600, step 5) | **Extra minutes** added to today's budget. |
| `button.media_time_<person>_extend_15` | button | Quick-add **+15 minutes**. |
| `button.media_time_<person>_extend_30` | button | Quick-add **+30 minutes**. |

## Services

All services take the person's **name or slug**.

| Service | Fields | Description |
|---|---|---|
| `media_time_guard.extend_time` | `person`, `minutes` (1–600) | Add extra media minutes for today (raises the effective budget). |
| `media_time_guard.suspend_today` | `person`, `suspended` (bool) | Suspend or resume enforcement for today. |
| `media_time_guard.reset_person` | `person` | Manually reset today's counters for a person. |

## Automation examples

**Reward 15 minutes when homework is done:**

```yaml
automation:
  - alias: "Media reward when homework done"
    trigger:
      - platform: state
        entity_id: input_boolean.luke_homework_done
        to: "on"
    action:
      - service: media_time_guard.extend_time
        data:
          person: Luke
          minutes: 15
```

**Suspend enforcement automatically on a sick day:**

```yaml
automation:
  - alias: "Suspend media limit when sick"
    trigger:
      - platform: state
        entity_id: input_boolean.luke_sick
        to: "on"
    action:
      - service: media_time_guard.suspend_today
        data:
          person: Luke
          suspended: true
```

**Notify your phone when the daily budget is used up:**

```yaml
automation:
  - alias: "Notify when media time is up"
    trigger:
      - platform: numeric_state
        entity_id: sensor.media_time_luke_remaining
        below: 1
    action:
      - service: notify.mobile_app_parent
        data:
          message: "Luke's media time for today is used up."
```

## Troubleshooting / FAQ

**Playback doesn't stop when the budget is empty.**
Make sure the child's `media_player` entities are actually assigned to that person in the
config flow and that the current weekday's budget isn't set to a huge value. Remember that
`0` means "blocked all day".

**Time counts even though nothing is (audibly) playing.**
Counting is based on the player's `playing` state, so muted or very quiet playback still
counts. This is intentional and keeps enforcement tamper-resistant.

**The same child uses two speakers — is time counted twice?**
No. Media time for a person is counted once, no matter how many of their assigned players
are playing simultaneously.

**A player can't be assigned to a second child.**
That's by design: each `media_player` belongs to exactly one person to keep the accounting
unambiguous.

**The warning never plays.**
Check the warning step: for the **TTS** method a TTS engine is required; for the **Media**
method a media content id is required. The warning fires once per day, at the configured
remaining-minutes threshold.

**Enable debug logging** to see how time is counted and enforced:

```yaml
logger:
  logs:
    custom_components.media_time_guard: debug
```

More detail: full user guides in [`docs/user/`](docs/user) (de, en, es, fr, nb, el, ja) and
the architecture write-up in [`docs/TECHNICAL.md`](docs/TECHNICAL.md).

## Contributing

Contributions are welcome. Please read [`CONTRIBUTING.md`](CONTRIBUTING.md) and open an issue
or pull request on [GitHub](https://github.com/Jo-Highness/media_time_guard).

## License

Released under the [MIT License](LICENSE).

## Credits

Created and maintained by [@Jo-Highness](https://github.com/Jo-Highness).
Built as a custom [Home Assistant](https://www.home-assistant.io/) integration for
[HACS](https://hacs.xyz/).
