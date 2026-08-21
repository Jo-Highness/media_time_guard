> 🇬🇧 [English](README.md) · 🇩🇪 Deutsch (this page) · 🇪🇸 [Español](README.es.md)

<p align="center">
  <img src="icon.png" alt="Media Time Guard" width="160" height="160">
</p>

<h1 align="center">Media Time Guard</h1>

<p align="center">
  <b>Bildschirm- und Hörzeit für Kinder — einmal einstellen, und es hält einfach.</b>
</p>

## Schluss mit der Diskussion um „nur noch fünf Minuten"

**Media Time Guard** gibt jedem Kind ein **tägliches Medienzeit-Budget** und setzt es
**automatisch und manipulationssicher** durch – auf Sonos One und **jedem** anderen
`media_player` in Home Assistant. Ist das Guthaben aufgebraucht, stoppt die Wiedergabe.
Box aus- und wieder einschalten? Ändert nichts. Neustart? Ändert nichts. Genau dafür ist es
gebaut – **Kinder testen Grenzen, diese Integration hält sie.**

### Warum Eltern es lieben

- ⏱️ **Pro Wochentag ein eigenes Budget** – werktags kurz, am Wochenende großzügiger (`0` = an dem Tag gesperrt).
- 🛡️ **Wirklich manipulationssicher** – zählt die echte Wanduhr-Wiedergabe und übersteht Neustarts, Stromausfälle und Aus/Ein-Tricks.
- 🔀 **Kein Doppelzählen** – läuft dasselbe Kind auf mehreren Boxen, zählt die Zeit trotzdem nur einmal.
- 🔔 **Faire Vorwarnung** – kurz vor Schluss eine freundliche **TTS-Ansage** („Noch 10 Minuten…") oder ein eigener Sound.
- ➕ **Belohnen leicht gemacht** – Extra-Minuten per Knopfdruck (+15/+30), Schieberegler oder Service.
- 🤒 **Ausnahmen** – Kind ist krank? Kontrolle für heute mit einem Schalter aussetzen.
- 🌍 **Mehrsprachig** – Oberfläche **und Entitäten** in Deutsch, Englisch, Spanisch, Französisch (+ Norwegisch, Griechisch, Japanisch).
- 🧩 **100 % über die Oberfläche, komplett lokal** – kein YAML, keine Automationen, keine Cloud nötig.

Eine Integrations-Instanz pro Kind: an eine `person`-Entität binden (oder einfach einen Namen
eingeben) und die zugehörigen `media_player`-Entitäten zuordnen. Die Integration zählt die
Medienzeit auf diesen Playern und hält die zugeordneten Player gestoppt, sobald das
Tagesbudget aufgebraucht ist.

## Installation

### HACS (empfohlen)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Jo-Highness&repository=media_time_guard&category=integration)

1. In **HACS** → **⋮ → Benutzerdefinierte Repositories** → `https://github.com/Jo-Highness/media_time_guard` als Kategorie **Integration** hinzufügen (entfällt, sobald die Integration im Standard-Store ist – dann einfach obigen Button nutzen).
2. *Media Time Guard* in HACS suchen und **herunterladen**.
3. Home Assistant **neu starten**.
4. *Einstellungen → Geräte & Dienste → Integration hinzufügen → „Media Time Guard"*.

### Manuell

1. Ordner `custom_components/media_time_guard/` nach `<config>/custom_components/` kopieren.
2. Home Assistant **neu starten**.
3. Integration unter *Einstellungen → Geräte & Dienste* hinzufügen.

## Einrichtung (eine Integration pro Kind)

Einrichtung und späteres Ändern nutzen dieselben vier Schritte des Konfigurations-Assistenten.
Alles ist später über *Konfigurieren* (Optionen) editierbar.

| Schritt | Was du einstellst |
|---|---|
| **1 · Person** | Ein **Name** (z. B. `Luke`), optional eine **`person`-Entität** und die zugeordneten **Media-Player**. Jeder Player gehört zu genau einer Person. |
| **2 · Tagesbudgets** | Minuten je Wochentag **Mo–So**. `0` sperrt Medien an dem Tag komplett. |
| **3 · Vorwarnung** | Ein/aus, **Restzeit-Schwelle** (Standard `10`) und die **Methode**: entweder eine **TTS**-Ansage (TTS-Engine + Nachricht wählen, `{minutes}` wird ersetzt) **oder** das Abspielen einer **Medien**-Content-ID (mit Content-Typ). |
| **4 · Reset** | Uhrzeit des **Tages-Resets** (Standard `00:00:00`), zu der Zähler und die einmalige Vorwarnung zurückgesetzt werden. |

## Entitäten

Jede konfigurierte Person bekommt ein eigenes **Gerät** mit diesen Entitäten
(`<person>` = der Namens-Slug):

| Entität | Typ | Zweck |
|---|---|---|
| `sensor.media_time_<person>_remaining` | Sensor (Messwert, Minuten) | Restliche Medienminuten heute, mit vielen Attributen (Budget, verbraucht, Wochentag, gesperrt/ausgesetzt, Extra-Minuten, letzter Reset). |
| `switch.media_time_<person>_suspend_today` | Schalter | **Heute aussetzen** – Kontrolle für den Rest des Tages pausieren (z. B. Kind ist krank). |
| `number.media_time_<person>_extend` | Nummer (0–600, Schritt 5) | **Extra-Minuten** für das heutige Budget. |
| `button.media_time_<person>_extend_15` | Taster | Schnell **+15 Minuten**. |
| `button.media_time_<person>_extend_30` | Taster | Schnell **+30 Minuten**. |

## Dienste

Alle Dienste erwarten den **Namen oder Slug** der Person.

| Dienst | Felder | Beschreibung |
|---|---|---|
| `media_time_guard.extend_time` | `person`, `minutes` (1–600) | Extra-Medienminuten für heute hinzufügen (erhöht das effektive Budget). |
| `media_time_guard.suspend_today` | `person`, `suspended` (bool) | Kontrolle für heute aussetzen oder fortsetzen. |
| `media_time_guard.reset_person` | `person` | Die heutigen Zähler einer Person manuell zurücksetzen. |

## Automatisierungs-Beispiele

**15 Minuten belohnen, wenn die Hausaufgaben erledigt sind:**

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

**Kontrolle an einem Krankheitstag automatisch aussetzen:**

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

## Fehlersuche / FAQ

**Die Wiedergabe stoppt nicht, obwohl das Budget leer ist.**
Prüfe, ob die `media_player`-Entitäten des Kindes im Assistenten wirklich dieser Person
zugeordnet sind und ob das Budget des aktuellen Wochentags nicht zu hoch steht. `0` bedeutet
„den ganzen Tag gesperrt".

**Es wird gezählt, obwohl (hörbar) nichts läuft.**
Gezählt wird anhand des `playing`-Status des Players – stummgeschaltete oder sehr leise
Wiedergabe zählt also mit. Das ist Absicht und hält die Durchsetzung manipulationssicher.

**Dasselbe Kind nutzt zwei Boxen – wird doppelt gezählt?**
Nein. Die Medienzeit einer Person wird nur einmal gezählt, egal wie viele der zugeordneten
Player gleichzeitig laufen.

**Debug-Logging aktivieren**, um Zählung und Durchsetzung nachzuvollziehen:

```yaml
logger:
  logs:
    custom_components.media_time_guard: debug
```

Mehr Details: ausführliche Anleitungen in [`docs/user/`](docs/user) (de, en, es, fr, nb, el, ja)
und die Architektur in [`docs/TECHNICAL.md`](docs/TECHNICAL.md).

## Mitwirken

Beiträge sind willkommen. Bitte lies [`CONTRIBUTING.md`](CONTRIBUTING.md) und öffne ein Issue
oder einen Pull Request auf [GitHub](https://github.com/Jo-Highness/media_time_guard).

## Lizenz

Veröffentlicht unter der [MIT-Lizenz](LICENSE).
