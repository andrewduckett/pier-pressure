## Story

#156 air-quality-provider — a pier can add Open-Meteo's air-quality forecast for aerosol and particulates, https://github.com/andrewduckett/pier-pressure/issues/156

## Decisions

| # | Question | Answer | Source |
|---|---|---|---|
| D1 | Are the endpoint's variable names and cadence as the packet says? | Yes: `aerosol_optical_depth` (no unit) and `pm2_5` (µg/m³), hourly, the same 48 hours as the forecast endpoint with `forecast_days=2`. | Evidence: live call to `air-quality-api.open-meteo.com/v1/air-quality`, 2026-11-03 |
| D2 | Is `open_meteo_air_quality` opt-in, or in the default provider list? | In the default list, appended after `seven_timer`, so it builds a health track record before computed transparency reads it. | User |
| D3 | Do air-quality hours create timeline rows on their own? | No. The timeline's hours come only from variables the timeline shows; a hidden variable never adds an hour, so an outage of every shown provider still yields an empty timeline. | User |
| D4 | How does the glossary's Timeline entry say this? | "every hour a provider returned for a variable the timeline shows … A variable the timeline does not show never adds an hour." Committed on this branch. | User |
| D5 | What does "kept off the timeline" mean for the document? | `TimelineEntry` gains no key, and two snapshots that differ only in aerosol or PM2.5 yield byte-identical verdict documents. | Evidence: #156 packet (Relevant code, Scope out) and D3 |
| D6 | Does the new provider get a health record? | Yes, like every listed provider, declaring its two variables. | Evidence: `openspec/specs/conditions/spec.md` (fetch outcomes) |
| D7 | Should the sun and moon show on the strip when every forecast fails? | Yes in principle, but as its own story, computed without any provider; not in this change. | User |
| D8 | Should the night strip scroll sideways like Astrospheric? | Yes, as its own dashboard-only story; not in this change. | User |

## Changes from the story

- Added: `open_meteo_air_quality` joins the default provider list (D2), so the conditions spec's default-list requirement and the README change here.
- Added: the timeline's hours come only from variables it shows (D3), with the glossary's Timeline entry reworded to match (D4).
- New issue, not a split: #174 `timeline-astronomy-always`, blocked by #156, makes the timeline always carry the sun and moon for the judged night (D7).
- New issue, not a split: #173 `scrollable-night-strip`, independent, makes the documented strip pan sideways through the whole timeline (D8).

Confirmed by user: yes
