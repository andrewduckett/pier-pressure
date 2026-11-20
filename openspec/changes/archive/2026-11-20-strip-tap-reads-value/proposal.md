## Why

Most people read the dashboard on a phone, and a phone has no hover. Every
exact value on the night strip, such as `Cloud cover, the hour from 04:00:
52%`, sits in a hover tooltip, so on a phone the strip shows only shades and
lines. Since #253 the temperature and dew point values are hover-only too.

## What Changes

- A tap on an item shows that item's hover text in a small box just above it,
  inside the card (D1, D4). The items are:
  - a row's cell, a Cloud range column, a Moon up bar or a target bar;
  - a dusk, dawn or now line;
  - an hour on the Temperature chart (D2);
  - a row's message, the Moon up lane's message or the Temperature chart key's
    message, whose hover text names the sensor (D3);
  - the moon drawing beside the verdict.
- Any pointer can tap: touch, pen or mouse (D5).
- A tap elsewhere on the card, or on the same item again, closes the box (D6).
  A tap on another item shows that item's text instead (D7).
- Any pan closes the box: a drag, a sideways wheel or trackpad swipe, an arrow
  key or `Back to tonight` (D7). A drag, or a swipe the browser takes to scroll
  the page, opens no box (D8).
- When Home Assistant or the minute timer redraws the card, an open box stays
  on its item, follows it and shows its latest text. It closes when the item is
  no longer on the card (D12).
- No hover text changes, and the browser's own tooltip stays (D9). There is no
  keyboard path to the box (D10).
- `docs/night-card.md` says that a tap shows what hovering shows (D11).

No change is **BREAKING**: the verdict document, the MQTT entities and the
hover texts stay as they are.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `night-card`: adds requirements for showing an item's hover text on a tap,
  closing it, keeping it through a redraw, and describing it in the docs.

## Impact

- **Card code:** `card/src/pierpressure-card.ts` (pointer handling on the strip
  and the moon drawing, the box and its styles); `card/src/chart.ts` (the
  Temperature chart's hour areas and key messages take part in taps).
- **Card tests:** new Vitest tests under `card/test/` for tapping, closing and
  redrawing. The pan tests in `card/test/pan.test.ts` keep passing.
- **Spec:** `openspec/specs/night-card/spec.md`.
- **Docs:** `docs/night-card.md`.
- **Core, MQTT and verdict document:** no change.
- **Dependencies:** none added.
