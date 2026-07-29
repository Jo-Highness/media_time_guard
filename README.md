<p align="center">
  <img src="icon.png" alt="Media Time Guard" width="160" height="160">
</p>

<h1 align="center">Media Time Guard</h1>

<p align="center">
  <b>Screen &amp; speaker time for kids — set it once, and it just holds.</b><br>
  <i>Bildschirm- und Hörzeit für Kinder — einmal einstellen, und es hält einfach.</i><br>
  <i>Tiempo de pantalla y audio para niños — configúralo una vez y se mantiene.</i>
</p>

<p align="center">
  <a href="https://github.com/hacs/integration"><img src="https://img.shields.io/badge/HACS-Custom-41BDF5.svg" alt="HACS Custom"></a>
  <img src="https://img.shields.io/badge/Home%20Assistant-2024.1%2B-41BDF5.svg" alt="Home Assistant 2024.1+">
  <img src="https://img.shields.io/badge/languages-DE%20%7C%20EN%20%7C%20ES%20%7C%20FR%20%7C%20NB%20%7C%20EL%20%7C%20JA-informational.svg" alt="Languages">
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="MIT">
</p>

<p align="center">
  <a href="#-deutsch">🇩🇪 Deutsch</a> ·
  <a href="#-english">🇬🇧 English</a> ·
  <a href="#-español">🇪🇸 Español</a>
</p>

---

Every parent knows the scene: *"Just five more minutes!"* — for the third time.
**Media Time Guard** gives every child a **daily media-time budget** and enforces it
**automatically and tamper-resistantly** across your Sonos and any other Home Assistant
`media_player`. No nagging, no timers on your phone, no loopholes. When the budget is up,
the music stops — and turning the speaker off and on again won't buy more time.

---

## 🇩🇪 Deutsch

### Schluss mit der Diskussion um „nur noch fünf Minuten"

**Media Time Guard** gibt jedem Kind ein **tägliches Medienzeit-Budget** und setzt es
**automatisch und manipulationssicher** durch – auf Sonos One und **jedem** anderen
`media_player` in Home Assistant. Ist das Guthaben aufgebraucht, stoppt die Wiedergabe.
Box aus- und wieder einschalten? Ändert nichts. Neustart? Ändert nichts. Genau dafür ist es
gebaut – **Kinder testen Grenzen, diese Integration hält sie.**

**Warum Eltern es lieben**

- ⏱️ **Pro Wochentag ein eigenes Budget** – werktags kurz, am Wochenende großzügiger (`0` = an dem Tag gesperrt).
- 🛡️ **Wirklich manipulationssicher** – zählt die echte Wanduhr-Wiedergabe und übersteht Neustarts, Stromausfälle und Aus/Ein-Tricks.
- 🔀 **Kein Doppelzählen** – läuft dasselbe Kind auf mehreren Boxen, zählt die Zeit trotzdem nur einmal.
- 🔔 **Faire Vorwarnung** – kurz vor Schluss eine freundliche **TTS-Ansage** („Noch 10 Minuten…") oder ein eigener Sound.
- ➕ **Belohnen leicht gemacht** – Extra-Minuten per Knopfdruck (+15/+30), Schieberegler oder Service.
- 🤒 **Ausnahmen** – Kind ist krank? Kontrolle für heute mit einem Schalter aussetzen.
- 🌍 **Mehrsprachig** – Oberfläche **und Entitäten** in Deutsch, Englisch, Spanisch, Französisch (+ Norwegisch, Griechisch, Japanisch).
- 🧩 **100 % über die Oberfläche** – kein YAML, keine Automationen nötig.

### Installation

1. **HACS** → ⋮ → *Benutzerdefinierte Repositories* → dieses Repo als Kategorie **Integration** hinzufügen.
2. *Media Time Guard* in HACS suchen und **herunterladen**.
3. Home Assistant **neu starten**.
4. *Einstellungen → Geräte & Dienste → Integration hinzufügen → „Media Time Guard"*.

> **Manuell:** Ordner `custom_components/media_time_guard/` nach `<config>/custom_components/` kopieren und HA neu starten.

### In 4 Schritten eingerichtet (eine Integration pro Kind)

1. **Person & Player** – Name (z. B. `Luke`), optional eine `person`-Entität, und die zugeordneten Media-Player.
2. **Tagesbudgets** – Minuten je Wochentag (Mo–So, `0` = gesperrt).
3. **Vorwarnung** – ein/aus, Restzeit-Schwelle, Methode (TTS **oder** Medien-URL), Text bzw. Content-ID.
4. **Reset** – Uhrzeit des Tages-Resets (Standard `00:00`).

Alles später über *Konfigurieren* änderbar. Ausführliche Anleitung: [`docs/user/de.md`](docs/user/de.md).

---

## 🇬🇧 English

### End the "just five more minutes" negotiation

**Media Time Guard** gives every child a **daily media-time budget** and enforces it
**automatically and tamper-resistantly** — on Sonos One and **any** other Home Assistant
`media_player`. When the budget runs out, playback stops. Power-cycle the speaker? No effect.
Restart? No effect. That's the whole point — **kids push the limits; this integration holds them.**

**Why parents love it**

- ⏱️ **A budget per weekday** – short on school days, generous on weekends (`0` = blocked that day).
- 🛡️ **Genuinely tamper-resistant** – counts real wall-clock playback and survives restarts, power cuts and off/on tricks.
- 🔀 **No double counting** – the same child on several speakers still spends time only once.
- 🔔 **A fair heads-up** – a friendly **TTS announcement** ("10 minutes left…") or your own sound just before time's up.
- ➕ **Easy to reward** – extra minutes via buttons (+15/+30), a slider, or a service call.
- 🤒 **Exceptions** – child is ill? Suspend enforcement for today with one switch.
- 🌍 **Multilingual** – UI **and entities** in English, German, Spanish, French (+ Norwegian, Greek, Japanese).
- 🧩 **100 % UI-configured** – no YAML, no automations required.

### Installation

1. **HACS** → ⋮ → *Custom repositories* → add this repo as category **Integration**.
2. Search for *Media Time Guard* in HACS and **download** it.
3. **Restart** Home Assistant.
4. *Settings → Devices & Services → Add Integration → "Media Time Guard"*.

> **Manual:** copy `custom_components/media_time_guard/` into `<config>/custom_components/` and restart HA.

### Set up in 4 steps (one integration per child)

1. **Person & players** – a name (e.g. `Luke`), an optional `person` entity, and the assigned media players.
2. **Daily budgets** – minutes per weekday (Mon–Sun, `0` = blocked).
3. **Warning** – on/off, remaining-time threshold, method (TTS **or** media URL), message or content ID.
4. **Reset** – the daily reset time (default `00:00`).

Everything is editable later via *Configure*. Full guide: [`docs/user/en.md`](docs/user/en.md) · internals: [`docs/TECHNICAL.md`](docs/TECHNICAL.md).

---

## 🇪🇸 Español

### Se acabó la negociación de "solo cinco minutos más"

**Media Time Guard** asigna a cada niño un **presupuesto diario de tiempo multimedia** y lo
aplica **de forma automática y a prueba de manipulaciones** — en Sonos One y en **cualquier**
otro `media_player` de Home Assistant. Cuando se agota el tiempo, la reproducción se detiene.
¿Apagar y encender el altavoz? No sirve. ¿Reiniciar? Tampoco. Ese es justo el objetivo:
**los niños ponen a prueba los límites; esta integración los mantiene.**

**Por qué les encanta a los padres**

- ⏱️ **Un presupuesto por día de la semana** – corto entre semana, generoso el fin de semana (`0` = bloqueado ese día).
- 🛡️ **Realmente a prueba de manipulaciones** – cuenta la reproducción real y sobrevive a reinicios, cortes de luz y trucos de apagar/encender.
- 🔀 **Sin doble conteo** – el mismo niño en varios altavoces gasta el tiempo una sola vez.
- 🔔 **Un aviso justo** – un **anuncio TTS** amable ("quedan 10 minutos…") o tu propio sonido antes de terminar.
- ➕ **Recompensar es fácil** – minutos extra con botones (+15/+30), un control deslizante o un servicio.
- 🤒 **Excepciones** – ¿el niño está enfermo? Suspende el control por hoy con un interruptor.
- 🌍 **Multilingüe** – interfaz **y entidades** en español, inglés, alemán, francés (+ noruego, griego, japonés).
- 🧩 **100 % configurable desde la interfaz** – sin YAML ni automatizaciones.

### Instalación

1. **HACS** → ⋮ → *Repositorios personalizados* → añade este repo con la categoría **Integración**.
2. Busca *Media Time Guard* en HACS y **descárgalo**.
3. **Reinicia** Home Assistant.
4. *Ajustes → Dispositivos y servicios → Añadir integración → "Media Time Guard"*.

> **Manual:** copia `custom_components/media_time_guard/` en `<config>/custom_components/` y reinicia HA.

### Configúralo en 4 pasos (una integración por niño)

1. **Persona y reproductores** – un nombre (p. ej. `Luke`), una entidad `person` opcional y los reproductores asignados.
2. **Presupuestos diarios** – minutos por día de la semana (lun–dom, `0` = bloqueado).
3. **Aviso** – activado/desactivado, umbral de tiempo restante, método (TTS **o** URL multimedia), mensaje o ID de contenido.
4. **Reinicio** – la hora del reinicio diario (predeterminado `00:00`).

Todo se puede editar después con *Configurar*. Guía completa: [`docs/user/es.md`](docs/user/es.md).

---

## Entities, services & details

Each configured person gets a device with these entities (`<person>` = the name slug):

| Entity | Purpose |
|---|---|
| `sensor.media_time_<person>_remaining` | remaining minutes today (main variable, rich attributes) |
| `switch.media_time_<person>_suspend_today` | suspend enforcement for today |
| `number.media_time_<person>_extend` | extra minutes for today (absolute value) |
| `button.media_time_<person>_extend_15` / `_extend_30` | +15 / +30 minutes |

**Services:** `media_time_guard.extend_time` (person, minutes) · `media_time_guard.suspend_today`
(person, suspended) · `media_time_guard.reset_person` (person).

**Known limitation:** counting is based on the `playing` state, so muted/very quiet playback
still counts. Full user guides live in [`docs/user/`](docs/user) (de, en, es, fr, nb, el, ja);
architecture in [`docs/TECHNICAL.md`](docs/TECHNICAL.md).

## License

MIT
