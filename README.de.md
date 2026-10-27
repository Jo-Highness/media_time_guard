> 🇬🇧 [English](README.md) · 🇩🇪 Deutsch (diese Seite) · 🇪🇸 [Español](README.es.md)

<p align="center">
  <img src="icon.png" alt="Media Time Guard" width="160" height="160">
</p>

<h1 align="center">Media Time Guard</h1>

<p align="center">
  <b>Ein tägliches Medienzeit-Budget pro Kind für deine Home-Assistant-Media-Player: zählt die Wiedergabe, warnt vor dem Ende und stoppt die Musik, wenn die Zeit um ist.</b>
</p>

<p align="center">
  <a href="https://github.com/hacs/integration"><img src="https://img.shields.io/badge/HACS-Custom-41BDF5.svg" alt="HACS Custom"></a>
  <a href="https://github.com/Jo-Highness/media_time_guard/actions/workflows/validate.yml"><img src="https://github.com/Jo-Highness/media_time_guard/actions/workflows/validate.yml/badge.svg" alt="Validate"></a>
  <a href="https://github.com/Jo-Highness/media_time_guard/actions/workflows/test.yml"><img src="https://github.com/Jo-Highness/media_time_guard/actions/workflows/test.yml/badge.svg" alt="Tests"></a>
  <a href="https://github.com/Jo-Highness/media_time_guard/releases"><img src="https://img.shields.io/github/v/release/Jo-Highness/media_time_guard" alt="Release"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green.svg" alt="MIT"></a>
  <img src="https://img.shields.io/badge/Home%20Assistant-2025.2%2B-41BDF5.svg" alt="Home Assistant 2025.2+">
</p>

## Schnellstart

1. **Installieren** über HACS: [![In HACS öffnen](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Jo-Highness&repository=media_time_guard&category=integration) → **Herunterladen** → Home Assistant neu starten.
2. Integration **hinzufügen**: **Einstellungen → Geräte & Dienste → Integration hinzufügen → Media Time Guard**.
3. **Namen eingeben** (z. B. `Luke`), die **Media-Player des Kindes wählen** und die Minuten je Wochentag festlegen.
4. **Fertig:** `sensor.media_time_luke_remaining` zeigt jetzt die Restminuten. Starte die Wiedergabe auf einem der Player und sieh zu, wie die Zeit abläuft – bei 0 werden die Player gestoppt.

Schritt 2–3 für jedes Kind wiederholen (ein Eintrag pro Kind).

## Was es macht

- ⏱️ **Pro Wochentag ein eigenes Budget** – werktags kurz, am Wochenende länger (`0` = an dem Tag keine Medien).
- ⏹️ **Stoppt die Wiedergabe, wenn das Budget aufgebraucht ist** – und stoppt erneut, wenn auf einem zugeordneten Player wieder gestartet wird, auch nach Aus-/Einschalten der Box oder einem Home-Assistant-Neustart (der Zustand wird gespeichert).
- 🔀 **Kein Doppelzählen** – laufen zwei Boxen des Kindes gleichzeitig, zählt die Zeit einmal (Wanduhr-Zeit).
- 🔔 **Vorwarnung vor dem Ende** – eine einmalige **TTS-Ansage** („Noch 10 Minuten …“) oder ein eigener Sound.
- ➕ **Bonusminuten** – per Taster (+15/+30), Nummern-Entität oder Aktion.
- 🤒 **Ausnahmen** – Kind ist krank? Kontrolle für heute mit einem Schalter aussetzen.
- 🌍 **Mehrsprachige Oberfläche** – Deutsch, Englisch, Spanisch, Französisch, Norwegisch, Griechisch und Japanisch.
- 🧩 **Einrichtung über die Oberfläche, komplett lokal** – kein YAML, keine Cloud.

### Was gezählt wird – und was es nicht kontrollieren kann

Gezählt wird nur Zeit, in der mindestens ein zugeordneter Player den Zustand **`playing`** meldet.
`paused`, `buffering`, `idle`, `on`, `standby`, `off` und `unavailable` zählen **nicht**.

Bitte beachten: Das ist ein Komfort-Werkzeug, keine Komplettsperre.

- Es sieht und stoppt nur die zugeordneten `media_player`-Entitäten. Andere Geräte, Apps, die
  nicht in Home Assistant eingebunden sind, oder Player, die nie `playing` melden (manche
  Fernseher melden nur `on`), werden nicht erfasst.
- Gestoppt wird mit `media_player.media_stop`; ein Player, der das nicht unterstützt oder
  offline ist, kann nicht gestoppt werden (Fehler werden geloggt).
- Wer Zugriff auf die Home-Assistant-Oberfläche hat, kann Extra-Minuten geben oder die
  Kontrolle aussetzen.
- Stummgeschaltete oder sehr leise Wiedergabe zählt mit, weil der Player `playing` meldet.

## Screenshots

> Aufgenommen in einer Demo-Instanz mit fiktiven Daten.

| Einrichtung (Version 1.1 – das Feld „Person-Entität“ gibt es nicht mehr) | Entitäten-Karte im Einsatz |
|:---:|:---:|
| ![Das Einrichtungsformular](images/config-flow.png) | ![Restzeit, Extra-Minuten, Aussetzen und Schnell-Taster](images/dashboard.png) |

## Installation

### HACS (empfohlen)

1. Den Button **In HACS öffnen** oben nutzen oder in **HACS → ⋮ → Benutzerdefinierte Repositories**
   `https://github.com/Jo-Highness/media_time_guard` als Typ **Integration** hinzufügen.
2. Nach **Media Time Guard** suchen und **herunterladen**.
3. Home Assistant **neu starten**.

### Manuell

1. Ordner `custom_components/media_time_guard/` nach `<config>/custom_components/` kopieren.
2. Home Assistant **neu starten**.

Voraussetzung: **Home Assistant 2025.2** oder neuer.

## Einrichtung

Ein Eintrag **pro Kind**. Einrichtung und spätere Änderungen (**Konfigurieren** am Eintrag) nutzen dieselben vier Schritte:

| Schritt | Was du einstellst |
|---|---|
| **1 · Person** | Ein **Name** (z. B. `Luke`, muss eindeutig sein) und die zugeordneten **Media-Player**. Jeder Player gehört zu genau einer Person. |
| **2 · Tagesbudgets** | Minuten je Wochentag **Mo–So**. `0` sperrt Medien den ganzen Tag. |
| **3 · Vorwarnung** | Ein/aus, **Restzeit-Schwelle** (Standard `10`) und die **Methode**: eine **TTS**-Ansage (TTS-Engine + Text, `{minutes}` wird ersetzt; Text leer lassen für den Standardtext in deiner Home-Assistant-Sprache) **oder** eine **Medien**-Content-ID (+ Content-Typ, Standard `music`). |
| **4 · Reset** | Uhrzeit des täglichen **Resets** (Standard `00:00:00`). Dann werden Zähler, Sperre, Aussetzen und Vorwarnung zurückgesetzt. |

Optionale Felder (TTS-Engine, Text, Medien-ID/-Typ) lassen sich in den Optionen auch wieder leeren.
Wird ein Budget in den Optionen erhöht, wird eine aktive Sperre sofort aufgehoben, sofern wieder Zeit übrig ist.

## Entitäten

Jede Person bekommt ein **Gerät** (benannt nach der Person) mit diesen Entitäten. `<person>` ist
der Namens-Slug zum Zeitpunkt der Einrichtung, z. B. `luke`:

| Entität | Typ | Zweck |
|---|---|---|
| `sensor.media_time_<person>_remaining` | Sensor (Dauer, min) | Restliche Medienminuten heute, mit Attributen (siehe unten). |
| `switch.media_time_<person>_suspend_today` | Schalter | **Heute aussetzen** – für den Rest des Tages keine Sperre und kein Stoppen (die Zeit wird weiter gezählt). |
| `switch.media_time_<person>_blocked` | Schalter | **Gesperrt** – sperrt alle Player dieser Person **bis auf Weiteres**: jede Wiedergabe wird sofort gestoppt, egal wie viel Zeit noch übrig ist. Hat Vorrang vor *Heute aussetzen* und Extra-Minuten, zählt keine Zeit, sendet keine Warnung und übersteht Tagesreset, `reset_person` und Neustarts. Endet nur durch Ausschalten. |
| `number.media_time_<person>_extend` | Nummer (0–600, Schritt 5, min) | **Extra-Minuten** für heute (absoluter Wert). |
| `button.media_time_<person>_extend_15` | Taster | **+15 Minuten**. |
| `button.media_time_<person>_extend_30` | Taster | **+30 Minuten**. |

Sensor-Attribute: `budget_minutes`, `effective_budget_minutes`, `used_minutes`,
`remaining_minutes`, `extra_minutes_today`, `weekday` (0 = Montag), `is_playing`, `is_locked`,
`is_suspended`, `is_blocked`, `warned_today`, `last_reset`, `players`.

**Entitäts-IDs und Umbenennen.** Entitäts-IDs werden einmal angelegt und danach von der
Entitäts-Registry von Home Assistant beibehalten. **Benennst du die Person** in den Optionen um,
ändern sich Gerätename, Titel des Eintrags und die *Namen* der Entitäten – die *IDs* bleiben
gleich (z. B. weiter `…_luke_…`), damit deine Automationen weiter funktionieren. Neue IDs
vergibst du bei Bedarf selbst in den Entitäts-Einstellungen.
**Benennst du einen Media-Player oder eine TTS-Entität um oder ersetzt sie**, wird die
Zuordnung nicht automatisch angepasst: Media Time Guard meldet dann ein **Reparaturproblem**
unter *Einstellungen → Reparaturen*; öffne **Konfigurieren** am Eintrag und wähle die aktuelle
Entität.

## Aktionen (Dienste)

Jede Aktion spricht eine Person an – entweder über **`person`** (Name oder Slug, Groß-/Kleinschreibung
egal) oder über **`config_entry_id`** (bleibt nach einer Umbenennung gültig). Eins von beiden ist Pflicht.

| Aktion | Felder | Beschreibung |
|---|---|---|
| `media_time_guard.extend_time` | `person` / `config_entry_id`, `minutes` (1–600) | Extra-Minuten für heute hinzufügen. |
| `media_time_guard.suspend_today` | `person` / `config_entry_id`, `suspended` (bool) | Kontrolle für heute aussetzen oder fortsetzen. |
| `media_time_guard.set_blocked` | `person` / `config_entry_id`, `blocked` (bool) | Alle Player der Person bis auf Weiteres sperren oder die Sperre aufheben. |
| `media_time_guard.reset_person` | `person` / `config_entry_id` | Heutige Zähler, Tages-Sperre, Extra-Minuten und Aussetzen zurücksetzen (die dauerhafte Sperre *Gesperrt* bleibt). |

## Automatisierungs-Beispiele

**15 Minuten belohnen, wenn die Hausaufgaben erledigt sind:**

```yaml
automation:
  - alias: "Medienzeit-Belohnung nach Hausaufgaben"
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

**Kontrolle an einem Krankheitstag aussetzen:**

```yaml
automation:
  - alias: "Medienlimit bei Krankheit aussetzen"
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

**Benachrichtigung aufs Handy, wenn das Budget aufgebraucht ist:**

```yaml
automation:
  - alias: "Benachrichtigen, wenn die Medienzeit um ist"
    triggers:
      - trigger: state
        entity_id: sensor.media_time_luke_remaining
        attribute: is_locked
        to: true
    actions:
      - action: notify.mobile_app_eltern_handy
        data:
          message: "Lukes Medienzeit für heute ist aufgebraucht."
```

`notify.mobile_app_eltern_handy` durch deine eigene Notify-Aktion ersetzen.

## Beispiel-Dashboard-Karte

```yaml
type: vertical-stack
cards:
  - type: gauge
    entity: sensor.media_time_luke_remaining
    name: Luke – Medienzeit übrig
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

## Fehlersuche / FAQ

**Die Wiedergabe stoppt nicht, obwohl das Budget leer ist.**
Prüfe, ob die Player des Kindes im Eintrag zugeordnet sind, beim Abspielen `playing` melden
(siehe *Entwicklerwerkzeuge → Zustände*) und „Stopp“ unterstützen. Schau nach einem
Reparaturproblem zu fehlenden Entitäten. `0` Minuten bedeutet „den ganzen Tag gesperrt“.

**Es wird gezählt, obwohl nichts zu hören ist.**
Gezählt wird anhand des Zustands `playing` – stumme Wiedergabe zählt also mit.

**Dasselbe Kind nutzt zwei Boxen – wird doppelt gezählt?**
Nein, die Zeit zählt einmal, solange mindestens ein zugeordneter Player spielt.

**Ein Player lässt sich keinem zweiten Kind zuordnen.**
Absicht: Jeder `media_player` gehört genau einer Person.

**Die Vorwarnung kommt nie.**
Für **TTS** ist eine TTS-Engine nötig, für **Medien** eine Content-ID. Die Vorwarnung kommt
einmal, wenn die Restzeit die Schwelle erreicht; heben Bonusminuten die Restzeit wieder über
die Schwelle, kommt sie vor dem neuen Ende noch einmal.

**Debug-Logging aktivieren:**

```yaml
logger:
  logs:
    custom_components.media_time_guard: debug
```

Diagnosedaten (ohne Namen und Entitäts-IDs) lassen sich über das ⋮-Menü des Eintrags herunterladen.

Mehr: Anleitungen in [`docs/user/`](docs/user) (de, en, es, fr, nb, el, ja) und die
Architektur in [`docs/TECHNICAL.md`](docs/TECHNICAL.md).

## Mitwirken

Beiträge sind willkommen. Bitte lies [`CONTRIBUTING.md`](CONTRIBUTING.md) und öffne ein Issue
oder einen Pull Request auf [GitHub](https://github.com/Jo-Highness/media_time_guard).

## Lizenz

Veröffentlicht unter der [MIT-Lizenz](LICENSE).

## Credits

Entwickelt und gepflegt von [@Jo-Highness](https://github.com/Jo-Highness).
Eine benutzerdefinierte [Home-Assistant](https://www.home-assistant.io/)-Integration für
[HACS](https://hacs.xyz/).
