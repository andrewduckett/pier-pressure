## Context

- The strip is built in two layers. `card/src/strip.ts` holds pure functions:
  `stripAxis(night, now)` picks today's fixed axis, and
  `buildStrip(states, pier, now, timeZone)` turns Home Assistant's states into
  a `Strip` of cells, bands, bars, lines and labels, each already cut off at
  the axis ends. `card/src/pierpressure-card.ts` draws a `Strip` as a CSS grid,
  placing every item by its share of the axis in percent.
- Every existing `night-card` requirement about the axis (cells cut at its
  ends, time labels, the now line only while on it, target bars cut off at it)
  is tested by building a strip and reading the drawn `data-*` attributes.
- The card redraws every minute from a `setInterval`, and on every `hass`
  update. Neither keeps any drawing state today.
- Tests run in Vitest with happy-dom, through `card/test/harness.ts`. happy-dom
  has `PointerEvent`, `WheelEvent`, `KeyboardEvent` and `setPointerCapture`,
  but no layout: every element's width is 0.

## Goals / Non-Goals

**Goals:**

- Every axis requirement keeps holding, word for word, for a panned axis
  (ledger D7, D9, D10).
- One pure function says how far the strip can pan, so the card and the tests
  agree on the reach.
- No new dependency; the card stays one file.

**Non-Goals:**

- Zooming (ledger D4), momentum after a swipe, or snapping a drag to whole
  hours.
- Keeping the view across a page reload (ledger D12).
- Any change to the YAML strip (#173).

## Test Seams

- **Primary test seam:** the card's Vitest suite under `card/test/`. A new
  `pan.test.ts` mounts the card with `mountCard`, stubs the hours' width with
  a spy on `getBoundingClientRect`, dispatches pointer, wheel and key events on
  the strip, and reads `data-axis-start` and `data-axis-end`, which the strip
  already carries. The reach function is tested as a plain function.
- **Docs seam:** `tests/test_night_card_doc.py` gains the "page covers panning"
  scenario.
- **Existing seams reused:** `card/test/harness.ts` (`mountCard`,
  `verdictEntity`, `forecastEntity`, the sensor ids). The real Home Assistant
  in `mise run dashboard-check` is the by-eye check (ledger D15), not an
  automated seam.

## Scrutiny Tier & Blast Radius

- **Tier:** medium. One package, on the card's established patterns, but the
  first input handling the card has, and it runs on touch and desktop
  browsers the tests cannot reach.
- **Blast radius:** `card/src/strip.ts`, `card/src/pierpressure-card.ts`,
  `card/test/`, `docs/night-card.md` and its test. No published entity, no
  core code.

## Decisions

### D-1: Pan by drawing the strip for a moved axis

On each pan, the card rebuilds the strip for the new axis and redraws it.
Everything stays placed in percent of the axis, as today.

- *Alternative: native scrolling.* Draw every forecast hour in an inner
  element wider than the card, inside an `overflow-x: auto` box. It brings
  touch, trackpad momentum and a scrollbar for free. But it changes what "the
  axis" is: the browser clips the hours, so no cell is cut off at an axis end,
  the time labels follow the whole reach, and the now line is drawn when off
  screen. Every axis requirement and its tests would need rewriting. A mouse
  still cannot drag a scroll box, so the drag code is needed anyway. The
  happy-dom tests could not see the scroll position either.
- *Why this one:* the existing requirements stay true of whatever axis is
  shown, the tests keep reading `data-axis-start`, and a strip of about 1,200
  items redraws well inside a frame.

### D-2: `buildStrip` takes a held start; the card keeps it

`buildStrip` gains an optional `start`. Without it, the axis is the opening
axis, `stripAxis` as today. With it, the axis has the opening axis's length,
starts at `start`, and is clamped into the reach. The `Strip` gains `reach`
and `opening`, so the card can clamp a pan and decide whether to show the
button.

The card holds one state property, `heldStart`, which is `undefined` until the
user pans. A pan sets it from the axis on screen, so a pan always starts from
what the user sees. "Back to tonight" sets it back to `undefined`. Clamping on
each draw does not write back to `heldStart`: a render never changes state.

- *Alternative: hold an offset from the opening axis.* On a night with no
  darkness the opening axis moves every minute, so the view would creep under
  the user (against ledger D11).

### D-3: The reach is a pure function of the states

`stripReach(states, pier, opening)` reads the `forecast` of every `ROWS`
sensor and of the two Cloud range sensors, skips an `unavailable` sensor, a
point without a readable `datetime`, and shifts a Rain chance point back an
hour, as `rowCells` does. It returns the earliest hour's start and the latest
hour's end, widened to cover the opening axis. It shares `forecastOf` and
`readTime` with the rows, so a row and the reach cannot disagree on a point.

### D-4: Pointer events on the strip, with `touch-action: pan-y`

The `.strip` element listens for `pointerdown`, `pointermove`, `pointerup`
and `pointercancel`, for mouse, touch and pen alike. On `pointerdown` from the
primary button it records the pointer's `clientX` and the axis start, and
calls `setPointerCapture`, so the drag goes on when the pointer leaves the
card. Each `pointermove` sets `heldStart` to the recorded start minus the
moved distance's share of the hours' width, times the axis length. Working
from the recorded start, not the last move, keeps rounding from building up.

The hours' width is the `getBoundingClientRect().width` of the strip's
time-label track, which spans exactly the hours column. A width of 0, as
before layout, pans nothing.

`touch-action: pan-y` on the strip lets the browser keep vertical swipes for
scrolling the page and hand sideways ones to the card (ledger D6).
`user-select: none` stops a drag from selecting row labels.

- *Alternative: mouse and touch events.* Two code paths for one gesture, and
  touch events need `preventDefault` on a non-passive listener to stop the page
  from scrolling sideways.

### D-5: Sideways wheel pans; vertical wheel is left alone

A `wheel` listener on the strip pans when `|deltaX| > |deltaY|`, by `deltaX`'s
share of the hours' width. Only then does it call `preventDefault`, so a mouse
wheel still scrolls the page. Lit binds the listener with `passive: false`
through an event-listener object. `deltaMode` lines count 16 px and pages the
hours' width, the browsers' usual sizes.

### D-6: The strip takes focus and pans one hour per arrow key

The `.strip` element gets `tabindex="0"`, `role="group"` and the accessible
name "Night strip. Use the Left and Right arrow keys to move through the
forecast." `ArrowLeft` and `ArrowRight` pan an hour, and call
`preventDefault` so the page does not scroll sideways too. A `:focus-visible`
outline in Home Assistant's `--primary-color` shows the focus.

### D-7: The button sits in the strip's top-left cell

"Back to tonight" is a plain `<button>` in the grid's top-left cell, above the
row labels and beside the dusk, dawn and now labels. That cell is empty today,
so the button appearing or going adds no height and moves nothing. It is shown
while the drawn axis start differs from the opening axis start, which covers a
pan that a clamp undid. It uses Home Assistant's theme variables
(`--primary-color`, `--secondary-text-color`) rather than an `mwc-button`,
which Home Assistant loads only on some pages.

### D-8: No ADR

Every decision here sits inside `card/src/`, behind the published entities,
and a later change can replace any of them there at little cost.

## Risks / Trade-offs

- [A drag redraws the strip on every pointer move, on a slow phone] → Lit
  batches updates to one per frame at most, and the strip has about 1,200
  items. The by-eye check (ledger D15) drags on a real Home Assistant; if it
  stutters, throttling moves to `requestAnimationFrame`, inside the card.
- [The browser reads a sideways swipe at the reach's end as "go back"] → the
  wheel listener calls `preventDefault` for every sideways movement, even when
  the axis cannot move, so the browser never sees one from the strip.
- [A tap on a cell meant to show its hover text starts a drag] → a tap moves 0
  px, so the axis does not move and the button does not appear.
- [`heldStart` survives a change of pier in the editor] → the reach clamps it,
  and "Back to tonight" shows, so the user is never stranded. Resetting it on
  `setConfig` is one line, and the card does so.
- [The tests cannot see layout] → the width comes from one
  `getBoundingClientRect` call, which the tests stub; the real Home Assistant
  check covers the rest.

## Migration & Rollback

N/A. Nothing changes shape. Rolling back is reverting the card's source and
docs; the published entities are untouched.
