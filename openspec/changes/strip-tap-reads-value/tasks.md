<!-- Plain language: Each task must make sense to an agent and reviewer without the planning conversation. Name an observable outcome, its location when needed, and how to verify it. Preserve checkbox syntax and tags. -->

Read design.md first. Hover texts, keys and scenarios come from
`specs/night-card/spec.md` in this change and design decision 1's table.
The card tests go in a new `card/test/tap.test.ts` and mount the card with
`mountCard` from `card/test/harness.ts`. A "box" is the `.tip` element in
`<ha-card>`; "shows no box" means there is no `.tip` element. happy-dom does
no layout, so a test that needs sizes stubs `getBoundingClientRect`, as
`card/test/pan.test.ts` does.

## 1. Tapping the card

- [x] 1.1 [medium] `placeTip(item, card, box)` in a new `card/src/tap.ts` returns the box's `left` and `top` in px relative to the card: centred on the part of the item inside the card, `left` clamped to 8 px from each card edge, and `top` 4 px above the item, or 4 px below it when that would leave less than 8 px above. Test with numbers: an item centred in a 400 px card, one at the right edge, one cut off by the card's left edge, and one 10 px from the card's top (design decision 6) (verify: `npm --prefix card test -- test/tap.test.ts`) (✓ `npm --prefix card test -- test/tap.test.ts` passed)
- [x] 1.2 [medium] Every tappable element carries the `data-tip` key from design decision 1's table, such as `cell:cloud_cover:2026-11-01T04:00:00.000Z`, `line:dusk`, `missing:chart:dew_point` and `moon`; and `tipText(strip, moon, key)` in `card/src/tap.ts` returns that element's hover text, or `undefined` for a key with no item on the card. Add the key builders to `tap.ts`, and a `key` parameter to `renderMissing` in `card/src/chart.ts` (design decisions 1 and 2) (verify: `npm --prefix card test -- test/tap.test.ts`) (✓ `npm --prefix card test -- test/tap.test.ts` passed)
- [x] 1.3 [complex] A tap (a `pointerdown` then a `pointerup` at the same point) on a Cloud cover cell, a Cloud range column, a Temperature chart hour, a target bar or the dusk line shows one `.tip` box, the last child of `<ha-card>`, with `aria-hidden="true"`, reading the item's hover text, such as `Cloud cover, the hour from 04:00: 52%` and `The hour from 21:00: Temperature 4.2 °C, Dew point 1.5 °C`; the item's `title` is unchanged. Move the `pointer()` helper from `card/test/pan.test.ts` to `harness.ts` and add a `tap()` helper there; track presses on `<ha-card>` with a `tipKey` property (design decisions 3 and 7) (verify: `npm --prefix card test -- test/tap.test.ts test/pan.test.ts`) (✓ `npm --prefix card test -- test/tap.test.ts test/pan.test.ts` passed)
- [x] 1.4 [medium] A tap on a message shows its hover text: the Seeing row's `Unavailable` (`sensor.pierpressure_backyard_seeing is unavailable`), the Moon up lane's `Not found`, the `Not found` beside `Dew point` in the Temperature chart's key, and the Cloud range row's message; and a tap on the moon drawing, or on a shape inside it, shows `Moon: waxing gibbous, 78% lit` (verify: `npm --prefix card test -- test/tap.test.ts`) (✓ `npm --prefix card test -- test/tap.test.ts` passed)
- [x] 1.5 [medium] Only a tap opens a box: a mouse click, pen tap or a press that moves 5 px opens one; a press that moves more than 8 px sideways or up and down, a drag that pans, a press with a button other than the main one, and a gesture that ends in `pointercancel` open none; and a second pointer pressed while the first is down is ignored (design decision 3) (verify: `npm --prefix card test -- test/tap.test.ts`) (✓ `npm --prefix card test -- test/tap.test.ts` passed)
- [x] 1.6 [medium] With a box showing, a second tap on the same item closes it; a tap on another item shows that item's text in the one box; and a tap on a row's label, an empty part of a track, the verdict or the reasons closes it (design decision 3) (verify: `npm --prefix card test -- test/tap.test.ts`) (✓ `npm --prefix card test -- test/tap.test.ts` passed)
- [x] 1.7 [medium] A pan that moves the axis closes the box: a drag, a sideways wheel movement, the Right arrow key, and `Back to tonight` selected by a click or the keyboard; the Right arrow key with the axis at the end of the reach leaves the box; and changing the card's `pier` closes it. Clear `tipKey` in `panTo` after its early return, in `onBack` and in `setConfig` (design decision 4) (verify: `npm --prefix card test -- test/tap.test.ts test/pan.test.ts`) (✓ `npm --prefix card test -- test/tap.test.ts test/pan.test.ts` passed)
- [x] 1.8 [complex] An open box follows its item through a redraw: the now line's box reads `Now, 21:01` after the minute timer fires at 21:01; a Cloud cover box reads `60%` after Home Assistant updates that hour; a Target 1 box reads `Orion Nebula (M42) from 06:00 to 10:00` after Target 1 changes; a Seeing message box reads `has no forecast for these hours` after the sensor turns `unknown`; and the box closes when its hour leaves the axis, its Moon up run starts in another hour, or the Verdict sensor turns `unavailable`. Clear `tipKey` in `willUpdate` when `tipText` returns `undefined` (design decision 2) (verify: `npm --prefix card test -- test/tap.test.ts`) (✓ `npm --prefix card test -- test/tap.test.ts` passed)
- [ ] 1.9 [medium] The box is placed without moving the card: the stylesheet gives `ha-card` `position: relative`, and `.tip` `position: absolute`, `z-index: 2`, `pointer-events: none`, `max-width: min(280px, calc(100% - 16px))` and `overflow-wrap: anywhere`; the `.strip` element's children are the same with and without a box; and with stubbed rects, `updated()` writes `placeTip`'s `left` and `top` to the box's inline style, again after a redraw moves the item (design decisions 5 and 6) (verify: `npm --prefix card test -- test/tap.test.ts`)

## 2. The docs

- [ ] 2.1 [parallel] [easy] A new "Reading a value on a phone" subsection of `docs/night-card.md`, after "The lines" and before "Panning the strip", names tap, phone and box in the same paragraph as hover; lists the cell, column, bar, line, Temperature chart hour, message and moon drawing; says any pointer can tap; and says a tap elsewhere, a second tap on the same item, or a pan closes the box. The moon drawing paragraph says "Hover over or tap the drawing". Add tests for these words to `tests/test_night_card_doc.py` (design decision 8) (verify: `uv run pytest tests/test_night_card_doc.py`)

## 3. Integration [depends-on: 1, 2]

- [ ] 3.1 [easy] The full CI gate passes: specs, ruff, mypy, pytest, and the card's type check, tests and build (verify: `mise run check`)

## Deviations Ledger

<!-- Dated notes on small departures from the plan, written during apply. Stop and ask the user about a large one. -->

- 2026-11-20, task 1.3: the spec's Temperature chart scenario said a Dew point
  forecast of 1.0 reads `Dew point 1.0 °C`. The card writes a forecast value as
  JavaScript reads the number, so 1.0 reads `1 °C`, and the hover text must not
  change. The scenario, and the tests, now use 1.5, which reads
  `Dew point 1.5 °C`, as the #253 chart tests do.
