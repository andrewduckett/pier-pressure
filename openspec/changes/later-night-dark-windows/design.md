<!-- Plain language: Help the next implementer find the approach, understand the choices and act on the plan. Explain necessary technical terms. Put each risk beside its mitigation and each open question beside the decision it affects. -->

## Context

- `pierpressure/core/sky.py` already has everything the later nights need:
  `dark_window(pier, instant)` selects a night and handles the polar cases,
  `_local_solar_day(pier, instant)` finds the noon-to-noon solar day that holds
  an instant, and `night_solar_day` gives the selected night's solar day.
- Skyfield finds a solar noon to about a millisecond. A search that starts at a
  noon it found can land on either side of that noon. `night_solar_day` already
  works around this by searching from a day's midpoint.
- `Conditions.hours(TIMELINE_VARIABLES)` returns every hour a filled series of a
  shown variable covers. Alternates and hidden variables are already left out.
  The timeline uses the same call.
- `VerdictDocument` (Pydantic) emits keys in declaration order, and
  `observation` is the last field today.
- `pierpressure/delivery/mqtt.py` has a pattern for sensors that may have
  nothing to show: the rank sensors (Target 1 to Target 10). Their attributes
  carry an `available` flag, and their discovery availability needs both the
  shared last-will topic and that flag (`availability_mode: all`).
- `card/src/strip.ts` reads the Verdict sensor's `dark_window` with
  `darkWindow()`, which rejects an unreadable, reversed or over-48-hour window,
  and draws lines with `nightLines()`. A tap box finds its line again by
  `tipKey.line(kind)`, which assumes one line of each kind.

## Goals / Non-Goals

**Goals:**

- Reuse the selected night's dark-window rules for every later night, so the
  polar and grazing-night cases behave the same on every night.
- Keep the core deterministic: the later nights depend only on the pier, the
  instant and the conditions.
- Add the Night sensors in the same shape as the rank sensors, so the
  delivery has one pattern for "a slot that may be empty".

**Non-Goals:**

- Moon and targets for later nights (#319 adds them to each entry).
- Any change to tonight's fields, the timeline or the card's opening axis.
- Fixing the existing quirks of `dark_window` near the edges of polar night
  (see Risks). Later nights inherit them.

## Test Seams

- **Primary test seam:** `produce_verdict` with a `FixedClock` and a built
  `Conditions` value, asserting on the document. Every night-verdict scenario
  is a test here.
- **Existing seams reused:**
  - `MqttDelivery.publish_verdict` with `FakeMqttClient` from
    `tests/conftest.py` (as in `tests/test_publish.py` and
    `tests/test_timeline_sensors.py`), for every ha-delivery scenario.
  - The card harness in `card/test/harness.ts`, rendering the card with
    Home Assistant states (as in `card/test/strip.test.ts`,
    `card/test/pan.test.ts` and `card/test/tap.test.ts`), for every night-card
    scenario.
  - `tests/test_golden_verdict.py`: the goldens gain `later_nights` and are
    regenerated once with `PP_WRITE_GOLDENS=1`.
  - `tests/test_night_card_doc.py` for the docs requirement.

## Scrutiny Tier & Blast Radius

- **Tier:** medium
- **Blast radius:** the core's sky and producer modules, the verdict document
  contract (one additive key), the MQTT delivery (three new entities per pier
  and one more key left out of the Verdict attributes), and the card's strip.
  No configuration, provider, scoring or ranking code changes.

## Decisions

### DD1. Chain the later solar days from the selected night's solar day

Start from the end of `night_solar_day(pier, instant, window)`. Each next solar
day starts exactly at the previous day's end. Its end is the end of
`_local_solar_day(pier, previous_end + half a day)`, searched from the middle
of the day, never from the noon itself, so millisecond jitter cannot return
the previous day. Floor each end to whole seconds, as `night_solar_day` does.
Reusing the previous end, rather than looking the same noon up again, matters
because two lookups with different search brackets can differ by about 0.1 ms,
and such a difference can cross a whole second and floor to a 1-second gap or
overlap.

- *Alternative:* add 24 hours to each noon. Rejected: solar noon drifts by up
  to about 30 seconds a day, so the days would drift off the real noons the
  timeline uses.

### DD2. Find each later night's window with `dark_window`, then keep it only if it belongs to the day

For a solar day from `day_start` to `day_end`, call
`dark_window(pier, day_start + 1 minute)`. Keep the result only when its
midpoint lies in `[day_start, day_end)`; otherwise the window is
`(None, None)`. The minute keeps the selection, and the continuous-night
anchor, inside the day despite noon jitter. The midpoint check stops a day with
no darkness from borrowing the next day's night, which `dark_window` would
otherwise select. When a kept window starts within one second of `day_start`
and ends within one second of `day_end`, it is the continuous-night window,
which `dark_window` anchors to its own lookup of the solar day: use the
chained `(day_start, day_end)` instead, so consecutive windows meet exactly.

Checked against the bundled ephemeris for the spec's scenarios: London in
September, the end of darkness at 52° N in May, and continuous polar night at
88° N, where the three windows run noon to noon with no gap or overlap.

- *Alternative:* a new crossing search over each solar day. Rejected: it would
  duplicate the polar-night and grazing-night rules, and the two copies could
  drift apart.

Put this in a new public function in `sky.py`, `later_night_windows(pier,
instant, window, reach_end)`, which returns the list of windows. It holds DD1,
DD2 and DD3, so the producer only builds the models.

### DD3. Count a night while its solar day starts before the forecast's end

`reach_end` is the last hour in `conditions.hours(TIMELINE_VARIABLES)` plus one
hour, or none when that is empty. Keep chaining days while
`day_start < reach_end`, and stop at `MAX_LATER_NIGHTS = 3`. With no
`reach_end`, the list is empty. The constant lives in the core, and the
delivery imports it to size the Night sensors, so the two cannot drift.

### DD4. One entry model, reused window model

Add `LaterNight(BaseModel)` to `model.py`, with `extra="forbid"` and one field,
`dark_window: DarkWindow`. Add `later_nights: list[LaterNight]` to
`VerdictDocument` after `observation`, defaulting to an empty list. #319 adds
`moon` and `targets` to `LaterNight`.

### DD5. Night sensors follow the rank-sensor pattern

In `mqtt.py`:

- `NIGHTS = range(2, MAX_LATER_NIGHTS + 2)`, giving Night 2 to Night 4.
- Topics `<base>/<pier>/night_<n>/state` and `.../attributes`; discovery
  object id `night_<n>`; unique id `pierpressure_<pier>_night_<n>`; name
  `Night <n>`; `device_class: timestamp`; icon `mdi:weather-night`.
- Availability as the rank sensors: the last-will topic and a template on the
  attributes' `available` flag, with `availability_mode: all`.
- State: the entry's `dark_window.start` through the existing `_iso()` helper
  (`+00:00` offset, whole seconds), or the literal `None` for a null start or
  a missing entry. `None` is what the timeline and health sensors already use
  for unknown.
- Attributes: `{"available": true, "night": n, **entry}`, or
  `{"available": false, "night": n}`.
- In `publish_verdict`, exclude `{"timeline", "later_nights"}` from the
  attributes payload, and publish the three Night sensors (discovery, state,
  attributes) after the timeline sensors and before the narrative.

### DD6. The card reads the Night sensors and tags each line with its night

In `strip.ts`, `buildStrip` reads `sensor.pierpressure_<slug>_night_<n>` for
n = 2 to 4 with `pierEntityId`, skips a sensor that is missing or
`unavailable`, and passes its `dark_window` attribute through `darkWindow()`.
Each readable window adds lines through `nightLines()`, whatever happened to
the Verdict sensor's window.

`Line` gains `night: number`: 1 for the selected night, 2 to 4 for later
nights, and none for the now line. `tipKey.line` becomes
`line:<kind>:<night>` for dusk and dawn, and stays `line:now` for the now
line, so a tap box keeps the right line when two dusk lines share an axis on a
long polar night. Rendering does not change: `data-line` stays the kind, so
existing tests and styles keep working. The harness gains a helper that
returns every line of a kind.

### DD7. One decision record

How the document and delivery carry later nights is a frozen-contract choice
that #319 builds on: a list of per-night entries in the document, left out of
the Verdict attributes, and one Night sensor per slot. The ADR step records it.

## Risks / Trade-offs

- [Risk] Near the edges of polar night, `dark_window` can return null or a
  window longer than a day, because its search looks only 24 hours back and 48
  hours forward. → Later nights inherit the same behaviour as tonight, by
  design. The card already ignores windows over 48 hours. No new rule is
  invented here.
- [Risk] Three more `dark_window` and solar-day searches per recompute. →
  Measured at about 0.14 s for three nights on the dev machine, small beside
  the provider fetches each recompute already makes.
- [Risk] The golden documents change. → Regenerate them once, in the same
  commit as the producer change, and check that the diff adds only
  `later_nights`.
- [Trade-off] In continuous polar night, one night's dawn and the next night's
  dusk fall at the same instant, so their lines and labels are drawn on top of
  each other, and hover or tap reaches only the line drawn last. → Accepted:
  it happens only above about 84.5° latitude in polar night, and both lines
  name the same time. The card does not merge or offset them.
- [Trade-off] A later night with no darkness shows unknown rather than
  unavailable, so a user can tell "no darkness" from "beyond the forecast"
  (D7). Home Assistant cannot show both a state and a reason, so the
  `dark_window` attributes carry the null bounds.

## Migration & Rollback

No data migration. Home Assistant creates the three Night sensors from
retained discovery on the first publish. To roll back, deploy the earlier
image: the Verdict attributes go back to their earlier form, and the retained
Night sensor discovery stays behind until a user deletes the entities or
clears the retained discovery topics, as the README's entity-removal note
describes.
