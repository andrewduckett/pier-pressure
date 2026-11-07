## Why

The card's night strip shows only the judged night, with a few hours either
side. The timeline sensors already carry two to three days of forecast, but the
card drops every hour off its fixed axis, so the adopter cannot look ahead to
tomorrow night from the card.

## What Changes

- The strip still opens on the judged night, the same axis as today (D3). The
  user can then pan it sideways, without zooming (D4), as far as the first and
  last hour any row's sensor holds (D5).
- A mouse drag, a touch swipe, a trackpad's sideways swipe and the Left and
  Right arrow keys pan the strip. An up or down swipe still scrolls the page
  (D6).
- Every row, lane and line moves together; the row labels stay put (D7). Time
  labels follow today's rule for the visible span (D10). Cells and bars are cut
  off at the visible span's ends as they are at today's axis ends (D9).
- On a night other than the judged one, the strip shows its rows and Moon up
  bars, but no dusk, dawn or target bars (D8).
- Once the user has panned, new state and the minute redraw keep the strip on
  the same hours (D11). A "Back to tonight" button returns it to the judged
  night (D12).
- `docs/night-card.md` says how to pan, where panning stops, and what the
  button does (D14).

No new data: the timeline sensors already carry every hour (D2).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `night-card`: the strip opens on the judged night and pans through every
  forecast hour, with a button back to the judged night, and its docs describe
  panning.

## Impact

- Code: `card/src/strip.ts` (the strip's visible span and how far it can
  pan), `card/src/pierpressure-card.ts` (panning input, the button) and
  `card/test/`.
- Docs: `docs/night-card.md`, and its test, `tests/test_night_card_doc.py`.
- No change to the core, the verdict document, MQTT delivery, the add-on or the
  YAML dashboard (#173 stays open for it). No new dependency.
