## Story

#157 dew-spread-reason — the reasons say when dew or frost is likely during the window
https://github.com/andrewduckett/pier-pressure/issues/157

## Decisions

| # | Question | Answer | Source |
|---|---|---|---|
| D1 | How does the line name the hour, given a pier has no timezone? | The document's UTC timestamp string, as the span line uses: `Dew likely from 2026-09-08T23:00:00Z.` | User |
| D2 | Which verdicts carry the line? | Only verdicts whose gates passed (a non-null score): GO, and MAYBE including the short-window and wind-capped caps. A gated NO-GO carries none. | User |
| D3 | Where does the line sit among the reasons? | Last of the core's lines, after Cloud agreement and before the producer's equipment notes. Strictly additive; the test that says a scored verdict ends with the agreement line rewords to "follows the score line". The user notes a position promise is a poor fit for named strings. | User |
| D4 | What if the first hour under the margin is above freezing but a later one is at or below 0 °C? | One line. The first hour under the margin decides the word: frost when its air temperature is at or below 0 °C, dew otherwise. | User |
| D5 | What is the setting? | `dew_margin` on the pier, a float in °C, default 4, `ge=0`; 0 turns the line off. Opt-out, where `max_gust` is opt-in, because the data is in every forecast. | Evidence: `pierpressure/core/config.py` (`max_gust`), issue #153 Shared decisions |
| D6 | When is an hour under the margin? | Temperature minus dew point is strictly less than the margin, both from the hour's filled series. | Assumption |
| D7 | Which hours are read? | The scored window's hour slots in order, as the score walks them. An hour missing temperature or dew point is skipped. Cloud does not weight or exclude an hour: a heater is a setup decision, not a sky one. No hour qualifying means no line. | Evidence: `pierpressure/core/scoring.py` (`hour_slots`, `_score_reasons`) |
| D8 | Does the line change the score, a gate or confidence? | No. A reason line only. | Evidence: issue #153 Shared decisions ("Dew spread is a reason line only") |
| D9 | Does a timeline variable or a document field change? | No. The spread is derived from `temperature` and `dew_point`, which the timeline already carries. The verdict document grows by one reason string only. | Evidence: issue #157 Scope |
| D10 | How do golden fixtures cover it? | The recorded Open-Meteo payload has no temperature or dew point, so no existing golden changes. New stub-based golden cases cover a dew night and a frost night. | Evidence: `tests/fixtures/golden/open_meteo_full.json` (hourly keys) |
| D11 | How does the add-on get the setting? | Through the add-on's `config.yaml`, which passes any pier key the form does not name. No form field or schema line (#99). README and add-on DOCS document `dew_margin`. | Evidence: `pierpressure/addon_options.py` (`pier_settings`) |

## Changes from the story

None.

Confirmed by user: yes
