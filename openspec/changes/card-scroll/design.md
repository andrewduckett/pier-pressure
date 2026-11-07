## Context

- The strip is built in two layers. `card/src/strip.ts` holds pure functions:
  `stripAxis(night, now)` picks today's fixed axis, and
  `buildStrip(states, pier, now, timeZone)` turns Home Assistant's states into
  a `Strip`. Cells, bands and bars come out already cut off at the axis ends,
  and the now line only while on the axis. The dusk and dawn lines are not
  checked against the axis: on today's fixed axis they always fall inside it.
  `card/src/pierpressure-card.ts` draws a `Strip` as a CSS grid, placing every
  item by its share of the axis in percent.
- Every existing `night-card` requirement about the axis is tested by building
  a strip and reading the drawn `data-*` attributes.
- PierPressure publishes every timeline hour in every timeline sensor's
  `forecast`, with `null` where a variable has no value
  (`pierpressure/delivery/mqtt.py`, `timeline_attributes`). So each sensor's
  `datetime`s are the timeline's hours. Weather sources reach different
  distances: Open-Meteo asks for 2 days, 7Timer! gives 3.
- The card redraws every minute from a `setInterval`, and on every `hass`
  update. Neither keeps any drawing state today.
- Tests run in Vitest with happy-dom, through `card/test/harness.ts`. happy-dom
  has `PointerEvent`, `WheelEvent`, `KeyboardEvent` and `setPointerCapture`,
  but no layout: every element's width is 0, and pointer capture does not
  retarget events.

## Goals / Non-Goals

**Goals:**

- Every axis requirement keeps holding for a panned axis (ledger D7, D9,
  D10).
- One pure function says how far the strip can pan, so the card and the tests
  agree on the reach.
- No new dependency; the card stays one file.

**Non-Goals:**

- Zooming (ledger D4), momentum after a swipe, or snapping a drag to whole
  hours.
- Keeping the axis across a page reload (ledger D12).
- Any change to the YAML strip (#173).

## Test Seams

- **Primary test seam:** the card's Vitest suite under `card/test/`. A new
  `pan.test.ts` mounts the card with `mountCard` and stubs the hours' width
  with a spy on `getBoundingClientRect`. It dispatches pointer, wheel and key
  events on the strip, and clicks on the button. It reads `data-axis-start`
  and `data-axis-end`, which the strip already carries, and the button's
  `hidden` property. The reach function is tested as a plain function, and the
  `touch-action` rule through the harness's `cardStyles`.
- **Docs seam:** `tests/test_night_card_doc.py` gains the "page covers panning"
  scenario.
- **Existing seams reused:** `card/test/harness.ts` (`mountCard`,
  `verdictEntity`, `forecastEntity`, `cardStyles`, the sensor ids). The real
  Home Assistant in `mise run dashboard-check` is the by-eye check (ledger
  D15). It covers what happy-dom cannot: the page scrolling on a vertical
  swipe, pointer capture, and the layout.

## Scrutiny Tier & Blast Radius

- **Tier:** medium. One package, on the card's established patterns, but the
  first input handling the card has. It runs on touch and desktop browsers the
  tests cannot reach.
- **Blast radius:** `card/src/strip.ts`, `card/src/pierpressure-card.ts`,
  `card/test/`, `docs/night-card.md` and its test. No published entity, no
  core code.

## Decisions

### D-1: Pan by drawing the strip for a moved axis

On each pan, the card rebuilds the strip for the new axis and redraws it.
Everything stays placed in percent of the axis, as today.

- *Alternative: native scrolling.* The card would draw every forecast hour in
  an inner element wider than the card, inside an `overflow-x: auto` box. That
  brings touch, trackpad momentum and a scrollbar for free. But it changes
  what "the axis" is. The browser would clip the hours, so no cell is cut off
  at an axis end, and the time labels and lines follow the whole reach. Every
  axis requirement and its tests would need rewriting. A mouse still cannot
  drag a scroll box, so the drag code is needed anyway. The happy-dom tests
  could not see the scroll position either.
- *Why this one:* the existing requirements stay true of whatever axis is
  shown, and the tests keep reading `data-axis-start`.

### D-2: `buildStrip` takes a held start; the card keeps it

`buildStrip` gains an optional `start`. Without it, the axis is the opening
axis, `stripAxis` as today. With it, the axis starts at `start`, clamped into
the reach, and is always as long as the opening axis. The `Strip` gains
`reach` and `opening`, so the card can clamp a pan and decide whether to show
the button.

The card holds one state property, `heldStart`, which is `undefined` until the
user pans. A pan works out a new start from the axis on screen and clamps it
into the reach. If the clamped start equals the start on screen, the pan
changes nothing, so a pan against the reach's end never arms `heldStart`.
Otherwise it sets `heldStart`. "Back to tonight" sets it back to `undefined`.
A render clamps but never writes back to `heldStart`.

- *Alternative: hold an offset from the opening axis.* On a night with no
  darkness the opening axis moves every minute, so the axis would creep under
  the user (against ledger D11).
- *Alternative: hold the panned axis's length too.* The time-label rule and
  the opening axis's span are tied together; holding an old length would show
  a night of the wrong length beside a new verdict.

### D-3: The reach is a pure function of the states

`stripReach(states, pier, opening)` reads the `forecast` of every `ROWS`
sensor and of the two Cloud range sensors. It skips an `unavailable` sensor,
and a point without a readable `datetime`. Each point counts its own hour,
whatever its value. A Rain chance point with a number also counts the hour
before, as `rowCells` draws it; a null Rain chance point does not, so the reach
gains no blank hour before the timeline. The function returns the earliest
hour's start and the latest hour's end, widened to cover the opening axis. It
shares `forecastOf` and `readTime` with the rows.

### D-4: Dusk and dawn lines are checked against the axis

`nightLines` takes the axis and drops a line whose time is off it, as
`nowLine` does. Without this, a panned dusk line would sit at a negative
`left` and draw over the row labels.

### D-5: Pointer events on the strip, one pointer at a time

The `.strip` element listens for `pointerdown`, `pointermove`, `pointerup`,
`pointercancel` and `lostpointercapture`, for mouse, touch and pen alike.

- `pointerdown`, only when no drag is active, only for `isPrimary` and the
  main button, records the `pointerId`, the pointer's `clientX` and `clientY`,
  the axis start, `heldStart`, and the hours' width. Recording the width here
  keeps a layout change mid-drag from changing the scale.
- `pointermove` from another `pointerId` is ignored. Until the drag starts,
  the card waits for the pointer to move more than 8 px sideways and further
  sideways than up or down. Then it calls `setPointerCapture`, so the drag
  goes on when the pointer leaves the card. From then on, each move sets the
  start to the recorded start minus the sideways distance's share of the
  width, times the axis length. Working from the recorded start, not the last
  move, keeps rounding from building up.
- `pointerup` from the active pointer ends the drag where it is.
- `pointercancel` puts `heldStart` back to its recorded value and ends the
  drag. That undoes the few moves a phone browser sends before it takes a
  swipe for scrolling.
- `lostpointercapture` without a `pointerup` ends the drag where it is.

The hours' width is the `getBoundingClientRect().width` of the strip's
time-label track, which spans exactly the hours column. A width of 0, as
before layout, pans nothing.

`touch-action: pan-y` on the strip lets the browser keep vertical swipes for
scrolling the page, and hand sideways ones to the card (ledger D6).
`user-select: none` stops a drag from selecting row labels.

- *Alternative: mouse and touch events.* Two code paths for one gesture, and
  touch events need `preventDefault` on a non-passive listener to stop the page
  from scrolling sideways.

### D-6: Sideways wheel pans; vertical wheel is left alone

A `wheel` listener on the strip pans when `|deltaX| > |deltaY|`, by `deltaX`'s
share of the hours' width. Only then does it call `preventDefault`, so a mouse
wheel still scrolls the page. Lit binds the listener with `passive: false`
through an event-listener object. For `deltaMode` lines the card counts 16 px
a line, and for pages the hours' width, the browsers' usual sizes.

### D-7: The strip takes focus and pans one hour per arrow key

The `.strip` element gets `tabindex="0"`, `role="group"` and the accessible
name "Night strip. Use the Left and Right arrow keys to move through the
forecast." `ArrowLeft` and `ArrowRight` pan an hour, and call
`preventDefault` so the page does not scroll sideways too. A `:focus-visible`
outline in Home Assistant's `--primary-color` shows the focus.

### D-8: The button sits on its own line above the strip, always laid out

"Back to tonight" is a plain `<button>` on a line of its own between the
summary and the strip, aligned right. It is outside `.strip`, so a press on it
never reaches the strip's pointer handlers. The card always draws it. On the
opening axis it carries `hidden`, which the card's styles turn into
`visibility: hidden` rather than `display: none`. So the line keeps its
height, and the button appearing moves nothing. A hidden button cannot take
focus. The button is at least 24 px tall, a comfortable touch target.

Selecting it clears `heldStart` and moves focus to the strip, so a keyboard
user is not left on a button that has just hidden itself.

The button uses Home Assistant's theme variables (`--primary-color`,
`--secondary-text-color`) rather than an `mwc-button`, which Home Assistant
loads only on some pages.

- *Alternative: the strip's empty top-left cell.* It adds no line, but the
  button is wider than the row labels' column and taller than its row, so
  showing it would widen the label column and push every row down, mid-drag.

### D-9: No ADR

Every decision here sits inside `card/src/`, behind the published entities,
and a later change can replace any of them there at little cost.

## Risks / Trade-offs

- [The button's line adds about 28 px to the card even when hidden] → that is
  the price of a button that moves nothing when it shows. `getCardSize` is an
  estimate in 50 px units and stays as it is.
- [A drag redraws the strip on every pointer move, on a slow phone] →
  browsers send at most one `pointermove` per frame, Lit draws once per batch
  of changes, and the strip has about 1,200 items. The by-eye check (ledger
  D15) drags on a real Home Assistant; if it stutters, throttling moves to
  `requestAnimationFrame`, inside the card.
- [The browser reads a sideways trackpad swipe as "go back"] → the wheel
  listener calls `preventDefault` for every sideways movement, even when the
  axis cannot move, so the browser never sees one from the strip.
- [A dashboard wrapper that swipes between views also listens for sideways
  touches] → the card captures the pointer once a drag starts. A wrapper that
  still steals the gesture sends `pointercancel`, which puts the axis back.
- [The tests cannot see layout, scrolling or capture] → the width comes from
  one `getBoundingClientRect` call, which the tests stub. The real Home
  Assistant check covers the rest.

## Migration & Rollback

N/A. Nothing changes shape. Rolling back is reverting the card's source and
docs; the published entities are untouched.
