## Story

#110 rank-remaining-night — mid-session, targets are ranked on the rest of the night
(https://github.com/andrewduckett/pier-pressure/issues/110)

## Decisions

| # | Question | Answer | Source |
|---|---|---|---|
| D1 | Once the night has started, which score terms judge the rest of the night only? | All four geometry terms: altitude and moon separation at the peak within the remaining window, window length as a share of the scored window, transit against the remaining window. Brightness and field-of-view fit are unchanged. | User |
| D2 | Which stretch is a target's remaining window? | The longest above-mask stretch within the scored window, even when it is not part of the emitted `window`. | User |
| D3 | Is the remaining window published? | Yes: a new per-target `remaining_window` {start, end}, equal to `window` before dusk. `window`, `max_altitude`, `transit_time` and `moon_separation` keep their whole-night meaning. | User |
| D4 | What happens in the last hour of the night? | The minimum stays the 60-minute `MIN_USABLE_WINDOW`, so with under an hour of dark left the target list is empty. | User |
| D5 | What does "keep the per-night cache useful" mean as a test? | The night's catalog scan stays cached per night: a later recompute in the same night does not rescan the catalog, and its result equals a fresh computation at that instant. | User |
| D6 | Which glossary terms are agreed? | Scored window, scoring instant and remaining window, in the shared `openspec/glossary.md`. | User |
| D7 | What happens before dusk? | The target list is unchanged, apart from the new `remaining_window` field. | Evidence: #110 body, **Expected** |
| D8 | Does the "Top pick" framing sentence change? | It follows the new top pick, because it reads the first target in the list. | Evidence: `pierpressure/core/producer.py` |

## Changes from the story

- Added: the `remaining_window` field. The story left it to the brainstorm to decide whether to publish the remaining part.
- Added: glossary entries for scoring instant and remaining window, beside the scored window entry the story asked for.
- Split out: drawing `remaining_window` on the dashboard card, filed as #277, blocked by #110.

Confirmed by user: yes
