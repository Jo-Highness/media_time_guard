# Media Time Guard – User Guide (English)

Media Time Guard limits a person's daily media time on their media players (e.g. Sonos One)
and enforces the limit reliably — even when children try to bypass it.

## 1. Installation

**Via HACS (recommended)**
1. Open HACS → ⋮ menu → *Custom repositories*.
2. Add the repository URL, category **Integration**.
3. Search for *Media Time Guard* and download it.
4. Restart Home Assistant.

**Manual:** copy the `custom_components/media_time_guard/` folder into
`<config>/custom_components/` and restart HA.

## 2. Set up a person

*Settings → Devices & Services → Add integration → "Media Time Guard".*
One entry is created per person. The wizard has four steps:

1. **Person & players**
   - **Name**: e.g. `Luke`. (Children often have no `person` entity — just type the name.)
   - **Person entity** (optional): if one exists.
   - **Media players**: one or more. A player may belong to only **one** person.
2. **Daily budgets**: minutes for Monday–Sunday. `0` = blocked all day.
3. **Warning** (optional): on/off, remaining-time threshold (minutes), method:
   - **TTS**: pick a TTS engine + announcement text. `{minutes}` is replaced by the minutes left.
   - **Media**: a media URL / content ID to play.
4. **Reset**: time of day the counter resets (default `00:00`).

Change later via the entry's **Configure** button.

## 3. What happens

- Time counts only while at least one assigned player is **playing**.
- Playing on several speakers at once is **not** double counted.
- When the budget is used up, all players are **stopped** and locked for the rest of the day.
  Power-cycling a speaker or restarting HA does **not** lift the lock.
- Shortly before the budget ends, a one-time warning is emitted (if enabled).

## 4. Entities per person

| Entity | Meaning |
|---|---|
| `sensor.media_time_<person>_remaining` | minutes left today |
| `switch.media_time_<person>_suspend_today` | suspend enforcement today (e.g. ill) |
| `number.media_time_<person>_extend` | extra minutes today (absolute value) |
| `button.media_time_<person>_extend_15` / `_extend_30` | +15 / +30 minutes |

Sensor attributes include `budget_minutes`, `used_minutes`, `remaining_minutes`, `is_locked`,
`is_suspended`, `extra_minutes_today`, `warned_today`.

## 5. Common tasks

- **Grant more time:** press the +15/+30 button, set the number entity, or call
  `media_time_guard.extend_time` with `person` and `minutes`.
- **No limit today (child ill):** turn on the *Suspend Today* switch or call
  `media_time_guard.suspend_today` with `suspended: true`.
- **Reset manually:** call `media_time_guard.reset_person`.

## 6. Known limitation

Counting is based on the `playing` state. **Muted or very quiet playback still counts**,
because the player is still "playing".
