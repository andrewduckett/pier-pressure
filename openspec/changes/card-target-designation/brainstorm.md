**Why:** A target bar on the night strip shows only the common name of a named target, so the catalog id you type into a mount or planetarium app is never on the card.

## Story

#297 card-target-designation — each target bar on the night strip shows the target's catalog id beside its name, https://github.com/andrewduckett/pier-pressure/issues/297

## Decisions

| # | Question | Answer | Source |
|---|---|---|---|
| D1 | Which surface shows the id beside the name? | The card's target bars only; the sensor state, the verdict document and the lane label stay as they are | User |
| D2 | What order and form does the bar text take? | `<name> (<id>)`, such as `Andromeda Galaxy (M31)` | User |
| D3 | What gets cut when the bar is too narrow? | The name shortens with "…"; `(<id>)` stays whole | User |
| D4 | What does a target the catalog does not name show? | `<id>` alone, such as `IC2184`, never the id twice | User |
| D5 | Where does the card read the id and name? | The Target sensor's `id` and `name` attributes, which the delivery already publishes at the top level | Evidence: `pierpressure/delivery/mqtt.py` (`rank_target_attributes`) |
| D6 | What do the hover and the aria-label show? | The same text with the window, `<name> (<id>) from <HH:MM> to <HH:MM>`, and the text alone for a window of 24 hours or more | User |
| D7 | What if the attributes carry no `id`, as from an older PierPressure? | The bar shows the sensor state, as it does today | User |
| D8 | Does a rank still need a usable state to have a lane? | Yes; the lane rule is unchanged, only the bar's text changes | Evidence: `openspec/specs/night-card/spec.md` (A rank with no target tonight leaves no lane) |
| D9 | Is an empty-string `name` treated like a null one? | Yes, it shows `<id>` alone | Assumption |
| D10 | Which docs change? | The night-card spec's two target-bar requirements and `docs/night-card.md`'s target lanes section | Evidence: `docs/night-card.md`, `openspec/specs/night-card/spec.md` |

## Changes from the story

None.

Confirmed by user: yes
