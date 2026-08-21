<!-- DRAFT — r/homeassistant post. Do not post as-is; add a real screenshot/GIF first. -->
<!-- Suggested flair: "Custom Integration" / "Project". -->

**Title:** Media Time Guard — a per-child daily media-time budget (local, HACS custom integration)

---

I made a small local integration that enforces a **daily media-time budget per child** in Home Assistant.

You create one config entry per child, bind it to a `person` (or just a name), and assign that child's
`media_player` entities. It counts playing time on those players and, when the day's budget is used up,
it keeps those players stopped. Budgets are per weekday in minutes (`0` = blocked that day), the daily
reset time is configurable, and there's an optional one-time warning (TTS announcement or a played media
URL) at a remaining-minutes threshold you set. Fully local, no cloud.

<!-- IMAGE/GIF PLACEHOLDER -->
<!-- Insert here: one screenshot of the per-child entities (remaining-time sensor, suspend switch,
     extra-minutes number, quick-add button) OR a short config-flow GIF. Reddit shows the first image. -->

Config is UI-first (person → daily budgets → warning → reset). Each child also gets a remaining-time
sensor, a "suspend today" switch (e.g. kid is ill), an extra-minutes number, and a quick-add button.
Services: `extend_time`, `suspend_today`, `reset_person`.

**Honest about the limits:** it only governs the media players you assign — it can't stop devices HA
doesn't control. Enforcement is stop/pause-based. TTS warnings need a TTS engine configured. And it's a
time-budget tool, not full parental control / content filtering — it manages *how long*, not *what*.

Version 1.1.0, min HA 2024.1, MIT. UI in 7 languages (DE/EL/EN/ES/FR/JA/NB).

Install via HACS as a custom repository (default store once accepted):
https://github.com/Jo-Highness/media_time_guard

Happy to hear feedback.
