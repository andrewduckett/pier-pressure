## Context

- `confidence()` in `pierpressure/core/scoring.py` computes
  `max(floor, 100·L·F)·K`, then multiplies by the agreement factor `A` and
  clamps at the MEDIUM threshold when the value before `A` was MEDIUM or more.
- `evaluate()` calls `confidence()` once and threads the result through every
  path. The paths for no dark window, no dark time and no cloud data set
  confidence to fixed values and skip `confidence()`.
- `produce_verdict()` in `pierpressure/core/producer.py` drops an observation
  that is not `usable` at the instant, calls `evaluate()` without it, then
  appends the observation line after the decision's reasons and before the
  equipment notes.
- `Observation` in `pierpressure/core/observation.py` keeps each layer's cover
  code and base. The cloud bundle fills `cloud_cover`, `cloud_low`, `cloud_mid`
  and `cloud_high` from one provider, so `conditions.value_at` gives the filled
  low and mid values for an hour.
- ADR-0037: the observation is an input beside the snapshot. It never fills a
  variable.

## Goals / Non-Goals

**Goals:**

- One new multiplicative factor in `confidence()`, computed from data the core
  already holds.
- The factor and its reason line come from one measurement, as agreement's do.

**Non-Goals:**

- No change to the agreement measure, the gates, the score or the timeline.
- No new field in the verdict document, and no change to delivery, the card or
  the narrative.
- No comparison with any hour other than the one that holds the instant, and
  none with alternates.

## Test Seams

- **Primary test seam:** `produce_verdict` with a pinned clock, a snapshot and
  an `Observation`, asserting `confidence` and `reasons`. It proves the factor,
  the clamp, the line and its place in one call.
- **Existing seams reused:** `tests/test_producer.py` (agreement confidence and
  reason tests show the pattern), `tests/test_observation.py` for the observed
  cloud of a report, and `tests/test_scoring.py` for the factor's bands.

## Scrutiny Tier & Blast Radius

- **Tier:** low
- **Blast radius:** `pierpressure/core/` only: `observation.py`, `scoring.py`
  and `producer.py`. Confidence values change only for piers with a usable
  observation; golden documents carry `observation: null` and stay unchanged.

## Decisions

### DD1. The observed cloud is a function in `observation.py`

`observed_cloud(observation) -> int` returns the spec's points: the largest of
`FEW` 12, `SCT` 37, `BKN` 62, `OVC`, `OVX` and `VV` 100 over layers with a known
base at most `CLEAR_BELOW_FT`, else 0. It sits beside `COVER_WORDS` and
`CLEAR_BELOW_FT`, because it reads the report's own codes.

*Alternative:* compute it in `scoring.py`. Rejected: scoring would learn METAR
cover codes, which `observation.py` already owns.

The points are the okta lower bound rounded down (1/8, 3/8, 5/8 of 100), so the
value never claims more cloud than the code proves (brainstorm D5). Whole
points keep the reason line's numbers subtracting exactly.

### DD2. An `ObservedTerm` mirrors `AgreementTerm`

A frozen `ObservedTerm(station, observed, forecast)` in `scoring.py`, with a
`gap` property (`observed − forecast`) and a `factor` property. `forecast` is
the combined low and mid cloud, rounded with `round()` as `AgreementTerm.spread`
is. `observed_term(instant, conditions, observation) -> ObservedTerm | None`
reads the slot `instant` floored to the hour, returns `None` without an
observation or without both `cloud_low` and `cloud_mid` values there.

The factor reuses `AGREE_MAX_GAP`, `MIXED_MAX_GAP`, `_A_MIXED` and
`_A_DISAGREE`: under 15 is 1, 15 to 35 is `_A_MIXED`, above 35 is
`_A_DISAGREE` (brainstorm D7). A negative gap is under 15, so less cloud is
always 1 (D4).

*Alternative:* new constants of its own. Rejected for now: the same band
reasoning (one model's hour-to-hour noise, half the clarity ramp) holds for a
report against a forecast, and one set of numbers is easier to tune. A comment
names the reuse, so a later change can split them.

### DD3. The low and mid cloud combine as independent layers

`low + mid − low·mid/100`. The larger plausible combination of the two
layers is the cautious one: the factor only lowers when the report exceeds the
forecast, so a higher forecast flags fewer false contradictions. Part of the mid
layer sits above what a station sees, which makes this the generous side too.

*Alternatives:* `max(low, mid)` flags more contradictions where both layers
are thin; `low` alone ignores mid cloud the station can see. Both rejected.

### DD4. `confidence()` takes the term and multiplies after agreement

`confidence(..., agreement=None, observed=None)`:
`value = round(raw · A · O)`, then the existing clamp, unchanged, so the clamp
covers the product (brainstorm D8). The default `None` keeps every existing
call and test as it is.

### DD5. `evaluate()` takes the observation; the producer places the line

`evaluate(..., observation=None)` measures the term once beside the agreement,
passes it to `confidence()` and stores it in a new `Decision.observed` field
only when its factor is below 1, so the field is exactly "the line is due". The
three fixed-confidence paths never measure it (D9).

The producer builds the line with `_observed_reason(term)` and appends it right
after the observation line (D11). The line needs the observation line before
it, and only the producer knows both. The producer already drops an unusable
observation before `evaluate()`, so `evaluate()` never sees a stale one.

*Alternative:* put the line in `evaluate()`'s reasons. Rejected: it would come
before the observation line.

### DD6. The line's wording

`Observed cloud above this hour's forecast: <station> reported at least <obs>%,
the forecast gave <fc>% low and mid cloud, a gap of <gap> points. Confidence
lowered.` It follows the agreement line's shape: what was compared, the
numbers, and the same closing sentence (D10). "At least" carries D5's lower
bound.

### DD7. Docs

The README's `metar_station` row says the observation lowers confidence when
the report shows more cloud than this hour's forecast. Its `confidence` row
adds "and falls when the forecasts disagree or the airport reports more cloud
than forecast". `produce_verdict`'s docstring drops "changes no confidence".

## Risks / Trade-offs

- [The airport's sky differs from the pier's] → the factor never takes a
  MEDIUM verdict to LOW, and the README tells users to choose a close station.
- [A shower or a passing layer makes one report unrepresentative] → only the
  current hour is compared, so the next recompute with a new report corrects it.
- [Reused agreement constants hide that the two may need different tuning] → a
  comment marks the reuse, and the numbers are fixed in one place.

## Migration & Rollback

N/A. No data or document shape changes. Rolling back the commits restores the
previous confidence values.
