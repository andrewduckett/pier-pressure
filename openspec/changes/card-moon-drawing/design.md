## Context

- The Verdict sensor's attributes are the whole verdict document. Its `moon`
  attribute holds `illumination` (0 to 1, two decimals), `phase` (one of eight
  names, from 45° octants of the sun-moon elongation), and `rise` and `set`
  (ISO times inside the dark window, or null) (`pierpressure/core/model.py`
  `Moon`; `pierpressure/core/sky.py` `moon_info`).
- `card/src/pierpressure-card.ts` renders a `<dl>` of Verdict, Score and
  Confidence, then the strip. Values come through small readers that turn a
  bad value into a dash (`shownNumber`, `shownText`).
- `card/src/strip.ts` already turns an ISO string into a time (`readTime`,
  private) and formats a time in Home Assistant's time zone (`clock`).
- The card's `HomeAssistant` type models only `states` and
  `config.time_zone`. Home Assistant's frontend object also carries
  `config.latitude`.
- The strip draws with fixed colours, not theme variables, so it reads the same
  in light and dark themes.

## Goals / Non-Goals

**Goals:**

- One small pure reader that turns the `moon` attribute into what the card
  shows, so every dash and drawing rule is tested in one place.
- A drawing that is a few lines of SVG with no image assets and no new
  dependency.

**Non-Goals:**

- No position angle of the bright limb, libration or earthshine (D6).
- No change to the strip, the Moon up lane or `getCardSize`.
- No new card option: the hemisphere comes from Home Assistant (D7).

## Test Seams

- **Primary test seam:** the card harness (`card/test/harness.ts`:
  `mountCard`, then reading the shadow DOM), in a new `card/test/moon.test.ts`.
  It proves every text, dash, drawing and hemisphere scenario from Home
  Assistant states. `mountCard` gains an optional latitude, passed as
  `hass.config.latitude`.
- **Existing seams reused:** `tests/test_night_card_doc.py` for the docs
  requirements; `card/test/render.test.ts`'s offline and not-found cases stay
  as they are, and the moon tests add their own.

## Scrutiny Tier & Blast Radius

- **Tier:** low
- **Blast radius:** the card only: `card/src/` and its tests, and
  `docs/night-card.md`. No Python code, sensor or document field changes.

## Decisions

### DD1. A pure reader in a new `card/src/moon.ts`

`readMoon(attribute, time, latitude)` returns a plain `MoonView`:

```ts
interface MoonView {
  phase: string;         // "Waxing gibbous", or "—"
  illumination: string;  // "78%", or "—"
  rise: string;          // "21:14", or "—"
  set: string;
  drawing?: MoonDrawing; // only when phase and illumination are both valid
}
interface MoonDrawing {
  lit: "none" | "all" | number; // number: the illumination, 0 to 1
  mirrored: boolean;             // true: lit on the left
  text: string;                  // "Moon: waxing gibbous, 78% lit"
}
```

`time` is the strip's `clock(timeZone)`. `readTime` moves from private to
exported in `strip.ts` so both share one parser. The card renders the view.
Alternative: read the fields inline in `renderBody`, as Score does. Rejected:
eleven rules are easier to test against one function, and the strip already
follows this split (`buildStrip` then render).

### DD2. Which side is lit

Waxing phases set `mirrored` to `false` (lit on the right), waning to `true`.
When `latitude` is a number below 0, `mirrored` flips. Any other latitude,
including a missing one, keeps the northern view. `new` gives `lit: "none"`
and `full` gives `lit: "all"`, whatever the illumination (D8); they have no
side, so `mirrored` is `false`.

### DD3. The SVG

A 48 px SVG with `viewBox="-1.1 -1.1 2.2 2.2"`, so the outline's stroke is not
clipped:

1. The unlit disc: `<circle r="1">` filled `#3b3a36` with a `#898781` stroke,
   the strip's grey. It always draws, so a new moon shows its outline.
2. The lit part, filled `#ece8dc`:
   - `lit: "all"`: a second `<circle r="1">`.
   - a number `k`: one `<path>` lit on the right, inside
     `<g transform="scale(-1 1)">` when `mirrored`:
     `M 0 -1 A 1 1 0 0 1 0 1 A <rx> 1 0 0 <sweep> 0 -1 Z`, where
     `rx = |1 − 2k|`, and `sweep` is `0` for `k < 0.5` (the terminator bulges
     right, a crescent) and `1` otherwise (it bulges left, a gibbous).
   - `lit: "none"`: nothing.

The path is the right half-disc's edge, then the terminator as a half-ellipse
back to the top. The terminator crosses the middle at `x = 1 − 2k`, so the lit
part spans `2k` of the width 2, which is the share the spec asks for. That is
the sphere's terminator seen face on, so the lit area is also `k`. At
`k = 0.5`, `rx = 0` draws a straight line, which SVG allows.

The SVG has `role="img"`, `aria-label` and a `<title>`, all the drawing's
`text`, so hovering shows it too. The `<svg>` carries `data-lit` (`none`,
`all` or the number) and `data-mirrored`, so tests can tell what was drawn
without a layout engine. Tests also read the path's `rx` and `sweep` to check
the span.

Alternative: eight fixed images, one per phase, as astroweather-card does.
Rejected: they ignore the illumination, and add assets to the one-file build.

### DD4. Layout

The `<dl>` and a new `<section class="moon">` sit in a `.summary` flex row
that wraps, with a 16 px gap, so on a narrow card the moon moves under the
verdict lines rather than squeezing them. The section holds the SVG, then its
own `<dl>` with **Phase**, **Illumination**, **Moonrise** and **Moonset**,
styled like the verdict lines. The texts carry `data-field="moon-phase"`,
`moon-illumination`, `moon-rise` and `moon-set`, as the verdict lines carry
theirs.

`getCardSize` stays as it is: side by side, the section is one line taller
than the verdict lines, well under one 50 px unit.

### DD5. Valid values

- Phase: exactly one of the eight names, else invalid.
- Illumination: a finite number from 0 to 1, else invalid. Shown as
  `Math.round(k * 100)` and `%`.
- Rise and set: a string `Date.parse` accepts, else a dash.
- The `moon` attribute itself: an object, else every text is a dash and there
  is no drawing.

## Risks / Trade-offs

- [Home Assistant's latitude is the home's, not the pier's] → A pier is almost
  always in the same hemisphere as its Home Assistant. The docs say which
  location the card uses.
- [A phase near the equator is tilted, not left or right] → Out of scope (D6);
  the drawing is a reading aid, and the phase name and percent carry the facts.
- [Fixed colours on an unusual theme] → The same choice as the strip; the disc
  has an outline, so it shows on any background.
- [`full` or `new` hides a sliver of up to 4%] → The phase name and percent
  stay beside it (D8).

## Migration & Rollback

N/A. The card adds a section; reverting the card file removes it. No sensor or
document changes.
