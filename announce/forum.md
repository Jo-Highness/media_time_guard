<!-- DRAFT — Home Assistant Community, category "Share your Projects!" -->
<!-- Do not post as-is: replace the image/GIF placeholders below with real captures first. -->

# Media Time Guard — a per-child daily media-time budget for Home Assistant

I built a small custom integration that enforces a **daily media-time budget per child**
inside Home Assistant. It counts how long a child's assigned media players run and, once the
day's budget is used up, it enforces the limit by keeping those players stopped. Everything
runs locally — no cloud, no account.

Repo: https://github.com/Jo-Highness/media_time_guard

<!-- IMAGE PLACEHOLDER: hero screenshot -->
<!-- Insert here: a screenshot of the integration's device page showing the per-child entities
     (Remaining-time sensor, Suspend-today switch, Extra-minutes number, quick-add button).
     Recommended width ~800px. -->
![Media Time Guard — per-child entities](docs/images/overview.png)

## What it does

- **One config entry per child.** You bind the entry to a `person` entity, or just give it a name.
- **Assign that child's `media_player` entities.** The integration watches those players and adds
  up the time they spend playing.
- **Per-weekday budgets in minutes.** Set a separate budget for each day of the week
  (`0` means the child is blocked that day).
- When the budget for the day is spent, it **enforces the limit** by stopping the assigned players
  and keeping them stopped for the rest of the day.
- **Optional one-time warning** before the time runs out: either a **TTS announcement** or a
  **played media URL**, triggered at a remaining-minutes threshold you choose.
- **Configurable daily reset time**, so the budget refills when you want (not necessarily midnight).

## Setup

Configuration is UI-first — the config flow walks through:

1. Pick the person (or enter a name)
2. Set the daily budgets (per weekday, in minutes)
3. Configure the optional warning (TTS or media URL, and the remaining-minutes threshold)
4. Set the daily reset time

<!-- GIF PLACEHOLDER: config flow walkthrough -->
<!-- Insert here: a short screen recording (GIF or MP4) stepping through the four config-flow pages.
     Keep it under ~10s and crop to the dialog. -->
![Config flow walkthrough](docs/images/config-flow.gif)

## Per-child entities

Each configured child gets:

- a **Remaining-time sensor** (minutes left today)
- a **Suspend-today switch** — turn off enforcement for one day (e.g. the child is ill)
- an **Extra-minutes number** — grant additional minutes for today
- a **quick-add button** — add the configured extra minutes in one tap

## Services

- `media_time_guard.extend_time` — add minutes to a child's remaining budget today
- `media_time_guard.suspend_today` — suspend enforcement for the rest of the day
- `media_time_guard.reset_person` — reset a child's counter

## Honest limitations

I want to be clear about what this is and is not:

- It only governs the **media players you assign to it**. It cannot stop devices Home Assistant
  doesn't control.
- Enforcement is **stop/pause-based** — it stops or pauses the assigned players; it does not lock
  a device or block an app.
- **TTS warnings require a TTS engine** already configured in Home Assistant.
- It is a **time-budget tool, not a full parental-control / content-filtering** solution. It manages
  *how long*, not *what* is played.

## Details

- Version **1.1.0**, minimum Home Assistant **2024.1**, licensed **MIT**.
- UI translated into **7 languages**: German, Greek, English, Spanish, French, Japanese, Norwegian Bokmål.

## Install

Via **HACS**:

- Add `https://github.com/Jo-Highness/media_time_guard` as a **custom repository** (type: Integration),
  then install and restart Home Assistant.
- Once the repository is accepted into the default HACS store, it will be installable directly from there.

Feedback and issues are welcome on the repo. It scratches my own itch at home; if it's useful to you too, all the better.
