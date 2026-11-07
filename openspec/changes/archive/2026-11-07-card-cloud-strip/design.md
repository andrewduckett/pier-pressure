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
  shadow DOM. Every scenario about the card is asserted here. Vitest's fake
  timers (`vi.setSystemTime`) pin the browser clock for the fallback window.
- **Existing seams reused:** `card/test/harness.ts` (gains helpers for cloud
  sensors and a time zone), `card/test/entity.test.ts` (the cloud entity ids),
  and `tests/test_night_card_doc.py`, which already reads `docs/night-card.md`
  for the skeleton's docs scenarios and takes the new docs scenario.

## Scrutiny Tier & Blast Radius

- **Tier:** low
- **Blast radius:** the card's source and tests in `card/`,
  `docs/night-card.md` and its test. No contract, schema, delivery or build
  change.

## Decisions

### DD1. A pure strip model in `card/src/strip.ts`, rendered by the card

`buildStrip(states, pier, now, timeZone)` returns plain data: the axis
(`start`, `end` in epoch milliseconds), the time labels, and the four rows,
each with its label and cells. Each cell holds its hour's start, its clipped
start and end, its shade and its hover text. The card turns that into a
template.

- Alternative: compute inside `render()`. Rejected: it mixes time arithmetic
  with markup, and later stories add more rows and marks to the same axis.
- The card harness stays the primary seam; the model's functions are exported
  so a focused test can pin a hard case, such as a half-hour time zone,
  without building markup.

### DD2. HTML positioned in percent of the axis, not SVG or canvas

The strip is a CSS grid: a label column and a track. The card positions each
cell in the track with `left` and `width` as percentages of the axis span, and
each time label with `left` alone, centred on its instant by
`translateX(-50%)`. Cells get `border-radius: 2px` and a 1 px inset on each
edge that meets a neighbouring hour, which keeps the YAML strip's gap. A cell
cut off at an axis end gets no inset on that edge, so it stays flush with the
axis end.

- Alternative: SVG. A `viewBox` that scales with the card stretches text and
  rounded corners unless the card measures its width, which needs a
  `ResizeObserver` and makes happy-dom tests depend on layout.
- Alternative: canvas. No native hover text, and the tests could not read it.
- Percent positioning reflows for free when the card's width changes, and the
  tests read the inline style and data attributes directly.

### DD3. The test surface is data attributes

The strip carries `data-axis-start` and `data-axis-end` as ISO strings. Each
row carries `data-row` with the variable key, such as `cloud_cover`. Each cell
carries `data-hour` with its hour's start as an ISO string, `data-from` and
`data-to` with its drawn start and end after clipping, and its shade in
`style`. Each time label carries its ISO instant in `data-at`. These follow the
skeleton's `data-field` convention.

### DD4. Hover is the native `title`, mirrored in `aria-label`

Each cell gets `title="Cloud cover, the hour from 21:00: 40%"`, which every
browser shows on hover, and the same text as `aria-label` for screen readers.
Home Assistant's `ha-tooltip` is not used: it is a frontend internal, not a
public element, and the card must not depend on it.

### DD5. Times through `Intl.DateTimeFormat` with `hourCycle: "h23"`

One formatter per render: locale `en-GB`, `numberingSystem: "latn"`, `hour`
and `minute` as `2-digit`, `hourCycle: "h23"` and
`timeZone: hass.config.time_zone`, assembled from `formatToParts` as `HH:MM`.
`h23` makes midnight `00`, never `24`. The pinned locale and `latn` keep the
digits `0` to `9` in a browser set to Arabic, Persian or Bengali, whose
default digits would otherwise defeat the time-label filter. When `hass.config.time_zone`
is missing, or `Intl` rejects it, the card falls back to the browser's time
zone rather than throwing.

### DD6. Time labels by stepping 15 minutes

The model steps through every quarter hour strictly between the axis start and
the axis end. It formats each instant in the time zone. It keeps those whose
minute is `00` and whose hour is a multiple of 3, or of 6 when the axis spans
more than 24 hours. Every time zone in use is offset from UTC by a multiple of
15 minutes. So this finds local whole hours in Kolkata (+05:30) and Kathmandu
(+05:45), and through a clock change, with no offset arithmetic.

When clocks go back, two instants an hour apart format the same, such as
`03:00` twice in Athens. The model drops a label whose text matches the label
it kept just before, if the two are less than 3 hours apart. That rule never
drops the two `12:00` labels of a polar-night axis, which are a day apart.

DD7's 48-hour cap on the window bounds the axis at 57 hours, so the loop runs
at most 228 steps.

### DD7. Lenient reading of every attribute

- The model reads `dark_window.start` and `.end` with `Date.parse`, and only
  when each is a string. It falls back to the 6-and-18-hour window around
  `Date.now()` when either is missing, null or unreadable, when `end` is not
  after `start`, or when they are more than 48 hours apart. The core never
  sends such a window; a hand-edited state or a script could.
- A cloud sensor whose state is `unavailable` gives an empty row, even if it
  still carries a `forecast`. This matches how the skeleton ignores the
  attributes of an unavailable Verdict sensor.
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
rows and axis. `getGridOptions()` asks a sections dashboard for the full width,
`columns: "full"`, as the YAML strip's `grid_options` do, so the time labels
have room. The card picker's description becomes "Tonight's verdict and night
strip for one pier."

No decision here is costly to reverse: each sits inside the card's own source,
behind the published entities.

## Risks / Trade-offs

- [A cell cut off to a few minutes at an axis end is too thin to see or
  hover] → It has no inset on its clipped edge, so it keeps its share of the
  track; a sliver of a few pixels is acceptable at the very end of the night.
- [Time labels crowd on a phone-width card] → Full width by default (DD9),
  and 6-hour labels on a long axis (DD6). A user who forces a narrow column
  accepts tighter labels.
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
