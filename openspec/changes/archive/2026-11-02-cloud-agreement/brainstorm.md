## Story

#158 cloud-agreement — the verdict says how well the forecasts agree on cloud, and confidence falls when they do not. https://github.com/andrewduckett/pier-pressure/issues/158

## Decisions

| # | Question | Answer | Source |
|---|---|---|---|
| D1 | What takes part in the measure? | Only providers that returned cloud cover: the filled series and its alternates. Per hour, the gap between the lowest and highest cloud given, counted only where two or more providers cover the hour. | Evidence: #153 Shared decisions |
| D2 | Which clarity weights each hour's gap? | `w·q(lowest cloud any provider gave)`, the most optimistic reading, so an hour any forecast calls usable counts most. If every weight is zero, all providers say overcast all night and the spread is 0. | User |
| D3 | Where do the bands sit, in cloud-cover points of mean gap? | agree below 15, mixed 15 to 35, disagree above 35, as tuning constants with their justification in code. | User |
| D4 | What does the document carry? | A top-level `agreement` object keyed by variable, always present: `{"cloud_cover": {"band": "AGREE\|MIXED\|DISAGREE", "spread": <mean gap, whole points>, "providers": [keys in provider order]}}`. Empty `{}` when fewer than two providers returned cloud. | User |
| D5 | What do the timeline fields look like? | `cloud_cover_min` and `cloud_cover_max`, appended after `precipitation_probability`; null for an hour fewer than two providers cover. | User |
| D6 | How does agreement reach confidence? | A factor on the whole value: agree 1, mixed about 0.9, disagree about 0.67, so a verdict otherwise at 100 cannot fall below MEDIUM on agreement alone. It never changes a gate or the score. | Evidence: #153 Shared decisions, `pierpressure/core/scoring.py` (`confidence`) |
| D7 | When does the reason line appear? | On every verdict whose `agreement` is non-empty, gated NO-GO included, since the alternates still bear on how far to trust the call. Never with fewer than two providers. | Assumption |
| D8 | Where do alternates live? | In `Conditions` beside `series`, additively, for every variable that lost the fill, in provider order. The core reads them only to measure agreement. An alternate never fills an hour the filled series lacks. | Evidence: `openspec/glossary.md` (Alternate), `pierpressure/core/conditions.py` |
| D9 | Does the delivery surface change? | No. `agreement` reaches the Verdict entity's attributes through the existing rule that the payload carries every document key except `timeline`. No new sensor; drawing the band is #132. | Evidence: `openspec/specs/ha-delivery/spec.md`, `pierpressure/delivery/mqtt.py` (`TIMELINE_SENSORS`) |
| D10 | Which decision record? | A new ADR widening confidence's inputs from lead time and freshness to agreement; `openspec/prd.md` and the config context already say so. | Evidence: #158 Scope, `openspec/prd.md` §6.1 |

## Changes from the story

None.

Confirmed by user: yes
