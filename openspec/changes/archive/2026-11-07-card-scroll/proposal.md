## Why

The card's night strip shows only the judged night, with a few hours either
side. The timeline sensors already carry two to three days of forecast, but the
card drops every hour off its fixed axis, so the adopter cannot look ahead to
tomorrow night from the card.

## What Changes

- The strip still opens on the judged night, the same axis as today (D3). The
  user can then pan it sideways, without zooming (D4), across every hour the
  timeline holds (D5).
- A mouse drag, a touch swipe, a trackpad's sideways swipe and the Left and
  Right arrow keys pan the strip. An up or down swipe still scrolls the page
  (D6).
- Every row, lane and line moves together; the row labels stay put (D7). Time
  labels follow today's rule for the panned axis (D10). The card cuts off cells
  and bars at the panned axis's ends, as it does at today's (D9).
- On a night other than the judged one, the strip shows its rows and Moon up
  bars, but no dusk, dawn or target bars. Each line shows only while its time
  is on the axis (D8).
- A touch that moves only a little sideways, or that the browser takes over
  to scroll the page, pans nothing (D16).
- Once the user has panned, new state and the minute redraw keep the strip on
  the same hours (D11). A "Back to tonight" button returns it to the judged
  night (D12).
- `docs/night-card.md` says how to pan, where panning stops, why a row can say
  "No forecast" on a later night, and what the button does (D14).

No new data: the timeline sensors already carry every hour (D2).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `night-card`: the strip opens on the judged night and pans through every
  forecast hour, with a button back to the judged night. The dusk and dawn
  lines show only while on the axis. The docs describe panning.

## Impact

- Code: `card/src/strip.ts` (the panned axis and how far it can pan), `card/src/pierpressure-card.ts` (panning input, the button) and
  `card/test/`.
- Docs: `docs/night-card.md`, and its test, `tests/test_night_card_doc.py`.
- No change to the core, the verdict document, MQTT delivery, the add-on or the
  YAML dashboard (#173 stays open for it). No new dependency.
