## Story

#146 provider-order — conditions are filled variable by variable from an ordered provider list
https://github.com/andrewduckett/pier-pressure/issues/146

## Decisions

| # | Question | Answer | Source |
|---|---|---|---|
| D1 | Do other specs change besides conditions? | ha-delivery's health attribute (in scope) and a wording-only delta on night-verdict's three timeline requirements; no scenario values change | User |
| D2 | When has a provider "returned" a variable? | When at least one hour carries a value for it, or for a variable in its bundle; empty columns fall through to the next provider | User |
| D3 | Is every listed provider fetched each recompute? | Yes, all, in order; one outcome per provider every time; fill is decided after all fetches | User |
| D4 | What replaces the health sensor's `role`? | `variables`: the provider's declared variables as a fixed-order list of timeline key names | User |
| D5 | Config validation for `conditions.providers` | Block optional, default `[open_meteo, seven_timer]`; empty list, unknown key, duplicate key and no keyless cloud-cover provider are each a startup error; plain error, no hidden input | User |
| D6 | Vocabulary | Glossary gains Provider, Variable, Series, Bundle, Provider order; the conditions spec says "provider" and "variable" for "source" and "field" | User |
| D7 | Which variables bundle today? | Only cloud total with its low, mid and high layers; every other variable is independent | Evidence: #131 Shared decisions |
| D8 | Does freshness reading the cloud series keep the goldens byte-identical? | Yes: cloud entirely absent already zeroes completeness, so confidence is 0 whatever freshness says | Evidence: `pierpressure/core/scoring.py` confidence formula and `tests/fixtures/golden/expected/base_wind_without_cloud.json` |
| D9 | Config keys for the providers | The existing provider keys `open_meteo` and `seven_timer` | Evidence: `pierpressure/conditions/open_meteo.py`, `seven_timer.py` |

## Changes from the story

- Added: a wording-only delta on night-verdict's timeline requirements (D1).
- Added: five glossary entries, committed on this branch as their own `docs:` commit (D6).
- Nothing cut, nothing split.

Confirmed by user: yes
