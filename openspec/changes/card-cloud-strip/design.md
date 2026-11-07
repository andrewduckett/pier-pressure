## Context

The card from #180 is one Lit element, `card/src/pierpressure-card.ts`, with
the entity-id rule in `card/src/entity.ts`. It renders a `<dl>` of verdict,
score and confidence inside `ha-card`, or a message when the Verdict sensor is
missing or offline. Its tests mount the real element in happy-dom through
`card/test/harness.ts` and read the shadow DOM.

The four cloud sensors each carry `forecast`: a list of
`{datetime, value}` points, one per timeline hour, in UTC (`docs/night-timeline.md`).
An unavailable sensor has no attributes. The YAML strip in
`docs/night-dashboard.md` is the reference for the window, the shades, the gap
between cells and the hover text.

The card only displays published entities (#132 Shared decisions), so all of
this is display logic in the browser. The core and delivery stay untouched.

## Goals / Non-Goals

**Goals:**

- A strip model built by pure functions from the Verdict and cloud entities,
  the current time and a time zone, so the time arithmetic is testable on its
  own terms.
- A strip that fills the card's width at any size without measuring the DOM.
- An axis that later stories (dusk, dawn, moon, now, other rows) add marks and
  rows to without reworking.

**Non-Goals:**

- Dusk, dawn, moon-up and "now" marks; the other condition rows; the cloud
  agreement band.
- A timer of its own (D12). The strip redraws when Home Assistant sets `hass`.
- Following the user profile's time zone or 12-hour clock setting (D10).

## Test Seams

- **Primary test seam:** the card harness, `card/test/harness.ts`: mount the
  real `pierpressure-card` with a fake `hass`, then read the strip from the
  shadow DOM. Every spec scenario is asserted here. Vitest's fake timers
  (`vi.setSystemTime`) pin the browser clock for the fallback window.
- **Existing seams reused:** `card/test/harness.ts` (gains helpers for cloud
  sensors and a time zone), `card/test/entity.test.ts` (the cloud entity ids).

## Scrutiny Tier & Blast Radius

- **Tier:** low
- **Blast radius:** the card's source and tests in `card/`, and
  `docs/night-card.md`. No contract, schema, delivery or build change.

## Decisions

### DD1. A pure strip model in `card/src/strip.ts`, rendered by the card

`buildStrip(states, pier, now, timeZone)` returns plain data: the axis
(`start`, `end` in epoch milliseconds), the tick labels, and the four rows,
each with its label and cells. Each cell holds its hour's start, its clipped
start and end, its shade and its hover text. The card turns that into a
template.

- Alternative: compute inside `render()`. Rejected: it mixes time arithmetic
  with markup, and later stories add more rows and marks to the same axis.
- The card harness stays the primary seam; the model's functions are exported
  so a focused test can pin a hard case, such as a half-hour time zone,
  without building markup.

### DD2. HTML positioned in percent of the axis, not SVG or canvas

The strip is a CSS grid: a label column and a track. Each cell and tick label
is absolutely positioned in the track with `left` and `width` as percentages of
the axis span. Cells get `border-radius: 2px` and a 1 px inset each side, which
keeps the YAML strip's gap between neighbouring hours.

- Alternative: SVG. A `viewBox` that scales with the card stretches text and
  rounded corners unless the card measures its width, which needs a
  `ResizeObserver` and makes happy-dom tests depend on layout.
- Alternative: canvas. No native hover text, and the tests could not read it.
- Percent positioning reflows for free when the card's width changes, and the
  tests read the inline style and data attributes directly.

### DD3. The test surface is data attributes

The strip carries `data-axis-start` and `data-axis-end` as ISO strings. Each
row carries `data-row` with the variable key, such as `cloud_cover`. Each cell
carries `data-hour` with its hour's start as an ISO string, and its shade in
`style`. Each tick carries its ISO instant in `data-at`. These follow the
skeleton's `data-field` convention.

### DD4. Hover is the native `title`, mirrored in `aria-label`

Each cell gets `title="Cloud cover, the hour from 21:00: 40%"`, which every
browser shows on hover, and the same text as `aria-label` for screen readers.
Home Assistant's `ha-tooltip` is not used: it is a frontend internal, not a
public element, and the card must not depend on it.

### DD5. Times through `Intl.DateTimeFormat` with `hourCycle: "h23"`

One formatter per render: `hour` and `minute` as `2-digit`, `hourCycle: "h23"`
and `timeZone: hass.config.time_zone`, assembled from `formatToParts` as
`HH:MM`. `h23` makes midnight `00`, never `24`. When `hass.config.time_zone`
is missing, or `Intl` rejects it, the card falls back to the browser's time
zone rather than throwing.

### DD6. Ticks by stepping 15 minutes

From the first quarter hour at or after the axis start to the axis end, the
model formats each instant in the time zone and keeps those whose minute is
`00` and whose hour is a multiple of 3. Every time zone in use is offset from
UTC by a multiple of 15 minutes, so this finds local whole hours in Kolkata
(+05:30) and Kathmandu (+05:45) as well as through a DST change, with no
offset arithmetic. A 24-hour axis is under 100 steps.

### DD7. Lenient reading of every attribute

- `dark_window.start` and `.end` are read with `Date.parse`. A missing,
  null or unparseable end of either side falls back to the 6-and-18-hour
  window around `Date.now()`.
- `forecast` that is not an array gives an empty row. A point that is not an
  object, or whose `datetime` does not parse, is skipped.
- A value draws a cell only when `typeof value === "number"` and it is
  finite. The hover shows `String(value)`, so `37.5` stays `37.5%`.
- The shade step is clamped to 0 to 6 at both ends, so a stray negative or
  above-100 value still draws a valid shade.

### DD8. Entity ids from one helper

`entity.ts` gains `pierEntityId(pier, key)`, returning
`sensor.pierpressure_<slug>_<key>`. `verdictEntityId` becomes
`pierEntityId(pier, "verdict")`. The strip asks for `cloud_cover`,
`cloud_low`, `cloud_mid` and `cloud_high`.

### DD9. The card grows

`getCardSize()` returns 5 instead of 2: the verdict lines and the strip's four
rows and axis. The card picker's description becomes "Tonight's verdict and
night strip for one pier."

No decision here is costly to reverse: each sits inside the card's own source,
behind the published entities.

## Risks / Trade-offs

- [The 1 px inset makes a cell clipped to a few minutes at an axis end vanish
  or invert] → Clamp the drawn width at zero; a sliver at the edge is not worth
  a special case.
- [happy-dom or Node lacks full ICU time-zone data] → Node ships full ICU by
  default; the Tokyo and Kolkata scenarios fail loudly if it does not.
- [`hass` changes on every state change in Home Assistant, so the strip
  rebuilds often] → Four rows of at most a few dozen cells each is trivial to
  rebuild; no caching until a profile says otherwise.
- [Native `title` hover appears after a delay and not on touch screens] →
  Accept for this story: it matches the YAML strip's "hover to see". A tap
  target is a later story's choice if adopters ask.

## Migration & Rollback

N/A. Nothing changes shape. Rolling back is reverting the card source; the
published entities are unchanged.
