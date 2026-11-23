<!-- Plain language: Write questions and answers so a reader without the conversation can understand each decision and its source. Keep the confirmation marker exactly as written. -->

## Story

#319 later-night-targets — each later night on the strip shows its own ranked targets, https://github.com/andrewduckett/pier-pressure/issues/319

## Decisions

| # | Question | Answer | Source |
|---|---|---|---|
| D1 | How is a later night's target list ranked? | On that night's own moon, over its whole dark window, with the same ranking as tonight (`rank_targets`, which reads no forecast). | Assumption |
| D2 | What do later nights' `later_nights` entries gain, and in what shape? | `moon` and then `targets`, after `dark_window`, each in the same shape as the top-level field. Tonight's fields are unchanged and not repeated. | Assumption |
| D3 | When are a later night's moon illumination and phase computed? | At the middle of that night's local solar day (local solar midnight), which every later night has, with or without darkness. | User |
| D4 | What do a later night's moon and targets hold when it has no astronomical darkness? | `moon` keeps its illumination and phase, with null `up_during_dark`, `rise` and `set`; `targets` is an empty list, as tonight's fields do on such a night. | Evidence: `pierpressure/core/sky.py` (`moon_info`), `pierpressure/core/ranking.py` (`rank_targets`) |
| D5 | What is a later night target's `remaining_window`? | The same as its `window`, because the evaluation instant is before that night's dusk, so the whole dark window is scored. | Evidence: `pierpressure/core/ranking.py` (`scored_window`, `_rank`) |
| D6 | Is a slower first verdict after a restart acceptable? | Yes. A cold catalog scan takes about 5 s per night, so the first verdict takes about 20 s per pier instead of about 5 s. Each night's scan is cached, so later recomputes that night reuse it. Publishing tonight first and later nights afterwards is ruled out: it would publish two documents for the same inputs. | User |
| D7 | How many night scans does the cache keep? | Every night of every configured pier, so a recompute never rescans a night it already scanned. Today `_CACHE_MAXSIZE` is 8. | Evidence: #319 Scope |
| D8 | How do the Night sensors deliver the new fields? | Their attributes carry the whole entry, so `moon` and `targets` appear there with no new entity, topic or state change. The Verdict attributes still leave out `later_nights`. | Evidence: `pierpressure/delivery/mqtt.py` (`night_attributes`), ADR-0043 |
| D9 | Which target lanes does the card draw, and what goes in them? | A lane for each rank that has a target on any night: tonight from its Target sensor, a later night from its available Night sensor's `targets`. Each night's bar sits in its rank's lane and is named for that night's target. Lane labels stay `Target <n>`. | Assumption |
| D10 | When does a later night's rank count as having a target? | By the same rule as tonight: the Night sensor is available, and the entry at that rank has a non-empty `name` or `id` and a readable `window` with `end` after `start`. | Assumption |
| D11 | What does a later night's bar say on hover or tap? | The same text as tonight's bars: the target's name, catalog id and window times. | Assumption |

D1, D2 and the delivery half of D8 come from the Shared decisions in epic #299, which `lets-go` accepted on the shaping step's recommendation; the user did not decide them. D9 to D11 follow the story's scope and the card's existing rules for tonight.

## Changes from the story

- **Added: when a later night's moon is computed (D3).** Tonight's moon is computed at the evaluation instant, which a later night does not have. The story did not say.
- **Added: the first verdict after a restart is slower (D6).** The story named this as a risk; the user accepted it.
- **Clarified: a later night with no darkness (D4) and a later night's `remaining_window` (D5).** Both follow from the existing code.
- **Noted:** open story #277 also edits the target lanes. Neither blocks the other; whichever merges second adapts to the first.

Nothing was split out.

Confirmed by user: yes
