---
service: media_time_guard
typ: requirements
version: 1.1
status: current
stand: 2026-06-18
quellen: [MDs/sonosbudget.md (Ursprungsauftrag), README.md, custom_components/media_time_guard]
---

# Anforderungen: Media Time Guard (HA Custom Integration)

> Code-unabhängige Soll-Beschreibung für eine Neuentwicklung von Grund auf (WAS/WARUM).

## 1. Zweck & Kontext
HACS-installierbare Home-Assistant-Integration (Domain `media_time_guard`), die die **tägliche
Medien-/Hörzeit von Personen** auf zugeordneten Media-Playern (primär Sonos, generell alle
`media_player`) **robust und manipulationssicher begrenzt**.
- **Nutzer:** HA-Haushalt (Eltern konfigurieren, Kinder werden begrenzt).
- **Use-Cases:** Tagesbudget je Person/Wochentag durchsetzen; Warnung vor Ablauf; Extra-Minuten gewähren;
  Kontrolle tageweise aussetzen.

## 2. Geltungsbereich
**In Scope:** UI-Konfiguration (Config-/Options-Flow), Zeitzählung über Player-State, Durchsetzung
(Stoppen/Sperren), Warnungen (TTS oder Media-URL), Extra-Minuten, Aussetzen, Reset.
**Out of Scope:** Inhalts-/Altersfilter, Zeitbegrenzung für Nicht-Media-Geräte, Cloud-Komponenten.

## 3. Funktionale Anforderungen
- **FR-1 Konfiguration (nur UI):** Personen wählen (Bindung an `person`-Entitäten); je Person beliebig viele
  `media_player` zuordnen – **ein Player nur EINER Person** (Validierung mit Fehlermeldung).
- **FR-2 Budgets:** je Person und Wochentag (Mo–So) Minutenbudget (0 = an dem Tag gesperrt).
- **FR-3 Warnung (optional je Person):** Schwelle in Restminuten + Methode TTS (Engine + Ansagetext mit
  Restminuten-Platzhalter) ODER abzuspielende Media-URL/Content-ID.
- **FR-4 Reset:** konfigurierbare Reset-Uhrzeit (Default 00:00) für die Tageszählung.
- **FR-5 Entitäten je Person:** `sensor.*_remaining` (verbleibende Minuten heute; Attribute budget/used/
  remaining/weekday/is_playing/is_locked/is_suspended/extra_minutes_today/warned_today/last_reset);
  `switch.*_suspend_today` (Aussetzen); `number.*_extend` bzw. Button/Service für Extra-Minuten; optional
  Komfort-Buttons (+15/+30).
- **FR-6 Services:** `extend_time(person, minutes)`, `suspend_today(person, suspended)`, `reset_person(person)`
  (mit `services.yaml` + Selektoren).
- **FR-7 Durchsetzung:** bei aufgebrauchtem Budget Wiedergabe stoppen/sperren; bei `suspend` nur informativ
  weiterzählen, kein Stoppen.

## 4. Nicht-funktionale Anforderungen
- **NFR-1 Async/Non-Blocking:** vollständig async, keine blockierenden I/O.
- **NFR-2 Präzise Zählung:** nur State `playing` zählt; Wand-Uhr-Zeit, in der **mind. ein** Player der Person
  spielt (keine Doppelzählung bei mehreren Boxen).
- **NFR-3 Persistenz:** Tageszählerstände/Status überleben HA-Neustart (Store).
- **NFR-4 Manipulationssicherheit/Robustheit:** robuste Durchsetzung; Edge-Cases (unavailable/Neustart) sauber.
- **NFR-5 HACS-/HA-Konformität:** manifest.json, hacs.json, korrekte Struktur, nicht-deprecated APIs, hassfest-valide.

## 5. Externe Schnittstellen & Verträge
- **HA-Entitäten/Services** s. FR-5/FR-6 (stabile Entity-ID-/Service-Namen, `services.yaml`).
- **Eingang:** `media_player`-States; **Ausgang:** media_player-Stop, TTS-/Media-Play-Service.
- **Übersetzungen:** mehrsprachige strings/translations.

## 6. Datenmodell
- **Person-Konfig:** zugeordnete Player[], Wochentags-Budgets[7], Warnoptionen, Reset-Zeit.
- **Laufzeit/Store je Person:** used_minutes_today, extra_minutes_today, is_suspended, warned_today, last_reset,
  Checkpoint-Zeitstempel der laufenden Zählung.

## 7. Integrationen & Abhängigkeiten
- Home Assistant (person, media_player, TTS), HACS für Verteilung. Keine externen Server.

## 8. Constraints & Rahmenbedingungen
- **C-1:** reine UI-Konfiguration, kein YAML-Setup. **C-2:** Zählung event-getrieben
  (`async_track_state_change_event`) **plus** periodischer Timer (≈20–30 s) mit Checkpoints gegen Doppelzählung.
- **C-3:** ein Player exklusiv einer Person. **C-4:** HA-Zeitzone für Reset/Wochentag.

## 9. Designentscheidungen (Rationale)
- **Hybride Zählung (Events + Timer):** Live-Sensor + rechtzeitige Warnung/Sperre trotz seltener Events.
- **Suspend statt Löschen:** Ausnahmen (Kind krank) ohne Datenverlust.

## 10. Akzeptanzkriterien
- **A-1:** Player-Zuordnung zu zwei Personen für denselben Player wird im Flow abgelehnt.
- **A-2:** Nur `playing` erhöht `used_minutes`; gleichzeitiges Spielen zweier Boxen zählt einfach.
- **A-3:** Bei Budget 0 oder aufgebraucht wird die Wiedergabe gestoppt/gesperrt.
- **A-4:** Warnung löst bei Erreichen der Restschwelle per gewählter Methode aus (einmal/Tag).
- **A-5:** `extend_time` erhöht das effektive Budget heute; Reset zur konfigurierten Uhrzeit setzt zurück.
- **A-6:** Nach HA-Neustart bleiben Tagesstände/Status erhalten.

## 11. Annahmen & offene Punkte
- Personen werden in HA als `person` gepflegt; Sonos exemplarisch, generell media_player.

## 12. Änderungshistorie
| Version | Datum | Änderung |
|---|---|---|
| 1.0 | 2026-05 | Erstfassung = Ursprungsauftrag (MDs/sonosbudget.md), Code v1.0.x |
| 1.1 | 2026-06-18 | Als Clean-Room-requirements-Doc strukturiert (Stand Code v1.0.1) |
