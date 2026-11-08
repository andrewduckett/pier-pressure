**Why:** A gated NO-GO has a null score by design, so the card shows "NO-GO" and "Score —" with no word on which gate failed; a dashboard review on 2026-11-07 found the wind-gust gate hidden this way, while the YAML night dashboard already lists the reasons.

## Story

#215 card-shows-reasons — the card lists the verdict's reasons, so a NO-GO says why
(https://github.com/andrewduckett/pier-pressure/issues/215)

## Decisions

| # | Question | Answer | Source |
|---|---|---|---|
| D1 | What does the card read? | The Verdict sensor's `reasons` attribute, shown in its own order, one item per reason; the core's wording is never changed. | Evidence: #215 packet, `openspec/specs/ha-delivery/spec.md` |
| D2 | When is the list valid? | Only when `reasons` is a non-empty list whose every item is a string; a missing, empty or mixed list shows no list and no heading, and the card renders as before. | Evidence: #215 packet |
| D3 | When does the list show at all? | Only beside the verdict: never before Home Assistant gives the card its state, and never under the offline or missing-sensor message. | Evidence: `card/src/pierpressure-card.ts` `renderBody`, night-card "The strip shows only with the verdict" |
| D4 | Where does the list sit? | Straight under the summary (verdict lines and Moon section), before the darkness note, the Back to tonight button and the strip; the reasons explain the verdict, and the note and the button belong to the strip, which the button must stay directly above. | Assumption |
| D5 | Does the list collapse on a phone? | No; it always shows in full, at every width. A collapse would hide the gate reason this story exists to show, and the list is a few short lines. | Assumption |
| D6 | How does the span line's raw UTC read? | The card shows each UTC timestamp of the form `YYYY-MM-DDTHH:MM:SSZ` in any reason as `HH:MM` in Home Assistant's time zone, as the strip shows times; the rest of the text is unchanged. So `Scored from 2026-10-31T21:00:00Z to 2026-11-01T03:25:00Z (the rest of tonight).` reads `Scored from 21:00 to 03:25 (the rest of tonight).` in UTC. | Assumption |
| D7 | Why rewrite every timestamp, not just the span line? | Matching only the span line's wording would tie the card to one core sentence; matching the timestamp form covers it and any later reason that names a time. The scored span lies within one night, so `HH:MM` is never ambiguous. | Assumption |
| D8 | How is the list marked up? | A list (`ul`, one `li` per reason) named "Reasons" for screen readers, in the secondary text colour, with no visible heading, as the YAML dashboard shows it. | Assumption |
| D9 | How does `getCardSize()` grow? | 10, plus 1 for every three target lanes, plus 1 for every two reasons shown, each rounded up. About two wrapped reason lines fill one of Home Assistant's 50 px units. | Assumption |
| D10 | A night with no astronomical darkness shows both its reason and the darkness note: keep both? | Yes. The reason explains the verdict; the note explains the strip's fallback axis. Removing either is outside this story. | Assumption |
| D11 | What do the docs gain? | A **Reasons** line in `docs/night-card.md`'s "What the card shows" table that says the list follows the verdict, that times show in the Home Assistant time zone, and that equipment notes come after the scoring reasons; a pytest checks the line, as for the other doc requirements. | Evidence: `tests/test_night_card_doc.py`, `pierpressure/core/producer.py` |
| D12 | How does the change stay a small rebase on #223 and #225? | Branch off `main`; put the card tests in a new `card/test/reasons.test.ts` and leave `card/test/harness.ts` alone; touch only the summary area, `getCardSize()` and the styles in `pierpressure-card.ts`. | User |

## Changes from the story

None. The story stands as written. The brainstorm settled the three questions the packet left open: placement (D4), collapsing on a phone (D5) and the span line's timestamps (D6, D7). The user delegated these to the agent's recommendation and asked to be stopped only where there was none.

Confirmed by user: yes
