<!-- Plain language: Help the next implementer find the approach, understand the choices and act on the plan. Explain necessary technical terms. Put each risk beside its mitigation and each open question beside the decision it affects. -->

## Context

- `pierpressure/core/sky.py` selects tonight's night from the evaluation
  instant (`dark_window`), finds its local solar day (`night_solar_day`), and
  lists the hours the timeline always carries (`night_hours`). Solar days come
  from `_local_solar_day`, which falls back to the UTC calendar day at the exact
  poles.
- `pierpressure/core/producer.py` builds the `timeline` from the night's hours
  joined with every hour a shown variable's filled series covers. It is the
  only place that knows the timeline's hours, so it is where later nights are
  counted.
- `VerdictDocument` in `pierpressure/core/model.py` declares fields in contract
  order. Each additive field so far went last: `timeline`, `agreement`,
  `observation`. The Verdict attributes are
  `document.model_dump_json(exclude={"timeline"})` in
  `pierpressure/delivery/mqtt.py`.
- The rank sensors (Target 1 to Target 10) already set the pattern a Night
  sensor needs. Discovery, state and attributes are all retained, every publish
  writes every rank, and availability combines the shared last-will topic with
  a template on an `available` attribute flag. The health sensors set the
  timestamp pattern: `device_class: timestamp`, ISO 8601 with `+00:00`, and the
  literal `None` for unknown.
- On the card, `buildStrip` in `card/src/strip.ts` reads the Verdict sensor's
  `dark_window` through `darkWindow()`. That function rejects unreadable,
  reversed and over-48-hour windows. `nightLines()` then filters the lines to
  the axis. A tap box finds its line again after a redraw by the key
  `line:<kind>` (`card/src/tap.ts`).
- The committed goldens in `tests/fixtures/golden/` pin whole documents byte
  for byte, so they gain `later_nights` and must be regenerated.

## Goals / Non-Goals

**Goals:**

- One pure function in `sky.py` gives the dark window of any given local solar
  day, so tonight's selection logic stays untouched.
- `later_nights` is a deterministic function of the pier, the instant and the
  timeline's hours.
- The `later_nights` entry shape and the Night sensors' attribute layout leave
  room for #319 to add `moon` and `targets` without changing anything this
  change ships.

**Non-Goals:**

- Changing how tonight is selected, or any tonight field.
- A verdict, score, confidence or reasons for a later night.
- Night sensors in the Verdict attributes, the narrative prompt or the README's
  dashboard YAML examples.
- Any card change beyond lines: no notes, messages, lanes or axis changes.

## Test Seams

- **Primary test seam:** `produce_verdict` with a pinned clock and a built
  conditions value, as `tests/test_producer_timeline.py` already does. It
  proves every `night-verdict` scenario at the document level.
- **Existing seams reused:**
  - `publish_verdict` against the recording fake MQTT client, as in
    `tests/test_timeline_sensors.py` and `tests/test_top_target.py`, for the
    Night sensors and the Verdict attributes. `tests/test_discovery.py`
    validates the discovery schema.
  - `buildStrip` with a `States` map in `card/test/strip.test.ts` and
    `card/test/pan.test.ts`, for the lines. `card/test/tap.test.ts` covers tap
    identity through the render harness.
  - `tests/test_night_card_doc.py` for the doc requirements.
  - `tests/test_golden_verdict.py`, regenerated with `PP_WRITE_GOLDENS=1`.

## Scrutiny Tier & Blast Radius

- **Tier:** high. The change adds to the frozen verdict-document contract and
  adds three Home Assistant entities per pier, across core, delivery and card.
- **Blast radius:** `pierpressure/core/sky.py`, `model.py` and `producer.py`;
  `pierpressure/delivery/mqtt.py`; `card/src/strip.ts`, `tap.ts` and
  `pierpressure-card.ts`; the goldens; `README.md` and `docs/night-card.md`.
  No configuration, provider or scoring code changes.

## Decisions

### DD1. A solar day's dark window comes from that day alone

Add `sky.solar_day_dark_window(pier, day_start, day_end)`. It finds the
astronomical-night flips inside `[day_start, day_end)` with the same
`dark_twilight_day` classification `_night_transitions` uses:

- **No flips:** read the sun's altitude at the day's midpoint. Below −18°, the
  window is the solar day (continuous night). Otherwise both bounds are null.
- **Flips:** dusk is the first dusk inside the day, or `day_start` when the day
  starts dark. Dawn is the first dawn after that dusk, or `day_end` when the
  day ends dark.
- Both bounds go through `_second_floor_window`, so a sub-second sliver becomes
  null, as it does tonight.

*Rejected: calling `dark_window(pier, solar_midnight)`.* It selects by "the
first dawn at or after the instant". On a solar day with no darkness it returns
the next day's night, which breaks "A later night with no astronomical darkness
has null dark-window bounds" (the 2026-08-03 Scotland scenario).

For an ordinary or continuous night, DD1 gives the same bounds `dark_window`
gives for that night. A test pins that equality on the London and 88° N
scenarios.

### DD2. Solar days chain from the selected night's solar day

Add `sky.next_solar_day(pier, day_end)`. It returns the solar day that starts
at `day_end`, found by searching from `day_end` plus half a day, the midpoint
trick `night_solar_day` already uses. It is floored to whole seconds, so day
`k+1` starts at the floored end of day `k`. The pole fallback comes for free
from `_local_solar_day`.

### DD3. The producer counts the later nights from the timeline's times

In `producer.py`, a private `_later_nights(pier, instant, window, times)` runs
after the timeline's sorted `times` are known. Starting from
`night_solar_day(...)`, it chains up to `LATER_NIGHTS = 3` days. It keeps a day
only while some `t` in `times` has `day_start <= t < day_end`, and stops at the
first day with none. `times` is computed once and shared with `_timeline`, so
both read the same hours. No forecast value is read, which keeps "The later
nights read only the timeline's hours" true by construction.

*Rejected: counting inside `sky.py`.* The sky module does not see the
conditions, and the rule is about the timeline.

### DD4. The document gets `LaterNight` entries after `observation`

Add `LaterNight(BaseModel)` with `extra="forbid"` and one field,
`dark_window: DarkWindow`. Add `later_nights: list[LaterNight] =
Field(default_factory=list)` as the last field of `VerdictDocument`. #319 adds
`moon` and `targets` to `LaterNight` after `dark_window`. Recorded in ADR-0043.

### DD5. Night sensors copy the rank sensors' availability and the health sensors' timestamp

In `mqtt.py`, add `NIGHTS = (2, 3, 4)`, plus these functions:

- `night_state_topic` and `night_attributes_topic`: `<base>/<pier>/night_<n>/state`
  and `/attributes`;
- `build_night_discovery`: `name: "Night <n>"`, `unique_id: <node>_night_<n>`,
  `device_class: timestamp`, the two-entry `availability_mode: all` list of
  the rank sensors, and `icon: mdi:weather-night`;
- `night_state` and `night_attributes`.

The state is `_iso(dark_window.start)`, or `None` when the night is absent or
its start is null. The attributes are `{"available": true, "night": n,
**entry}`, or `{"available": false, "night": n}`. As with the rank sensors,
`update` re-asserts `available` and `night` so a future entry key cannot
replace them. `publish_verdict` writes discovery, state and attributes for all
three nights on every publish, after the timeline sensors.

The Verdict attributes become
`model_dump_json(exclude={"timeline", "later_nights"})`. Recorded in ADR-0044.

*Rejected: one sensor holding every later night.* Its state could not be a
timestamp, and the card would need a second way of finding a night. One sensor
per night matches Target 1 to Target 10.

### DD6. The card reads each Night sensor through `darkWindow()`

In `buildStrip`, for `n` in 2 to 4:

1. Look up `states[pierEntityId(pier, "night_" + n)]`.
2. Skip it when it is missing or its state is `unavailable` or `unknown`.
3. Otherwise pass `asRecord(attributes.dark_window)` to `darkWindow()`, and
   draw its lines with `nightLines()`.

The lines are drawn regardless of the opening axis. Reusing `darkWindow()`
gives the readable, ordered and at-most-48-hours rules the spec states. Tonight
stays as it is: its lines exist only when `night` came from the Verdict
sensor.

`Line` gains `night: number`, which is 1 for tonight. `tipKey.line(kind, night)`
returns `line:<kind>` for night 1, so tonight's keys do not change, and
`line:<kind>:<n>` otherwise. The rendered `data-line` stays the kind, and
`data-night` is added for tests. Line order in `strip.lines` is tonight, then
Nights 2 to 4, then now.

### DD7. Docs and goldens

- `README.md`, "Home Assistant entities": one row for **Night 2** to
  **Night 4**.
- `docs/night-card.md`, "The lines" and "Panning the strip": later nights' dusk
  and dawn lines, the sensors, and that a night with no darkness has none. The
  "No astronomical darkness tonight" help says a later night can still show
  lines.
- Regenerate the goldens in their own commit, and check that their diff only
  adds `later_nights`.

## Risks / Trade-offs

- [In continuous polar night, one night's dawn and the next night's dusk fall
  at the same second, so a `dawn` and a `dusk` label overlap] → Accept it. Both
  lines are correct and hover still names each one. The tap key carries the
  night, so tapping cannot confuse them.
- [Night 4 can exist with its dusk just past the strip's reach, as at 18:00 in
  London in November] → Accept it (D2 in the brainstorm). The sensor still
  gives a correct dusk, and the card only draws what is on the axis.
- [A transition day near polar night's start or end gives a window that starts
  or ends at a solar noon] → DD1 clamps the window to the day, and a test
  covers a day that starts dark.
- [Three extra sky searches per recompute] → Each is one `find_discrete` over a
  day plus one meridian search. That is small next to target ranking, and no
  cache is needed.
- [Home Assistant's recorder stores the Night sensors' attributes] → Each
  payload is under 200 bytes now. #319 adds targets, and its design checks the
  16 KiB limit.

## Migration & Rollback

Additive. Home Assistant creates the three Night sensors from discovery on the
first publish after upgrade, and nothing existing changes. To roll back, deploy
the previous image. The retained Night sensor topics stay on the broker until
they are cleared, as the README's "Removing the entities" section describes.
No data migration.
