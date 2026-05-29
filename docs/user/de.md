# Media Time Guard – Benutzerhandbuch (Deutsch)

Media Time Guard begrenzt die tägliche Medienzeit einer Person auf deren Media-Playern
(z. B. Sonos One) und setzt die Grenze zuverlässig durch – auch wenn Kinder versuchen, sie
zu umgehen.

## 1. Installation

**Über HACS (empfohlen)**
1. HACS öffnen → Menü ⋮ → *Benutzerdefinierte Repositories*.
2. Die Repo-URL hinzufügen, Kategorie **Integration**.
3. *Media Time Guard* suchen und herunterladen.
4. Home Assistant neu starten.

**Manuell:** Ordner `custom_components/media_time_guard/` nach `<config>/custom_components/`
kopieren und HA neu starten.

## 2. Eine Person einrichten

*Einstellungen → Geräte & Dienste → Integration hinzufügen → „Media Time Guard“.*
Pro Person wird ein eigener Eintrag angelegt. Der Assistent hat vier Schritte:

1. **Person & Player**
   - **Name**: z. B. `Luke`. (Kinder haben oft keine eigene `person`-Entität – dann einfach
     den Namen eintippen.)
   - **Person-Entität** (optional): falls vorhanden.
   - **Media-Player**: eine oder mehrere. Ein Player darf nur **einer** Person zugeordnet sein.
2. **Tagesbudgets**: Minuten für Montag bis Sonntag. `0` = an diesem Tag komplett gesperrt.
3. **Warnung** (optional): aktiv ja/nein, Restzeit-Schwelle (Minuten), Methode:
   - **TTS**: TTS-Engine wählen + Ansagetext. `{minutes}` wird durch die Restminuten ersetzt.
   - **Medien**: eine Medien-URL / Content-ID, die abgespielt wird.
4. **Reset**: Uhrzeit, zu der jeden Tag neu gezählt wird (Standard `00:00`).

Später ändern: Eintrag → **Konfigurieren**.

## 3. Was passiert?

- Gezählt wird nur, wenn mindestens ein zugeordneter Player **spielt** (`playing`).
- Gleichzeitiges Abspielen auf mehreren Boxen zählt **nicht** doppelt.
- Ist das Budget aufgebraucht, werden alle Player **gestoppt** und für den Rest des Tages
  gesperrt. Aus- und Wiedereinschalten oder ein HA-Neustart hebt die Sperre **nicht** auf.
- Kurz vor Ablauf gibt es (falls aktiviert) **einmalig** eine Warnung.

## 4. Entitäten pro Person

| Entität | Bedeutung |
|---|---|
| `sensor.media_time_<person>_remaining` | verbleibende Minuten heute |
| `switch.media_time_<person>_suspend_today` | Kontrolle heute aussetzen (z. B. krank) |
| `number.media_time_<person>_extend` | Extra-Minuten heute (absoluter Wert) |
| `button.media_time_<person>_extend_15` / `_extend_30` | +15 / +30 Minuten |

Der Sensor liefert u. a. die Attribute `budget_minutes`, `used_minutes`, `remaining_minutes`,
`is_locked`, `is_suspended`, `extra_minutes_today`, `warned_today`.

## 5. Häufige Aufgaben

- **Mehr Zeit geben:** Button +15/+30 drücken, die Number-Entität setzen oder den Service
  `media_time_guard.extend_time` mit `person` und `minutes` aufrufen.
- **Heute keine Begrenzung (Kind krank):** Schalter *Suspend Today* einschalten oder Service
  `media_time_guard.suspend_today` mit `suspended: true`.
- **Manuell zurücksetzen:** Service `media_time_guard.reset_person`.

## 6. Hinweis / Limitierung

Gezählt wird der Zustand `playing`. **Stummes oder sehr leises Abspielen zählt trotzdem**,
weil der Player weiterhin „spielt“.
