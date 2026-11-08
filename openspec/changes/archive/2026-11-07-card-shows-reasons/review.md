# Plan review: card-shows-reasons

- **Round:** 1
- **Reviewed commit:** 1c49f55
- **Reviewer:** gemini/gemini-3.8-flash, through the `t3` resolver
- **Reviewer context:** fresh context, other family (author: claude)
- **How it ran:** `lets delegate review run` exited 5, because the Gemini session ran in plan mode and ended its turn as if it were asking. Its last message holds the complete review and a verdict, so the author used it rather than run the review again.
- **Verdict:** APPROVE_WITH_CHANGES

## Findings

| # | Label | Concern | Check | Outcome |
|---|---|---|---|---|
| 1 | Moderate | The strip's `clock()` throws a `RangeError` on an invalid time, so a reason such as `Scored from 2026-13-45T21:00:00Z onwards.` would break the card. | CONFIRMED: `Intl.DateTimeFormat.formatToParts(NaN)` throws `RangeError: Invalid time value`; `card/src/strip.ts:564` passes the time straight through. | Fixed: task 1.5 now says an unreadable time never reaches the clock. The spec already requires it to stay as written. |
| 2 | Moderate | `getCardSize()` could count reasons left on an `unavailable` Verdict sensor and leave empty space under the offline message. | CONFIRMED as a risk: `getCardSize()` (`card/src/pierpressure-card.ts:297`) has no guard of its own; only `shownStrip()` checks the state. | Fixed: a new scenario, "Offline with reasons left over", in the MODIFIED size requirement, and task 1.7 says the size counts no reason without a verdict. |
| 3 | Moderate | `card/test/messages.test.ts:229` expects the darkness note's previous sibling to be the summary, which a reasons list would break. | REFUTED: that test's `SUMMER` fixture has no `reasons` attribute, so no list renders and the test still holds. The new order (list, then note) is tested in task 1.4 in `card/test/reasons.test.ts`. | Rebutted. |
| 4 | Suggestion | Two sentences run over 30 words, and one scenario uses the passive "is read". | CONFIRMED for the long sentences. The passive "is read" matches every doc scenario in the main night-card spec, and its actor (the reader) is plain. | Fixed: the Why line is now two sentences, and the docs requirement is a list. The passive scenario is kept for consistency. |

## Required changes applied

1. Task 1.5 guards the clock against an unreadable time.
2. Task 1.7 and a new size scenario count no reasons without a verdict.
3. The Why line and the docs requirement are split under 30 words a sentence.
