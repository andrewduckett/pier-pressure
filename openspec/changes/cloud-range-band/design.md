## Context

- The core already fills `TimelineEntry.cloud_cover_min` and `cloud_cover_max`
  (`pierpressure/core/producer.py` `_cloud_band`): both are numbers when two or
  more providers gave cloud cover for the hour, and both are null otherwise.
- The delivery adapter publishes one sensor per row of `TIMELINE_SENSORS`
  (`pierpressure/delivery/mqtt.py`), through one code path: discovery, state
  and a `forecast` attributes payload. A row's `key` must be a float field of
  `TimelineEntry`, and its `name` must slug to its key
  (`tests/test_timeline_sensors.py`).
- The card builds a plain `Strip` object in `card/src/strip.ts` (`buildStrip`)
  and renders it in `card/src/pierpressure-card.ts`. Each row is a `Row` with
  `cells`, or with a `missing` message when it has none. A row's track is
  16 px tall, and each cell is positioned across it by percent of the axis.
- With the default providers only Open-Meteo gives cloud cover, so on most
  installs every hour's min and max is null.

## Goals / Non-Goals

**Goals:**

- Publish the two values with no new delivery code: two table rows.
- Draw the band with the same horizontal placement, hover and message
  machinery the other rows use.

**Non-Goals:**

- No change to the core, the verdict document, agreement or confidence.
- No change to the YAML dashboard.
- No shading of the band by value: the bar's height and position carry the
  meaning.

## Test Seams

- **Primary test seam:** the card harness (`card/test/harness.ts`: `mountCard`
  with `forecastEntity` states, then reading the shadow DOM), in a new
  `card/test/range.test.ts`. It proves the row's order, bars, hover and
  messages from Home Assistant states.
- **Existing seams reused:** the fake MQTT client in
  `tests/test_timeline_sensors.py` for the two sensors, and the doc tests in
  `tests/test_timeline_docs.py` and `tests/test_night_card_doc.py`.

## Scrutiny Tier & Blast Radius

- **Tier:** medium
- **Blast radius:** `pierpressure/delivery/mqtt.py`'s sensor table (the MQTT
  delivery surface grows by two entities per pier; no existing topic or payload
  changes), and the card's strip model and rendering. The core is untouched.

## Decisions

### DD1. Two rows appended to `TIMELINE_SENSORS`

`TimelineSensor("cloud_cover_min", "Cloud cover min", "%", "mdi:weather-cloudy")`
and the same for `cloud_cover_max`, after Precipitation probability. Every
discovery, state, attribute and publish-order rule then applies unchanged, and
every message published before them keeps its place (timeline-sensors DD6).

Alternative: one "Cloud range" sensor whose forecast points carry `{low, high}`.
Rejected: it would need a second payload shape and its own code path, and its
state could not be one number.

### DD2. A `Band` list on the row, not a new kind of cell

`Row` gains an optional `bands: Band[]`. Only the Cloud range row has it; its
`cells` is always empty. A `Band` holds what a `Cell` holds for placement
(`hour`, `from`, `to`), plus `low`, `high` and the hover `text`.

`buildStrip` builds the row after Cloud cover, so `strip.rows` keeps the
top-to-bottom order the renderer draws and the grid row count stays
`rows.length + targets.length + 3`. The row's key is `cloud_range`.

Alternative: a separate `Strip.cloudRange` field. Rejected: the renderer and
the grid count would need a special case to place it between two rows.

Alternative: put `low` and `high` on `Cell`. Rejected: every other row's cell
would carry two always-absent fields, and `value`, `shade` and `arrow` mean
nothing for a band.

### DD3. Pairing the two forecasts

The row reads both forecasts into maps from hour to value, using the existing
`hourlyValues` helper. An hour gets a band only when both maps hold a finite
number for it. `low` is the smaller of the two and `high` the larger, each
clamped to 0–100 for drawing; the hover text shows the values as the forecasts
hold them, lower first. Horizontal placement reuses the cell rule: the hour
starts at `datetime`, is cut off at the axis ends, and an hour wholly off the
axis is dropped.

### DD4. How a band draws

Each band renders as a `.cell` element across its hour, in the lightest blue
(`#cde2fb`), so the hour's 0–100% column is visible. Inside it, a `.range`
element in the dark blue `#256abf` sits at `bottom: <low>%` with
`height: max(2px, <high − low>%)`. So two forecasts that agree still show as a
2 px line. At 100% the line is pulled down to stay inside the track, by
`bottom: min(<low>%, calc(100% - 2px))`.

The Cloud range track is 32 px tall, twice a shade row, so a 15% step is about
5 px. The `.cell` element carries `data-hour`, `data-from`, `data-to`,
`data-low` and `data-high`, and the hover text in `title` and `aria-label`, as
the other cells do.

The card still reports a size of 10 plus its target lanes. The extra 18 px is
well under one of Home Assistant's 50 px size units.

Alternative: draw the band on the Cloud cover row. Rejected in the brainstorm
(D6).

### DD5. The row's message

When the row has no band, `missing` is the first that applies: `Not found` for
the min sensor, then for the max sensor; `Unavailable` for the min sensor, then
for the max sensor; otherwise `Needs two forecasts`, with the hover text
`No hour on the strip has cloud cover from two or more forecasts`. The
`Missing.message` union gains `"Needs two forecasts"`; the renderer's
`data-missing` value is `needs-two-forecasts`, from the existing rule.

An unavailable sensor's kept forecast is ignored, as for every other row
(`forecastOf`).

### DD6. Docs

- `docs/night-timeline.md`: two rows in the sensor table, two entities in the
  recorder exclusions, and "seventeen" for "fifteen". The two sensors' state is
  unknown for an hour with fewer than two forecasts.
- `README.md`: the two sensors in the entity table, both MQTT topic tables, the
  discovery pattern and the removal loop.
- `docs/night-card.md`: Cloud range in the row table, a paragraph on how to
  read it, its hover, `Needs two forecasts` with the other messages, and a
  troubleshooting entry that says to add a second provider that gives cloud
  cover, such as an Open-Meteo model.

### ADR

None. This adds two rows to an existing table under ADR 0025 and one row to the
card under ADR 0034. Both are cheap to reverse.

## Risks / Trade-offs

- [On most installs the row says `Needs two forecasts` for good] → The message
  says what is missing, and the docs say how to add a second cloud provider.
- [Six more retained messages per pier on every publish] → Each attributes
  payload is the same size as Cloud cover's, well under the 16 KiB recorder
  limit; the doc tells recorder users to exclude the two new entities.
- [A taller row breaks the strip's even rhythm] → It is the only row whose
  height carries a value, and it sits right under the Cloud cover row it
  explains.

## Migration & Rollback

Adding: on the first publish after upgrade, Home Assistant discovers two new
entities per pier. Nothing to migrate.

Rolling back: an older release no longer publishes the two sensors, but their
retained discovery configs stay on the broker, so Home Assistant keeps the
entities with their last state. Clear them as the README's "Removing the
entities" says. The older card ignores them.
