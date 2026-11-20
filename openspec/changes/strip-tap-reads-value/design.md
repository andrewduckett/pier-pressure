<!-- Plain language: Help the next implementer find the approach, understand the choices and act on the plan. Explain necessary technical terms. Put each risk beside its mitigation and each open question beside the decision it affects. -->

## Context

All of this change is in the dashboard card, `card/`, and its docs. No core,
verdict or MQTT code changes.

- `card/src/pierpressure-card.ts` renders the card into its shadow root as
  one `<ha-card>`. Inside it, the summary holds the verdict and the moon
  drawing (`renderDrawing`, an `<svg>` whose text is in a `<title>` child and
  `aria-label`). The strip is one CSS grid, `.strip`. Every strip item that
  has hover text carries it twice, in `title` and `aria-label`: cells
  (`renderCell`), Cloud range columns (`renderBand`), Moon up and target bars
  (`renderBar`) and the dusk, dawn and now lines (`renderLine`). The lines sit
  in an overlay, `.lines`, with `z-index: 1`, above the rows.
- `card/src/chart.ts` renders the Temperature chart row. Its hour areas
  (`renderHour`) and every row message (`renderMissing`, shared by the rows,
  the Moon up lane and the chart's key) carry `title` and `aria-label` too.
- The text of each item comes from the strip model that `buildStrip` in
  `card/src/strip.ts` returns: `Cell.text`, `Band.text`, `Bar.text`,
  `Line.text`, `ChartHour.text` and `Missing.text`. The moon drawing's text
  is `MoonDrawing.text` from `readMoon` in `card/src/moon.ts`.
- Panning: the strip's pointer handlers live in the card's `input` object.
  `pointerdown` starts a `Drag` and calls `setPointerCapture` on the strip,
  so a later `pointerup` targets the strip, not the element first pressed.
  A drag starts to pan after `DRAG_SLOP` (8 px) sideways. Every pan, from any
  input, goes through `panTo`, which returns early when the axis would not
  move. `onBack` handles `Back to tonight`.
- The card redraws whenever Home Assistant sets `hass` and once a minute
  from its own timer. `willUpdate` runs before each draw.
- Tests run in Vitest on happy-dom, which does no layout:
  `getBoundingClientRect` returns zeros unless a test stubs it, as
  `card/test/pan.test.ts` does. `card/test/harness.ts` mounts the card with
  Home Assistant states and pins the clock. `pan.test.ts` builds pointer
  events with a local `pointer()` helper. `tests/test_night_card_doc.py`
  asserts words in `docs/night-card.md`.

## Goals / Non-Goals

**Goals:**

- One tap mechanism for every item on the card, strip or not, driven by a
  single attribute on each tappable element.
- Take the box's text from the strip model, not from the DOM, so a redraw
  shows the item's latest text with no second draw.
- Keep box placement in a pure function, so tests can check it with plain
  numbers on happy-dom.

**Non-Goals:**

- No change to any hover text, `title` or `aria-label` (spec: the hover
  texts stay as they are).
- No keyboard path to open the box (D10), and no change to how the strip
  pans.
- No tooltip library, and no new dependency.
- A tap outside the card does not close the box. The ledger lists what
  closes it (D6, D7, D12), and the box covers only the card.

## Test Seams

- **Primary test seam:** the card harness, `mountCard` in
  `card/test/harness.ts`, run by Vitest. A new `card/test/tap.test.ts`
  mounts the card, sends pointer events to an item, and reads the box's
  text and its inline `left` and `top`. The same file unit-tests the pure
  placement function, `placeTip`, with numbers.
- **Existing seams reused:** `card/test/pan.test.ts`, which must keep
  passing unchanged except for its `pointer()` helper moving to
  `harness.ts`; `tests/test_night_card_doc.py` (pytest) for the docs page.

## Scrutiny Tier & Blast Radius

- **Tier:** medium
- **Blast radius:** the card's rendering, stylesheet and pointer handling in
  `card/src/pierpressure-card.ts`; `card/src/chart.ts` (one attribute on two
  elements); a new `card/src/tap.ts`; the card's tests; `docs/night-card.md`
  and its doc test. One subsystem, on the card's established patterns. The
  verdict document, MQTT entities and core are untouched.

## Decisions

### 1. Each tappable element carries a `data-tip` key

Every element that a tap can open gets a `data-tip` attribute holding a key
that names the item. The key is also how the card recognises "the same item"
after a redraw (spec: an item is the same after a redraw when it has the same
place in the strip). Hours are ISO times, as the existing `data-hour`
attributes write them.

| Item | Key | Rendered by |
|---|---|---|
| A row's cell | `cell:<row key>:<hour>` | `renderCell` |
| A Cloud range column | `column:<hour>` | `renderBand` |
| A Temperature chart hour | `hour:<hour>` | `renderHour` in `chart.ts` |
| A Moon up bar | `moon-up:<run start>` | `renderBar` |
| A target bar | `target:<rank>` | `renderBar` |
| A dusk, dawn or now line | `line:<kind>` | `renderLine` |
| A row's message | `missing:<row key>` | `renderMissing` |
| The Moon up lane's message | `missing:moon_up` | `renderMissing` |
| A message in the chart's key | `missing:chart:<series>` | `renderMissing` |
| The moon drawing | `moon` | `renderDrawing` |

`renderMissing` gains a `key` parameter, since it does not know where it is
drawn. The key builders live in `card/src/tap.ts`, so the renderers and the
lookup (decision 2) cannot drift apart.

Alternative: find the tapped item by its existing `data-row`, `data-hour`
and `data-line` attributes. The attributes differ by item, and the moon
drawing and the messages have none that name them uniquely.

### 2. The box's text comes from the model, looked up by key

`card/src/tap.ts` exports `tipText(strip, moon, key): string | undefined`.
It finds the item in the strip model, or the moon drawing, and returns its
`text`. It returns `undefined` when no such item exists, for example when
the hour has left the axis, the run starts in another hour, the lane has no
bar, or the strip is not drawn.

The card keeps the open key as a reactive property, `tipKey`. In
`willUpdate`, when `tipText` returns `undefined` for it, the card clears
`tipKey`. Setting a property in `willUpdate` causes no second draw. `render`
then draws the box with `tipText`'s result. So a redraw from Home Assistant
or the minute timer shows the latest text (D12), and an item that has gone
closes the box, with one draw each.

Alternative: read the tapped element's `aria-label` in `updated()`. That
needs a second draw for the text, and setting state in `updated()` is the
pattern Lit warns about.

### 3. Taps are tracked on `<ha-card>`, apart from the drag

The card listens for `pointerdown`, `pointermove`, `pointerup` and
`pointercancel` on its `<ha-card>` element, so a tap anywhere on the card is
seen: on the strip, on the moon drawing, or on empty space (D6). A private
`Press` records the pointer id, the press point, and the key of the nearest
`[data-tip]` ancestor of the pressed element, found with
`(event.target as Element).closest("[data-tip]")`. The key is taken at
`pointerdown`, because the strip's pointer capture retargets `pointerup` to
the strip.

- `pointerdown` starts a press only for a primary pointer with `button`
  `0`, and only when no press is under way, so a second finger is ignored.
  Any pointer type counts (D5).
- `pointermove` marks the press as moved once it is more than 8 px from the
  press point sideways or up and down. The 8 px is `DRAG_SLOP`, so any
  gesture that pans has moved.
- `pointerup` for the same pointer, not moved, is a tap: with the same key
  as `tipKey`, it closes the box; with another key, it opens that one; with
  none, it closes the box.
- `pointercancel` drops the press: the browser took the gesture to scroll
  the page (D8).

The tracker never reads the `Drag`, and the strip's handlers do not change.
`pan.test.ts` keeps proving that.

Alternative: decide taps inside the strip's `pointerup` handler from the
`Drag`. It would not see taps outside the strip, the moon drawing among
them, and it couples two jobs in one handler.

### 4. Every axis move closes the box

`panTo` clears `tipKey` after its early return, so only a pan that moves the
axis closes the box. That covers a drag, a wheel or trackpad swipe and the
arrow keys, which all call `panTo`. `onBack` clears `tipKey` too, so
`Back to tonight` closes the box from a click or from the keyboard. A pan
the reach stops entirely leaves the box, as the spec says. `setConfig`
clears `tipKey` when the pier changes, because the same keys would then name
another pier's items.

### 5. The box is one absolutely placed element in `<ha-card>`

When `tipKey` is set, `render` adds `<div class="tip" aria-hidden="true">`
as the last child of `<ha-card>`, after the card content. `ha-card` gets
`position: relative`. The box:

- is `position: absolute`, so showing it moves nothing (D4), and
  `z-index: 2`, above the lines' overlay;
- has `pointer-events: none`, so a tap on the box reaches the item under it:
  another item switches the box and empty space closes it;
- has `max-width: min(280px, calc(100% - 16px))`, `white-space: normal` and
  `overflow-wrap: anywhere`, so a long entity id wraps inside the card;
- uses `var(--primary-text-color)` as its background and
  `var(--card-background-color)` as its text colour, so it reads on light
  and dark themes alike, at the strip's `0.85em` size with 4 px by 8 px
  padding and a 4 px radius;
- is `aria-hidden`, because the item's `aria-label` already gives a screen
  reader the same text, and a second copy would be read twice.

Alternative: a fixed line above the strip, or one that opens below it. The
user chose the box (D4).

### 6. Placement is a pure function, applied in `updated()`

`card/src/tap.ts` exports
`placeTip(item: Rect, card: Rect, box: Size): { left: number; top: number }`,
in px relative to the card:

- **Across:** the box's centre is the centre of the part of the item that
  lies inside the card, so a target bar the axis cuts off centres on what
  shows. `left` is then clamped to `[8, card.width − 8 − box.width]`.
- **Up and down:** `top` is the item's top less 4 px less the box's height.
  When that is less than 8 px from the card's top, the box goes 4 px below
  the item instead.

After each draw with a box, `updated()` reads the item's element through
`[data-tip="<key>"]`, and the rects of the item, the card and the box with
`getBoundingClientRect`, then writes `left` and `top` to the box's inline
style. The box's style has no Lit binding, so the next draw does not reset
it. This runs before the browser paints, so the box never shows in the
wrong place. A line spans the whole strip, so its box sits above the strip's
first row. A Temperature chart hour spans the chart, so its box sits above
the chart.

Alternative: CSS anchor positioning. It is not in every browser Home
Assistant's apps use, and happy-dom cannot test it.

### 7. The tap tests' pointer helper moves to the harness

The `pointer()` helper in `card/test/pan.test.ts` moves to
`card/test/harness.ts`, beside a `tap(element, type?)` helper that sends a
`pointerdown` and a `pointerup` at the same point. Both test files import
them.

### 8. The docs

`docs/night-card.md` gets a short subsection, "Reading a value on a phone",
after "The lines" and before "Panning the strip". It says that a tap on a
cell, column, bar, line, Temperature chart hour, message or the moon drawing
shows its hover text in a box, with any pointer, and that a tap elsewhere, a
second tap on the same item, or a pan closes it. The moon drawing paragraph
says "Hover over or tap the drawing". `tests/test_night_card_doc.py` gets
tests for the spec's words.

## Risks / Trade-offs

- [On a desktop, a click shows the box beside the browser's own tooltip,
  with the same text twice] → Accepted with D5. The browser's tooltip is
  slow to appear and the box shows only after a click.
- [A box above a tall item, such as a line or a chart hour, covers the rows
  above it] → It closes on the next tap anywhere, and `pointer-events: none`
  lets a tap through to the item under it.
- [A tap outside the card leaves the box open] → The box is small and inside
  the card. Any tap on the card closes it. A later story can add a
  document-level listener if users ask.
- [Home Assistant's own `ha-card` styles could set `overflow: hidden` or
  their own `position`] → The box stays inside the card by placement, so
  `overflow: hidden` cuts nothing. The card's stylesheet sets
  `position: relative` on `ha-card`, which wins over `ha-card`'s own `:host`
  styles.
- [happy-dom does no layout, so the tests cannot prove the box sits in the
  right place on a real page] → `placeTip` is tested with numbers, and one
  card test stubs `getBoundingClientRect` to check that the box's `left` and
  `top` come from it. Placement on a real phone stays unproven by the
  automated checks; the pull request should say so.

## Migration & Rollback

N/A. Nothing changes shape. Rolling back is reverting the card release; the
core and its entities are untouched.
