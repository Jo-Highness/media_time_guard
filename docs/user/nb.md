# Media Time Guard – Brukerveiledning (Norsk bokmål)

Media Time Guard begrenser en persons daglige medietid på vedkommendes mediespillere
(f.eks. Sonos One) og håndhever grensen pålitelig – selv når barn prøver å omgå den.

## 1. Installasjon

**Via HACS (anbefalt)**
1. Åpne HACS → ⋮-menyen → *Egendefinerte arkiver*.
2. Legg til arkiv-URL-en, kategori **Integrasjon**.
3. Søk etter *Media Time Guard* og last ned.
4. Start Home Assistant på nytt.

**Manuelt:** kopier mappen `custom_components/media_time_guard/` til
`<config>/custom_components/` og start HA på nytt.

## 2. Sette opp en person

*Innstillinger → Enheter og tjenester → Legg til integrasjon → «Media Time Guard».*
Det opprettes én oppføring per person. Veiviseren har fire trinn:

1. **Person og spillere**
   - **Navn**: f.eks. `Luke`. (Barn har ofte ingen `person`-entitet – skriv bare navnet.)
   - **Person-entitet** (valgfritt): hvis den finnes.
   - **Mediespillere**: én eller flere. En spiller kan bare tilhøre **én** person.
2. **Daglige budsjetter**: minutter for mandag–søndag. `0` = sperret hele dagen.
3. **Advarsel** (valgfritt): på/av, terskel for gjenværende tid (minutter), metode:
   - **TTS**: velg en TTS-motor + annonseringstekst. `{minutes}` erstattes med gjenværende minutter.
   - **Media**: en medie-URL / innholds-ID som spilles av.
4. **Nullstilling**: tidspunktet telleren nullstilles (standard `00:00`).

Endre senere via **Konfigurer**-knappen på oppføringen.

## 3. Hva skjer

- Tiden telles bare mens minst én tildelt spiller **spiller** (`playing`).
- Avspilling på flere høyttalere samtidig telles **ikke** dobbelt.
- Når budsjettet er brukt opp, stoppes alle spillere og sperres resten av dagen. Å slå
  høyttaleren av/på eller starte HA på nytt opphever **ikke** sperren.
- Like før slutten gis en engangsadvarsel (hvis aktivert).

## 4. Entiteter per person

| Entitet | Betydning |
|---|---|
| `sensor.media_time_<person>_remaining` | gjenværende minutter i dag |
| `switch.media_time_<person>_suspend_today` | sett håndheving på pause i dag (f.eks. syk) |
| `number.media_time_<person>_extend` | ekstra minutter i dag (absolutt verdi) |
| `button.media_time_<person>_extend_15` / `_extend_30` | +15 / +30 minutter |

Sensorattributter: `budget_minutes`, `used_minutes`, `remaining_minutes`, `is_locked`,
`is_suspended`, `extra_minutes_today`, `warned_today`.

## 5. Vanlige oppgaver

- **Gi mer tid:** trykk +15/+30-knappen, sett number-entiteten eller kall
  `media_time_guard.extend_time` med `person` og `minutes`.
- **Ingen grense i dag (barn sykt):** slå på *Suspend Today*-bryteren eller kall
  `media_time_guard.suspend_today` med `suspended: true`.
- **Nullstill manuelt:** kall `media_time_guard.reset_person`.

## 6. Kjent begrensning

Tellingen er basert på tilstanden `playing`. **Dempet eller svært lav avspilling telles
likevel**, fordi spilleren fortsatt «spiller».
