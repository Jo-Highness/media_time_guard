---
service: media_time_guard
typ: requirements
version: 1.3
status: current
stand: 2026-10-27
quellen: [MDs/sonosbudget.md (Ursprungsauftrag), README.md, ADR 9ba35275 (dauerhafte Sperre), QA-Suite e07cc73c]
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
  Kontrolle tageweise aussetzen; Person bis auf Widerruf komplett sperren (z.B. Medienverbot).

## 2. Geltungsbereich
**In Scope:** UI-Konfiguration (Config-/Options-Flow), Zeitzählung über Player-State, Durchsetzung
(Stoppen/Sperren), dauerhafte Sperre je Person, Warnungen (TTS oder Media-URL), Extra-Minuten,
Aussetzen, Reset.
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
  „nicht gesperrt“ gelesen.

## 5. Externe Schnittstellen & Verträge
- **HA-Entitäten/Services** s. FR-5/FR-6 (stabile Entity-ID-/Service-Namen, `services.yaml`).
- **Service-Vertrag `media_time_guard.set_blocked`:** Felder `person` (Name) ODER `config_entry_id`, Pflichtfeld
  `blocked` (bool). Unbekannte Person/Eintrag → übersetzter Fehler. Idempotent (wiederholtes Setzen desselben
  Werts ändert nichts).
- **Schalter `switch.media_time_<slug>_blocked`:** an = gesperrt; Zustand spiegelt den persistierten Sperrstatus.
- **Diagnostics:** enthält den Sperrstatus (`is_blocked`).
- **Eingang:** `media_player`-States; **Ausgang:** media_player-Stop, TTS-/Media-Play-Service.
- **Übersetzungen:** mehrsprachige strings/translations (de, el, en, es, fr, ja, nb).

## 6. Datenmodell
- **Person-Konfig:** zugeordnete Player[], Wochentags-Budgets[7], Warnoptionen, Reset-Zeit.
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

## 11. Annahmen, offene Punkte & akzeptierte Risiken
- Personen werden über einen Namen identifiziert (eine `person`-Entität ist nicht nötig); Sonos exemplarisch, generell media_player.
- **Akzeptiert:** keine automatische Aufhebung der Sperre (kein Ablaufdatum).
- **Akzeptiert:** kurzes Anspielen vor dem Stopp möglich (C-5).
- **Akzeptiert:** Downgrade auf ≤ v1.2.0 verliert die Sperre (ältere Versionen kennen den Zustand nicht).

## 12. Änderungshistorie
| Version | Datum | Änderung |
|---|---|---|
| 1.0 | 2026-05 | Erstfassung = Ursprungsauftrag (MDs/sonosbudget.md), Code v1.0.x |
| 1.1 | 2026-06-18 | Als Clean-Room-requirements-Doc strukturiert (Stand Code v1.0.1) |
| 1.2 | 2026-10-16 | Ungenutzte `person`-Bindung entfernt, `config_entry_id` für Services (Stand Code v1.2.0) |
| 1.3 | 2026-10-27 | Dauerhafte Sperre je Person (FR-8, Schalter + `set_blocked`, Vorrangregel, Persistenz, A-7..A-12; ADR 9ba35275; Stand Code v1.3.0) |
