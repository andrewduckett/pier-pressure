<!-- Plain language: Write questions and answers so a reader without the conversation can understand each decision and its source. Keep the confirmation marker exactly as written. -->

## Story

#318 later-night-dark-windows — the night strip draws dusk and dawn on every night it pans to.
https://github.com/andrewduckett/pier-pressure/issues/318

## Decisions

| # | Question | Answer | Source |
|---|---|---|---|
| D1 | Which nights are later nights? | One per local solar day after the selected night's solar day, in date order, up to three, while the timeline reaches that solar day (D2). | Assumption (#299 shared decision, accepted by lets-go) |
| D2 | When does the timeline reach a later night's solar day? | When the timeline holds an hour that starts inside that solar day. With no provider data there are then no later nights. | Assumption (lets-go accepted the step's recommendation) |
| D3 | How does the document carry later nights? | A `later_nights` list after `observation`. Each entry holds `dark_window` in the top-level shape. Tonight's fields are unchanged and not repeated. | Assumption (#299 shared decision, accepted by lets-go) |
| D4 | What is a later night's dark window? | The whole astronomical night inside its solar day, even where it runs past the timeline. It is anchored to the solar day in continuous polar night, and has null bounds when the night has no astronomical darkness. | Assumption (lets-go confirmed it on the user's standing instruction; the user did not decide, and may reopen it). Reason: it matches the shape of tonight's `dark_window`, and the spec's rule that a night with no darkness has null bounds. |
| D5 | Do the Verdict attributes carry `later_nights`? | No. They leave it out, as they leave out `timeline`. | Assumption (#299 shared decision, accepted by lets-go) |
| D6 | How is each later night delivered? | Night 2 to Night 4 sensors per pier, `sensor.pierpressure_<slug>_night_<n>`. The state is the night's dusk as a timestamp and the attributes hold its entry. The sensor is unavailable when its night is not in `later_nights`. | Assumption (#299 shared decision, accepted by lets-go) |
| D7 | What does a Night sensor show for a night with no astronomical darkness? | It stays available with state unknown, and its attributes hold the entry with null bounds. | Assumption (lets-go confirmed it on the user's standing instruction; the user did not decide, and may reopen it). Reason: a night with no darkness is still a real night in `later_nights`, so its sensor is available; a timestamp sensor with no dusk has the state unknown. |
| D8 | How does the card draw a later night? | Dusk and dawn lines from each Night sensor's `dark_window`, styled, labelled and hovered like tonight's. They show whenever their time is on the axis, even when the opening axis falls back to the browser's clock. A missing or unavailable Night sensor draws nothing. Tonight's lines keep today's rule. | Assumption (lets-go accepted the step's recommendation) |
| D9 | Does the card note a later night with no astronomical darkness? | No. That night shows no lines. `No astronomical darkness tonight` stays about tonight. | Assumption (lets-go accepted the step's recommendation) |
| D10 | What does the term *Later night* mean, and where does it apply? | The definition below, now in `openspec/glossary.md`. Scope: the verdict document, its delivery and dashboards. Code and specs use `later_nights`. | Assumption (lets-go accepted the step's recommendation) |
| D11 | Does the narrative change? | No. The prompt is built only from the verdict, score, confidence, reasons and top targets, so `later_nights` never reaches the explainer. | Evidence: `pierpressure/explain/prompt.py` |
| D12 | Which docs and records change? | A decision record on the document shape and the delivery, the README's entity list and `docs/night-card.md`. | Evidence: #318 issue body |
| D13 | What is out of scope? | Moon and targets for later nights (#319), any change to tonight's fields, and any change to the card's opening axis. | Evidence: #318 issue body |
| D14 | What is a later night's dark window on a day when polar night starts or ends? | The window stops at the solar day's edge: `start` is the solar day's start when the day starts dark, and `end` is its end when the day ends dark. Tonight's `dark_window` still gives null on such a day; this change leaves tonight unchanged (D13). | Assumption (lets-go accepted the plan review's recommendation; the user did not decide) |
| D15 | What happens when one night's dawn line and the next night's dusk line fall at the same second, in continuous polar night? | Accept the overlap: the next night's dusk line covers the ending night's dawn line, so only the dusk line can be hovered or tapped there. Each line keeps its own label and tap key. | Assumption (lets-go accepted the plan review's recommendation; the user did not decide) |
| D16 | What about tonight's `dark_window` faults the plan review found (it can miss a night shorter than about 58 minutes, and gives null on polar-night transition days and the continuous-night days just before one)? | A separate bug issue covers them. This change keeps tonight unchanged. | Assumption (lets-go accepted the plan review's recommendation; the user did not decide) |

D10's definition:

> **Later night** — a night after the selected night, one for each local solar
> day after the selected night's solar day, from solar noon to the next solar
> noon. A later night counts only while the timeline holds an hour that starts
> inside its solar day, and there are at most three. It carries its own dark
> window. It has no verdict, score or confidence; those judge only the selected
> night.

## Changes from the story

- **Night-count rule reworded (D2).** The story counts a later night "while
  that solar day starts before the timeline's last hour ends". Taken literally,
  that always adds one later night, even when every provider fails. The
  timeline always ends with the hour that holds the next solar noon. With no
  provider data, the London timeline for 2026-11-21 ends with the hour
  11:00–12:00 UTC, and the next solar day starts at 11:46. The new rule keeps
  the story's other promise: when every provider fails, there are no later
  nights.
- **Behaviour the story left open, now stated:** a Night sensor for a night
  with no darkness (D7), later-night lines drawn on the fallback axis (D8), and
  no darkness note for later nights (D9).
- **Added after the round-1 plan review:** D14 to D16 settle what the review
  found: a later night's window on a polar-night transition day, coincident
  lines, and tonight's `dark_window` faults, which a separate bug covers.
  D4 and D7 now give their reasons.
- Nothing was cut or split out.

lets-go confirmed this ledger for the user, on the user's standing instruction; the user did not review it.

Confirmed by user: yes
