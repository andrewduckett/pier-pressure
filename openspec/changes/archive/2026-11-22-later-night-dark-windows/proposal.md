<!-- Plain language: Lead with the problem and resulting behavior. Give a reader enough context to decide whether the scope solves that problem. Keep the required headings. -->

## Why

The night strip pans as far as the forecast reaches, often three days, but
only the selected night has dusk and dawn lines. On a later night the weather
rows have no frame, so nobody can tell which hours are dark. This story is the
walking skeleton of epic #299: it takes later nights through the core, the
verdict document, delivery and the card with the smallest payload, one dark
window per night, so the next story (#319) only adds moon and targets.

## What Changes

- **Core:** the producer computes the *later nights*: one per local solar day
  after the selected night, in date order, up to three (D1). A later night
  counts only while its solar day starts before the end of the last hour a
  provider returned for a variable the timeline shows (D2). With no provider
  data there are no later nights.
- **Verdict document (additive):** a new `later_nights` list after
  `observation`. Each entry holds a `dark_window` in the top-level shape, with
  null bounds on a night with no astronomical darkness (D3). The list is always
  present, and empty when there are no later nights (D4). Tonight's fields keep
  their position, value and meaning, and `observation` is no longer the last
  key.
- **Home Assistant delivery:**
  - the Verdict sensor's attributes leave out `later_nights`, as they leave out
    `timeline` (D5);
  - each pier gets three new sensors, Night 2 to Night 4
    (`sensor.pierpressure_<slug>_night_<n>`). The state is that night's dusk as
    a timestamp, and the attributes hold its `later_nights` entry. A sensor is
    unavailable only when its night is not in `later_nights` (D6). A night with
    no astronomical darkness shows state unknown and stays available (D7).
- **Card:** the strip draws the same dashed grey dusk and dawn lines, with the
  same hover text, for each later night, read from the Night sensors. It draws
  them even when tonight has no dark window. A later night with no darkness
  gets no lines and no note (D8). The opening axis and tonight's lines do not
  change.
- **Decision record:** one ADR on how the document and delivery carry later
  nights.
- **Docs:** the README's entity table and `docs/night-card.md`. The glossary
  entry for *Later night* (D9) is already on this branch.

Out of scope: moon and targets for later nights (#319), and any change to
tonight's fields or to the card's opening axis.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `night-verdict`: adds the `later_nights` list, the rule that picks and
  counts later nights, and each entry's dark window. Changes the observation
  requirement, which says `observation` is the document's last key. Extends the
  requirement that hidden variables leave the document unchanged to cover
  `later_nights`.
- `ha-delivery`: the Verdict attributes also leave out `later_nights`; adds
  the Night 2 to Night 4 sensors, their discovery, state, attributes and
  availability, and their place in the publish.
- `night-card`: dusk and dawn lines also mark each later night's dark window;
  panning no longer says other nights have no dusk or dawn line; the docs
  describe the later nights' lines.

## Impact

- **Core:** `pierpressure/core/sky.py` (dark window and solar day for a given
  later solar day), `pierpressure/core/producer.py` (build `later_nights`),
  `pierpressure/core/model.py` (`VerdictDocument.later_nights`, a
  `LaterNight` entry model reusing `DarkWindow`).
- **Delivery:** `pierpressure/delivery/mqtt.py` (attributes exclusion, Night
  sensor discovery, state and attributes, publish order).
- **Card:** `card/src/strip.ts` (read the Night sensors, draw their lines),
  with tests in `card/test/`.
- **Contract:** additive only. One new document key and three new entities per
  pier; no existing topic, entity, unique id or field changes.
- **Docs:** `README.md`, `docs/night-card.md`, a new ADR in `docs/decisions/`.
- **Dependencies:** none.
