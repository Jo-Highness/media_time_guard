> 🇬🇧 English (this page) · 🇩🇪 [Deutsch](README.de.md) · 🇪🇸 [Español](README.es.md)

<p align="center">
  <img src="icon.png" alt="Media Time Guard" width="160" height="160">
</p>

<h1 align="center">Media Time Guard</h1>

<p align="center">
  <b>A daily media-time budget per child for your Home Assistant media players: counts playback, warns before the end, and stops the music when time is up.</b>
</p>

<p align="center">
  <a href="https://github.com/hacs/integration"><img src="https://img.shields.io/badge/HACS-Custom-41BDF5.svg" alt="HACS Custom"></a>
  <a href="https://github.com/Jo-Highness/media_time_guard/actions/workflows/validate.yml"><img src="https://github.com/Jo-Highness/media_time_guard/actions/workflows/validate.yml/badge.svg" alt="Validate"></a>
  <a href="https://github.com/Jo-Highness/media_time_guard/actions/workflows/test.yml"><img src="https://github.com/Jo-Highness/media_time_guard/actions/workflows/test.yml/badge.svg" alt="Tests"></a>
  <a href="https://github.com/Jo-Highness/media_time_guard/releases"><img src="https://img.shields.io/github/v/release/Jo-Highness/media_time_guard" alt="Release"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green.svg" alt="MIT"></a>
  <img src="https://img.shields.io/badge/Home%20Assistant-2025.2%2B-41BDF5.svg" alt="Home Assistant 2025.2+">
</p>

## Quick start

1. **Install** via HACS: [![Open in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Jo-Highness&repository=media_time_guard&category=integration) → **Download** → restart Home Assistant.
2. **Add** the integration: **Settings → Devices & services → Add integration → Media Time Guard**.
3. **Enter a name** (e.g. `Luke`) and **pick the child's media players**, then set the minutes per weekday.
4. **Done:** `sensor.media_time_luke_remaining` now shows the remaining minutes. Start playback on one of the players and watch it count down — when it reaches 0, the players are stopped.

Repeat step 2–3 for every child (one entry per child).

## What it does

- ⏱️ **A budget per weekday** – short on school days, longer at the weekend (`0` = no media that day).
- ⏹️ **Stops playback when the budget is used up** – and stops it again if playback is restarted on an assigned player, also after a speaker power-cycle or a Home Assistant restart (the state is saved).
- 🔀 **No double counting** – playing on two of the child's speakers at once counts once (wall-clock time).
- 🔔 **A heads-up before the end** – a one-time **TTS announcement** ("10 minutes left …") or your own sound.
- ➕ **Bonus minutes** – via buttons (+15/+30), a number entity or an action.
- 🤒 **Exceptions** – child is ill? Suspend enforcement for today with one switch.
- 🌍 **Multilingual UI** – English, German, Spanish, French, Norwegian, Greek and Japanese.
- 🧩 **UI-configured, fully local** – no YAML, no cloud.

### What counts — and what it can't control

Only time in which at least one assigned player reports the state **`playing`** is counted.
`paused`, `buffering`, `idle`, `on`, `standby`, `off` and `unavailable` are **not** counted.

Keep in mind that this is a convenience tool, not a lock-down:

- It only sees and stops the `media_player` entities you assign. Other devices, apps that are
  not exposed to Home Assistant, or players that never report `playing` (some TVs only report
  `on`) are not covered.
- Stopping uses `media_player.media_stop`; a player that doesn't support it, or is offline,
  can't be stopped (failures are logged).
- Anyone with access to the Home Assistant UI can grant extra minutes or suspend enforcement.
- Muted or very quiet playback still counts, because the player is `playing`.

## Screenshots

> Captured from a demo Home Assistant with fictional data.

| Setup (version 1.1 – the "Person entity" field no longer exists) | Entities card in use |
|:---:|:---:|
| ![The setup form](images/config-flow.png) | ![Remaining time, extra minutes, suspend and quick-add buttons](images/dashboard.png) |

## Installation

### HACS (recommended)

1. Click the **Open in HACS** button above, or in **HACS → ⋮ → Custom repositories** add
   `https://github.com/Jo-Highness/media_time_guard` as type **Integration**.
2. Search for **Media Time Guard** and **download** it.
3. **Restart** Home Assistant.

### Manual

1. Copy `custom_components/media_time_guard/` into your `<config>/custom_components/` folder.
2. **Restart** Home Assistant.

Requires **Home Assistant 2025.2** or newer.

## Configuration

Add one entry **per child**. Setup and later changes (**Configure** on the entry) use the same four steps:

| Step | What you set |
|---|---|
| **1 · Person** | A **name** (e.g. `Luke`, must be unique) and the assigned **media players**. Each player can belong to only one person. |
| **2 · Daily budgets** | Minutes for each weekday **Mon–Sun**. `0` blocks media for the whole day. |
| **3 · Warning** | On/off, the **remaining-minutes threshold** (default `10`) and the **method**: a **TTS** announcement (TTS engine + text, `{minutes}` is replaced; leave the text empty for the default in your Home Assistant language) **or** a **media** content ID (+ content type, default `music`). |
| **4 · Reset** | The daily **reset time** (default `00:00:00`). Counters, lock, suspension and warning are reset then. |

Optional fields (TTS engine, text, media ID/type) can be cleared again in the options.
Raising a budget in the options lifts an active lock right away if time is left.

## Entities

Each person gets a **device** (named after the person) with these entities. `<person>` is the
slugified name at the time the entry was created, e.g. `luke`:

| Entity | Type | Purpose |
|---|---|---|
| `sensor.media_time_<person>_remaining` | sensor (duration, min) | Remaining media minutes today, with attributes (see below). |
| `switch.media_time_<person>_suspend_today` | switch | **Suspend today** – no lock and no stopping for the rest of the day (time is still counted). |
| `switch.media_time_<person>_blocked` | switch | **Blocked** – blocks all players of this person **until further notice**: any playback is stopped right away, regardless of the remaining time. Takes precedence over *Suspend today* and extra minutes, counts no time, sends no warning and survives the daily reset, `reset_person` and restarts. Only switching it off ends it. |
| `number.media_time_<person>_extend` | number (0–600, step 5, min) | **Extra minutes** for today (absolute value). |
| `button.media_time_<person>_extend_15` | button | Add **+15 minutes**. |
| `button.media_time_<person>_extend_30` | button | Add **+30 minutes**. |

Sensor attributes: `budget_minutes`, `effective_budget_minutes`, `used_minutes`,
`remaining_minutes`, `extra_minutes_today`, `weekday` (0 = Monday), `is_playing`, `is_locked`,
`is_suspended`, `is_blocked`, `warned_today`, `last_reset`, `players`.

**Entity IDs and renaming.** Entity IDs are created once and then kept by Home Assistant's
entity registry. If you **rename the person** in the options, the device name, entry title and
entity *names* change, but the entity *IDs* stay the same (e.g. still `…_luke_…`) so your
automations keep working. To get new IDs, rename them yourself in the entity settings.
If you **rename or replace a media player or TTS entity**, the assignment is not updated
automatically: Media Time Guard raises a **repair issue** under *Settings → Repairs*; open
**Configure** on the entry and select the current entity.

## Actions (services)

Every action addresses one person, either with **`person`** (name or slug, case-insensitive)
or with **`config_entry_id`** (stays valid after a rename). One of both is required.

| Action | Fields | Description |
|---|---|---|
| `media_time_guard.extend_time` | `person` / `config_entry_id`, `minutes` (1–600) | Add extra minutes for today. |
| `media_time_guard.suspend_today` | `person` / `config_entry_id`, `suspended` (bool) | Suspend or resume enforcement for today. |
| `media_time_guard.set_blocked` | `person` / `config_entry_id`, `blocked` (bool) | Block all players of the person until further notice, or lift the block. |
| `media_time_guard.reset_person` | `person` / `config_entry_id` | Reset today's counters, lock, extra minutes and suspension (the permanent *Blocked* switch stays). |

## Automation examples

**Reward 15 minutes when homework is done:**

```yaml
automation:
  - alias: "Media reward when homework is done"
    triggers:
      - trigger: state
        entity_id: input_boolean.luke_homework_done
        to: "on"
    actions:
      - action: media_time_guard.extend_time
        data:
          person: Luke
          minutes: 15
```

**Suspend enforcement on a sick day:**

```yaml
automation:
  - alias: "Suspend media limit when sick"
    triggers:
      - trigger: state
        entity_id: input_boolean.luke_sick
        to: "on"
    actions:
      - action: media_time_guard.suspend_today
        data:
          person: Luke
          suspended: true
```

**Notify your phone when the budget is used up:**

```yaml
automation:
  - alias: "Notify when media time is up"
    triggers:
      - trigger: state
        entity_id: sensor.media_time_luke_remaining
        attribute: is_locked
        to: true
    actions:
      - action: notify.mobile_app_parent_phone
        data:
          message: "Luke's media time for today is used up."
```

Replace `notify.mobile_app_parent_phone` with your own notify action.

## Example dashboard card

```yaml
type: vertical-stack
cards:
  - type: gauge
    entity: sensor.media_time_luke_remaining
    name: Luke – media time left
    min: 0
    max: 120
    severity:
      green: 30
      yellow: 10
      red: 0
  - type: entities
    entities:
      - entity: number.media_time_luke_extend
      - entity: switch.media_time_luke_suspend_today
      - entity: switch.media_time_luke_blocked
      - entity: button.media_time_luke_extend_15
      - entity: button.media_time_luke_extend_30
```

## Troubleshooting / FAQ

**Playback doesn't stop when the budget is empty.**
Check that the child's players are assigned in the entry, that they report `playing` while
playing (see *Developer tools → States*) and support "stop". Look for a repair issue about
missing entities. `0` minutes means "blocked all day".

**Time counts although nothing is audible.**
Counting is based on the `playing` state, so muted playback counts too.

**The same child uses two speakers — is time counted twice?**
No, time is counted once while at least one assigned player is playing.

**A player can't be assigned to a second child.**
By design: each `media_player` belongs to exactly one person.

**The warning never plays.**
For **TTS** a TTS engine is required, for **Media** a content ID. The warning plays once when
the remaining time reaches the threshold; after bonus minutes push the remaining time above
the threshold again, it plays once more before the new end.

**Enable debug logging:**

```yaml
logger:
  logs:
    custom_components.media_time_guard: debug
```

Diagnostics (without names or entity IDs) can be downloaded from the entry's ⋮ menu.

More: user guides in [`docs/user/`](docs/user) (de, en, es, fr, nb, el, ja) and the
architecture in [`docs/TECHNICAL.md`](docs/TECHNICAL.md).

## Contributing

Contributions are welcome. Please read [`CONTRIBUTING.md`](CONTRIBUTING.md) and open an issue
or pull request on [GitHub](https://github.com/Jo-Highness/media_time_guard).

## License

Released under the [MIT License](LICENSE).

## Credits

Created and maintained by [@Jo-Highness](https://github.com/Jo-Highness).
Built as a custom [Home Assistant](https://www.home-assistant.io/) integration for
[HACS](https://hacs.xyz/).
