---
service: media_time_guard
typ: requirements
version: 1.4
status: current
stand: 2026-11-02
quellen: [MDs/sonosbudget.md (Ursprungsauftrag), README.md, ADR 9ba35275 (dauerhafte Sperre), QA-Suite e07cc73c, ADR f1d19c22 (Benutzerprüfung)]
---

# Anforderungen: Media Time Guard (HA Custom Integration)

> Code-unabhängige Soll-Beschreibung für eine Neuentwicklung von Grund auf (WAS/WARUM).

## 1. Zweck & Kontext
HACS-installierbare Home-Assistant-Integration (Domain `media_time_guard`), die die **tägliche
Medien-/Hörzeit von Personen** auf zugeordneten Media-Playern (primär Sonos, generell alle
`media_player`) **robust und manipulationssicher begrenzt** und Personen bei Bedarf **dauerhaft
sperren** kann.
- **Nutzer:** HA-Haushalt (Eltern konfigurieren, Kinder werden begrenzt).
- **Use-Cases:** Tagesbudget je Person/Wochentag durchsetzen; Warnung vor Ablauf; Extra-Minuten gewähren;
  Kontrolle tageweise aussetzen; Person bis auf Widerruf komplett sperren (z.B. Medienverbot);
  Änderungen nur durch berechtigte Benutzer zulassen (z.B. nicht durch das Kind am Wandtablet).

## 2. Geltungsbereich
**In Scope:** UI-Konfiguration (Config-/Options-Flow), Zeitzählung über Player-State, Durchsetzung
(Stoppen/Sperren), dauerhafte Sperre je Person, Warnungen (TTS oder Media-URL), Extra-Minuten,
Aussetzen, Reset, serverseitige Benutzerprüfung für alle verändernden Aktionen.
**Out of Scope:** Inhalts-/Altersfilter, Zeitbegrenzung für Nicht-Media-Geräte, Cloud-Komponenten,
zeitgesteuertes automatisches Ende der Sperre (bewusst den HA-Automationen überlassen).

## 3. Funktionale Anforderungen
- **FR-1 Konfiguration (nur UI):** Personen per eindeutigem Namen anlegen (keine Bindung an `person`-Entitäten);
  je Person beliebig viele `media_player` zuordnen – **ein Player nur EINER Person** (Validierung mit Fehlermeldung).
- **FR-2 Budgets:** je Person und Wochentag (Mo–So) Minutenbudget (0 = an dem Tag gesperrt).
- **FR-3 Warnung (optional je Person):** Schwelle in Restminuten + Methode TTS (Engine + Ansagetext mit
  Restminuten-Platzhalter) ODER abzuspielende Media-URL/Content-ID.
- **FR-4 Reset:** konfigurierbare Reset-Uhrzeit (Default 00:00) für die Tageszählung.
- **FR-5 Entitäten je Person:** `sensor.*_remaining` (verbleibende Minuten heute; Attribute budget/used/
  remaining/weekday/is_playing/is_locked/is_suspended/**is_blocked**/extra_minutes_today/warned_today/last_reset);
  `switch.*_suspend_today` (Aussetzen); **`switch.*_blocked` (dauerhafte Sperre, Anzeigename DE „Gesperrt“,
  EN „Blocked“, übersetzt)**; `number.*_extend` bzw. Button/Service für Extra-Minuten; optional
  Komfort-Buttons (+15/+30).
- **FR-6 Services:** `extend_time(person, minutes)`, `suspend_today(person, suspended)`, `reset_person(person)`,
  **`set_blocked(person, blocked: bool)`**; alternativ zu `person` jeweils `config_entry_id` (ab v1.2.0);
  genau eines von beiden ist anzugeben (mit `services.yaml` + Selektoren, übersetzte Fehler).
- **FR-7 Durchsetzung:** bei aufgebrauchtem Budget Wiedergabe stoppen/sperren; bei `suspend` nur informativ
  weiterzählen, kein Stoppen.
- **FR-8 Dauerhafte Sperre (ab v1.3.0):**
  - Solange die Sperre aktiv ist, wird **jede Wiedergabe auf allen Playern der Person sofort gestoppt**,
    unabhängig vom Restbudget.
  - **Vorrangregel:** Sperre > Aussetzen (`suspend_today`) > Budget inkl. Extra-Minuten. Weder Aussetzen
    noch Extra-Minuten heben eine aktive Sperre auf.
  - Während der Sperre wird **keine Medienzeit gezählt** und **keine Vorwarnung** ausgegeben; die Sperrdauer
    wird auch nach dem Entsperren nicht nachträglich berechnet.
  - Der Budget-Sperrzustand `is_locked` wird durch die Sperre **nicht** verändert (getrennte Zustände).
  - Die Sperre **übersteht Tagesreset, `reset_person` und HA-Neustart** und **endet nur durch explizites
    Ausschalten** (Schalter oder `set_blocked(blocked: false)`).
  - Nach dem Entsperren gilt sofort die normale Tageslogik (Restbudget, Aussetzen, Warnung) des aktuellen Tages.
  - Schalter und Service wirken identisch (eine Wahrheitsquelle je Person).
- **FR-9 Benutzerprüfung (ab v1.4.0):**
  - Je Person einstellbar: **„Änderungen beschränken“** (Standard **aus** = jeder darf ändern, Verhalten wie ≤ v1.3)
    und eine Liste **zusätzlich erlaubter Benutzer** (HA-Benutzer ohne Adminrechte).
  - Geschützt sind **alle verändernden Wege**: Extra-Minuten (Buttons, Zahl, `extend_time`), Aussetzen
    (Schalter, `suspend_today`), dauerhafte Sperre (Schalter, `set_blocked`, an UND aus), `reset_person`.
    Lesen (Sensor, Attribute) bleibt für alle möglich.
  - Bei aktiver Beschränkung dürfen: **Aufrufe ohne Benutzer** (Automationen, Zeitpläne, System),
    **aktive Administratoren** (immer, da sie die Beschränkung ohnehin abschalten könnten) und **aktive Benutzer
    der Erlaubt-Liste**. Alle anderen – auch **unbekannte/gelöschte oder deaktivierte** Benutzer – werden abgewiesen
    (fail-closed).
  - Die Prüfung erfolgt **serverseitig in der Integration**, also unabhängig davon, ob über Dashboard, Assist,
    REST/WebSocket-API oder ein vom Benutzer gestartetes Skript/Szene aufgerufen wird.
  - Abgewiesene Aufrufe ändern **nichts** (keine Teilwirkung), liefern einen Berechtigungsfehler
    (HA-Standard „Unauthorized“) und werden mit Person, Aktion und Benutzer als Warnung protokolliert.
  - Die Auswahl im Formular bietet nur aktive, echte Benutzer ohne Adminrechte an; nicht mehr existierende
    Benutzer verschwinden beim nächsten Bearbeiten aus der Liste, ohne das Formular zu blockieren.

## 4. Nicht-funktionale Anforderungen
- **NFR-1 Async/Non-Blocking:** vollständig async, keine blockierenden I/O.
- **NFR-2 Präzise Zählung:** nur State `playing` zählt; Wand-Uhr-Zeit, in der **mind. ein** Player der Person
  spielt (keine Doppelzählung bei mehreren Boxen).
- **NFR-3 Persistenz:** Tageszählerstände/Status überleben HA-Neustart (Store). **Das Setzen/Aufheben der Sperre
  wird sofort (nicht verzögert) persistiert**, damit ein Neustart im Speicherfenster die Sperre nicht verliert
  (fail-closed).
- **NFR-4 Manipulationssicherheit/Robustheit:** robuste Durchsetzung; Edge-Cases (unavailable/Neustart) sauber.
- **NFR-5 HACS-/HA-Konformität:** manifest.json, hacs.json, korrekte Struktur, nicht-deprecated APIs, hassfest-valide.
- **NFR-6 Abwärtskompatibilität:** Speicherstände älterer Versionen ohne Sperr-Information werden als
  „nicht gesperrt“ gelesen. Einträge ohne Zugriffseinstellungen (≤ v1.3) verhalten sich wie „nicht beschränkt“;
  keine Migration nötig.
- **NFR-7 Erzwungene Prüfung:** Jeder Schreibpfad muss die Berechtigung prüfen, **bevor** Zustand verändert wird;
  ein neuer Schreibpfad darf die Prüfung nicht versehentlich auslassen können. Parallele Aufrufe verschiedener
  Benutzer werden jeweils dem richtigen Benutzer zugeordnet.

## 5. Externe Schnittstellen & Verträge
- **HA-Entitäten/Services** s. FR-5/FR-6 (stabile Entity-ID-/Service-Namen, `services.yaml`).
- **Service-Vertrag `media_time_guard.set_blocked`:** Felder `person` (Name) ODER `config_entry_id`, Pflichtfeld
  `blocked` (bool). Unbekannte Person/Eintrag → übersetzter Fehler. Idempotent (wiederholtes Setzen desselben
  Werts ändert nichts).
- **Schalter `switch.media_time_<slug>_blocked`:** an = gesperrt; Zustand spiegelt den persistierten Sperrstatus.
- **Diagnostics:** enthält den Sperrstatus (`is_blocked`); die Erlaubt-Liste (Benutzer-IDs) wird geschwärzt.
- **Berechtigungsfehler:** abgewiesene Aufrufe liefern `Unauthorized` (WebSocket/REST-Code `unauthorized`,
  bricht aufrufende Skripte ab); Frontend zeigt die HA-Standardmeldung.
- **Eingang:** `media_player`-States; **Ausgang:** media_player-Stop, TTS-/Media-Play-Service.
- **Übersetzungen:** mehrsprachige strings/translations (de, el, en, es, fr, ja, nb).

## 6. Datenmodell
- **Person-Konfig:** zugeordnete Player[], Wochentags-Budgets[7], Warnoptionen, Reset-Zeit,
  **restrict_changes (bool, Standard false), allowed_users[] (HA-Benutzer-IDs)**.
- **Laufzeit/Store je Person:** used_minutes_today, extra_minutes_today, is_suspended, warned_today, last_reset,
  Checkpoint-Zeitstempel der laufenden Zählung, **is_blocked (bool, nicht tagesgebunden, vom Tagesreset
  ausgenommen)**.

## 7. Integrationen & Abhängigkeiten
- Home Assistant (media_player, TTS), HACS für Verteilung. Keine externen Server.

## 8. Constraints & Rahmenbedingungen
- **C-1:** reine UI-Konfiguration, kein YAML-Setup. **C-2:** Zählung event-getrieben
  (State-Change-Events) **plus** periodischer Timer (≈20–30 s) mit Checkpoints gegen Doppelzählung.
- **C-3:** ein Player exklusiv einer Person. **C-4:** HA-Zeitzone für Reset/Wochentag.
- **C-5:** Durchsetzung erfolgt reaktiv (Stopp nach Erkennen von `playing`); ein kurzes Anspielen vor dem
  Stopp ist technisch nicht vermeidbar.

## 9. Designentscheidungen (Rationale)
- **Hybride Zählung (Events + Timer):** Live-Sensor + rechtzeitige Warnung/Sperre trotz seltener Events.
- **Suspend statt Löschen:** Ausnahmen (Kind krank) ohne Datenverlust.
- **Sperre als eigener Zustand statt Budget 0 / `is_locked`** (ADR 9ba35275): Budget-Konfiguration und
  Tageszähler bleiben unangetastet; nach dem Entsperren ist der Tag ohne Nacharbeit korrekt; eindeutige
  Vorrangregel statt Wechselwirkungen mit Aussetzen/Extra-Minuten.
- **Kein Ablaufdatum:** bewusst einfach; zeitgesteuertes Entsperren über HA-Automationen.
- **Benutzerprüfung in der Integration statt nur im Dashboard** (ADR f1d19c22): HA kennt keine Rechte pro
  Entität; Dashboard-Sichtbarkeit ist nur Oberfläche. **Je Person** statt global (kein globaler Eintrag; ältere
  Geschwister können unbeschränkt bleiben). **Admins immer erlaubt** (eine Sperre gegen Admins wäre wirkungslos).
  **Aufrufe ohne Benutzer erlaubt**, sonst wären Automationen/Zeitpläne der Eltern unbrauchbar.
  **Standard „aus“** für reibungsloses Update.

## 10. Akzeptanzkriterien
- **A-1:** Player-Zuordnung zu zwei Personen für denselben Player wird im Flow abgelehnt.
- **A-2:** Nur `playing` erhöht `used_minutes`; gleichzeitiges Spielen zweier Boxen zählt einfach.
- **A-3:** Bei Budget 0 oder aufgebraucht wird die Wiedergabe gestoppt/gesperrt.
- **A-4:** Warnung löst bei Erreichen der Restschwelle per gewählter Methode aus (einmal/Tag).
- **A-5:** `extend_time` erhöht das effektive Budget heute; Reset zur konfigurierten Uhrzeit setzt zurück.
- **A-6:** Nach HA-Neustart bleiben Tagesstände/Status erhalten.
- **A-7:** Bei aktiver Sperre wird jede Wiedergabe auf allen Playern der Person gestoppt, auch mit Restbudget,
  bei aktivem `suspend_today` und nach Extra-Minuten.
- **A-8:** Während der Sperre steigt `used_minutes` nicht und es erfolgt keine Warnung; `is_locked` bleibt unverändert.
- **A-9:** Die Sperre bleibt nach Tagesreset, `reset_person` und HA-Neustart aktiv; sie endet nur durch Ausschalten.
- **A-10:** Schalter und `set_blocked` (per `person` oder `config_entry_id`) setzen denselben Zustand; `is_blocked`
  erscheint am Restzeit-Sensor und in Diagnostics.
- **A-11:** Nach dem Entsperren gelten Restbudget/Aussetzen/Warnung des aktuellen Tages; die Sperrzeit wurde nicht gezählt.
- **A-12:** Ein Speicherstand ohne Sperr-Information (≤ v1.2.x) wird als „nicht gesperrt“ geladen.
- **A-13:** Bei aktiver Beschränkung wird ein Nicht-Admin ohne Freigabe bei allen geschützten Aktionen
  (Buttons, Zahl, beide Schalter an/aus, `extend_time`, `suspend_today`, `set_blocked`, `reset_person`)
  abgewiesen; der Zustand bleibt unverändert; eine Warnung wird protokolliert.
- **A-14:** Admins, freigegebene Benutzer und Aufrufe ohne Benutzer (Automation) dürfen weiterhin ändern.
- **A-15:** Deaktivierte oder nicht existierende Benutzer werden abgewiesen, auch wenn sie in der Liste stehen.
- **A-16:** Ein vom gesperrten Benutzer gestartetes Skript, das eine geschützte Aktion ausführt, wird abgewiesen.
- **A-17:** Ohne Beschränkung (Standard bzw. Eintrag aus ≤ v1.3) verhält sich alles wie bisher.
- **A-18:** Gleichzeitige Aufrufe eines Admins und eines gesperrten Benutzers: nur der des Admins wirkt.

## 11. Annahmen, offene Punkte & akzeptierte Risiken
- Personen werden über einen Namen identifiziert (eine `person`-Entität ist nicht nötig); Sonos exemplarisch, generell media_player.
- **Akzeptiert:** keine automatische Aufhebung der Sperre (kein Ablaufdatum).
- **Akzeptiert:** kurzes Anspielen vor dem Stopp möglich (C-5).
- **Akzeptiert:** Downgrade auf ≤ v1.2.0 verliert die Sperre (ältere Versionen kennen den Zustand nicht).
- **Akzeptierte Restrisiken der Benutzerprüfung** (der Betreiber muss gegensteuern, ADR f1d19c22):
  - (a) **Automationen laufen ohne Benutzer.** Kann ein gesperrter Benutzer eine Automation auslösen
    (`automation.trigger`, oder per Zustandsauslöser über einen Helfer/Taster, den er bedienen darf), die eine
    geschützte Aktion ausführt, greift die Prüfung nicht. HA kann den ursprünglichen Benutzer nicht zurückverfolgen.
  - (b) **Sprachsatelliten, HomeKit, MQTT, Zigbee/KNX** rufen ohne Benutzer auf → erlaubt. Die Entitäten deshalb
    nicht für Assist-Satelliten/HomeKit freigeben.
  - (c) **Alexa/Google über die Cloud** laufen mit dem (Admin-)Cloud-Benutzer → erlaubt.
  - (d) Abgewiesene Button-Drücke aktualisieren trotzdem den Zeitstempel der Button-Entität (HA-Kern schreibt
    ihn vor der Aktion); der Zustand der Person ändert sich nicht.
  - (e) Das Frontend zeigt nur die unübersetzte HA-Meldung „Unauthorized“.
  - (f) **Downgrade auf ≤ v1.3** entfernt den Schutz stillschweigend.

## 12. Änderungshistorie
| Version | Datum | Änderung |
|---|---|---|
| 1.0 | 2026-05 | Erstfassung = Ursprungsauftrag (MDs/sonosbudget.md), Code v1.0.x |
| 1.1 | 2026-06-18 | Als Clean-Room-requirements-Doc strukturiert (Stand Code v1.0.1) |
| 1.2 | 2026-10-16 | Ungenutzte `person`-Bindung entfernt, `config_entry_id` für Services (Stand Code v1.2.0) |
| 1.3 | 2026-10-27 | Dauerhafte Sperre je Person (FR-8, Schalter + `set_blocked`, Vorrangregel, Persistenz, A-7..A-12; ADR 9ba35275; Stand Code v1.3.0) |
| 1.4 | 2026-11-02 | Benutzerprüfung je Person (FR-9, NFR-7, A-13..A-18, Restrisiken a–f; ADR f1d19c22; Stand Code v1.4.0) |
