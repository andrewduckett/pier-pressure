## Context

`evaluate` in `pierpressure/core/scoring.py` builds every reason line. The
scored verdict path ends with the cap lines, then the agreement line, then
returns. `Conditions.value_at` reads one variable for one hour slot, and
`hour_slots` tiles the scored window from the top of the hour. `temperature`
and `dew_point` already travel as variables and sit on the timeline; nothing in
the core reads them yet, and the conditions module's docstring says so.

`PierConfig` holds the two tuning knobs. `max_gust` is `float | None` with
`gt=0`, opt-in. The add-on form schema names only `go_threshold` and
`max_gust`; `addon_options.pier_settings` passes any other pier key from the
add-on's `config.yaml` through to the core unchanged.

The golden suite drives recorded Open-Meteo and 7Timer! payloads through the
provider layer at a pinned instant. The recorded Open-Meteo payload has no
temperature or dew point, so no existing golden sees the new line.

## Goals / Non-Goals

**Goals:**
- One pure function decides the line from the scored window, the conditions
  and the margin, so it is unit-tested without a full verdict.
- The line is appended last on the gate-passing paths and nowhere else.
- Existing reasons, goldens and tests keep their content and order.

**Non-Goals:**
- A timeline variable for the spread, a confidence term, or a score term.
- An add-on form field or schema line (#99).
- Local time in the line (no pier timezone exists).

## Test Seams

- **Primary test seam:** `evaluate` in `tests/test_scoring.py`, through the
  existing `_window`, `make_conditions` and `Series` helpers, asserting on
  `decision.reasons`.
- **Existing seams reused:** `PierConfig` and `load_config` in
  `tests/test_config.py` for the setting; `tests/test_golden_verdict.py`
  for two new stub-based cases through the provider layer.

## Scrutiny Tier & Blast Radius

- **Tier:** low
- **Blast radius:** `pierpressure/core/scoring.py` (one new reason),
  `pierpressure/core/config.py` (one new field), docs. No document field, MQTT
  entity or provider changes.

## Decisions

**D1. One pure function, `dew_reason(window, conditions, margin) -> str | None`.**
It walks `hour_slots(*window)`, reads `temperature` and `dew_point` through
`value_at`, skips an hour missing either, and returns the line for the first
hour whose spread is strictly under the margin, or `None`. A margin of 0 returns
`None` before the walk. Alternative: fold the walk into `_score_reasons`.
Rejected: the dew line is not a score term and must also follow the cap and
agreement lines, which `_score_reasons` does not emit.

**D2. Appended in `evaluate` on every gate-passing path, after `agreed`.**
Both the scored path and the missing-cloud `MAYBE` (score 0) gain
`reasons.extend(dew)` after `reasons.extend(agreed)`. Each is a verdict whose
gates passed and whose score is non-null, which is the brainstorm's rule (D2).
The missing-cloud path still has the weather rows, and the advice holds.
The gated `NO-GO` paths and the empty-window `MAYBE` get nothing: the former
by decision, the latter because it tiles no hour. Alternative: add the line to
every path with a scored window. Rejected by the brainstorm (D2).

**D3. `dew_margin: float = Field(default=4.0, ge=0.0, allow_inf_nan=False)` on `PierConfig`.**
Opt-out with a default, where `max_gust` is opt-in with `None`, because the
data is in every forecast. Zero is the off switch, so `ge` not `gt`. `.inf`
would make every hour qualify, so it is refused. The field sits beside the
other two knobs with a comment naming it the third.
Alternative: `float | None` like `max_gust`. Rejected: it would make the
common case a configuration step.

**D4. Time rendered with `iso_z`, the slot start.** Same string as the span
line. A boundary hour that starts before the scored window still names its
slot start, because that is the hour the forecast row describes.

**D5. Frost decided by the first qualifying hour's own temperature, `<= 0.0`.**
Brainstorm D4. No second line for a later frost.

**D6. Two new golden cases built from stubs, `dew_night` and `frost_night`.**
Each takes `_base_full()` and adds `temperature` and `dew_point` to every
reading so the spread closes from a chosen hour: at 22:00 UTC above freezing
for dew, at 00:00 UTC at −1 °C for frost. They go in `_CASES`, so the goldens
are written with `PP_WRITE_GOLDENS=1`. Existing goldens are untouched.

**D7. The agreement test keeps its tail check and gains a sibling.**
`test_a_scored_verdict_ends_its_reasons_with_the_agreement` stays as it is:
with no weather rows there is no dew line, so the agreement line is still
last. A new test with weather rows asserts the tail `Score`, `Cloud agreement`,
`Dew likely from`, and another asserts a wind-capped `MAYBE` puts the dew line
after the cap line and the agreement line.

**D8. Docs.** README gains a `dew_margin` row and example line beside
`max_gust`. The add-on DOCS note that `dew_margin` is set in the add-on's
`config.yaml`, since the tab has no field for it. The conditions docstring
line that says no term reads the weather variables narrows to the score,
gates and confidence.

## Risks / Trade-offs

- [A provider's dew point unit differs from °C] → Every provider normalises
  temperature and dew point to °C in `SourceReading`, whichever provider
  fills each. No new unit handling.
- [Temperature and dew point fill from different providers] → Neither is in
  a bundle, so each fills independently and the spread can mix two models,
  or go negative. Accepted: the line is advice, not a gate, a negative spread
  is simply under the margin, and the fill order is the pier's choice.
- [Golden churn] → None: no existing fixture carries the variables.

## Migration & Rollback

N/A. The field has a default, so existing `config.yaml` files load unchanged.
