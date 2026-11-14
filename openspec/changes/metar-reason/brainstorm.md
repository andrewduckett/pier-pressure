## Story

#218 metar-reason — the verdict says what the pier's chosen airport reports now.
https://github.com/andrewduckett/pier-pressure/issues/218

The issue thread had no comments at either fetch.

The user pre-authorized the recommended answer to every question in this
brainstorm, so rows the agent recommended are recorded as `User`. No question
was left without a recommendation.

## Decisions

| # | Question | Answer | Source |
|---|---|---|---|
| D1 | What does "observation" mean, and where does it apply? | A report of what the sky was at one moment, measured at one place, such as an airport's METAR. Unlike a series it is not a forecast, covers no hours and never fills a variable. Shared glossary: it spans conditions, the verdict document and health. | User |
| D2 | How does a pier name its airport? | An optional per-pier `metar_station`: four letters or digits, starting with a letter, stored in upper case. Anything else is a configuration error that names the field, and skips the pier. | User |
| D3 | Is `metar_station` a tuning knob? | No. Like the horizon and equipment, it describes the site, so the "three tuning knobs and no others" rule stands. | Evidence: openspec/specs/night-verdict/spec.md |
| D4 | Does the add-on's Configuration form get a field? | No. Add-on users set `metar_station` in `config.yaml`, as they do `dew_margin`; `DOCS.md` says how. | Evidence: ha-addon/DOCS.md (dew_margin) |
| D5 | Is METAR a provider in the provider order? | No. It is fetched per pier when the pier names a station, never fills a variable, and is not listed in `conditions.providers`. | User |
| D6 | Which time is the observation's time? | The report's `obsTime`, when the station measured, not the nominal `reportTime` or the fetch time. | Evidence: aviationweather.gov METAR JSON |
| D7 | When is an observation ignored? | When it was observed more than 90 minutes before the evaluation instant, or after it. An ignored observation adds no field value and no reason line. | User |
| D8 | What does the verdict document gain? | One additive top-level key, `observation`, after `agreement`: null when there is no usable observation, else `station`, `observed_at`, the report's overall `cover` code and `clouds` (each `cover` and `base_ft` above ground, lowest first, as reported). | User |
| D9 | How is the reason line worded? | One line, with the observation time as a UTC timestamp so the card shows it in local time, such as `At 2026-11-14T20:54:00Z, KBOS reported few cloud at 3,000 ft and broken cloud at 4,200 ft.` A relative age would go stale on the dashboard between recomputes. | User |
| D10 | What does a report with no cloud layers say? | `no cloud below 12,000 ft`, because automated stations see no higher. A CAVOK report says `no cloud below 5,000 ft`, which is all CAVOK promises. | User |
| D11 | Where does the reason line go, and on which verdicts? | On every verdict with a usable observation, NO-GO included, after the verdict's own terms and before the equipment notes. | User |
| D12 | Does the observation change the gates, score or confidence? | No. Confidence is `metar-confidence`'s job. | Evidence: #218 Scope |
| D13 | How does the METAR fetch show in provider health? | A `METAR health` sensor (key `metar`), only for piers that name a station. Its `variables` is empty, its issue time is the observation time, and an empty response is a failed fetch. A report too old to use is still a successful fetch. | User |
| D14 | Does a fetch failure fail the verdict? | No. The verdict is produced with `observation` null, and only health shows the failure. | Evidence: #218 Scope |
| D15 | Does the narrative or the card need changes? | No. Both read `reasons`, so the line reaches them as it is. | Evidence: pierpressure/explain/prompt.py, openspec/specs/night-card/spec.md |

## Changes from the story

- The reason line gives the observation time as a UTC timestamp, not "20 minutes ago" (D9). The story offered the relative form only as an example.
- A CAVOK report says "below 5,000 ft", not "below 12,000 ft" (D10). The story did not cover CAVOK.
- No split: the story fits in about ten tasks.

Confirmed by user: yes
