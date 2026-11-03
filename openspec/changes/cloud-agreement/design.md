## Context

`assemble_snapshot` in `pierpressure/conditions/provider.py` walks the fixed `Variable` order and the configured provider order, fills each variable or bundle from the first provider that returned it, and discards the rest. The core's `Conditions` holds `series: Mapping[Variable, Series]` and answers `value_at`, `issued_at` and `hours()`. `scoring.py` builds every clarity-weighted quantity on `hour_slots`, `coverage_weight` and `clarity_weight`, and `confidence()` is `max(floor, L·F)·K`, with every tuning constant at the top of the module. `evaluate()` returns a `Decision` whose reasons the producer extends with equipment notes. `VerdictDocument` and `TimelineEntry` are Pydantic models with `extra="forbid"` and a fixed key order; `timeline` is last. The MQTT adapter publishes the document minus `timeline` as the Verdict entity's attributes, and one sensor per row of `TIMELINE_SENSORS`. The golden suite drives recorded payloads through `assemble_snapshot` into `produce_verdict` and pins the whole document byte for byte.

Constraints: the core stays pure and deterministic; the document grows additively only; the delivery surface does not change; the glossary's Alternate and Agreement definitions hold.

## Goals / Non-Goals

**Goals:**
- Carry alternates through the existing seam without changing the fill or any existing field.
- Compute agreement with the same clarity and coverage machinery the score uses, so it stays one concept.
- Keep every new tuning constant beside the others, with its justification.
- Pin the new behaviour in the golden suite with a two-provider case.

**Non-Goals:**
- Agreement on any variable but cloud cover. The object is keyed by variable so gusts can follow without a reshape.
- Any new MQTT entity, topic or dashboard card.
- Blending or averaging alternates into the filled series.

## Test Seams

- **Primary test seam:** the golden suite, `tests/test_golden_verdict.py`: `assemble_snapshot(fills)` into `produce_verdict` at the pinned instant, asserted byte-identical. A new case with a second cloud provider pins alternates, the agreement object, the reason line, the confidence factor and the timeline band in one document.
- **Existing seams reused:** `tests/test_conditions_provider.py` for the fill and alternates; the scoring tests for the measure, the bands, the factor and the reason line against hand-built `Conditions`; the producer and model tests for the document's shape and key order.

## Scrutiny Tier & Blast Radius

- **Tier:** medium
- **Blast radius:** `pierpressure/core/conditions.py`, `pierpressure/conditions/provider.py`, `pierpressure/core/scoring.py`, `pierpressure/core/model.py`, `pierpressure/core/producer.py`; every golden expected document; the Verdict entity's attributes payload gains one key. No configuration, topic or entity changes.

## Decisions

### DD1. Alternates are a second mapping on `Conditions`

`Conditions` gains `alternates: Mapping[Variable, tuple[Series, ...]]`, default empty, in configured order. `series`, `value_at`, `issued_at` and `hours()` keep their meaning: `hours()` still spans the filled series only, so an alternate never adds a timeline entry (a sixteen-day GFS alternate would otherwise balloon every timeline sensor's `forecast` attribute). A new reader, `readings_at(variable, time)`, returns the values present for that hour across the filled series and its alternates, filled first. Alternative: a list of `Series` per variable with the winner first. Rejected: every existing call site reads one series, and a tuple's head would have to be special-cased everywhere.

### DD2. The fill keeps walking after it fills

`assemble_snapshot` fills exactly as today, then for each variable collects, from every provider after the one that filled it, the series of each provider that declares the variable and returned its bundle. Alternates are decided per variable, not per bundle: a losing bundle yields one alternate per member, and a member the earlier provider carries with no values still has its alternate. Alternative: a second pass over `fills` after the fill. Chosen: one loop, so the rule that decides "returned" is written once.

### DD3. The measure lives in `scoring.py` beside the clarity curve

`cloud_agreement(window, conditions) -> AgreementTerm | None` walks `hour_slots` over the scored window. For each slot it takes `readings_at("cloud_cover", slot)`; with two or more values it records `gap = max - min` and `weight = coverage_weight · clarity_weight(min)`. The result is `Σ(weight·gap) / Σ(weight)`, 0 when the denominator is 0, and `None` when no slot had two readings, which is also the case when no provider shares an hour with another. `providers` lists only providers that gave a value for a counted slot. Three constants: `AGREE_MAX_GAP = 15`, `MIXED_MAX_GAP = 35`, with the justification that 15 points is within one model's hour-to-hour noise and 35 spans almost half the 10–90 clarity ramp. `spread` is `round(mean)` and the band is decided on that integer, so the line a reader sees and the band always agree. Weighting by the lowest reading is the user's decision (brainstorm D2): the hours any forecast calls usable are the hours the night turns on.

### DD4. Confidence multiplies by an agreement factor

`confidence()` becomes `max(floor, L·F)·K·A`, where `A` is `_A_MIXED = 0.90` or `_A_DISAGREE = 0.67` and 1 otherwise, then clamped: when the value before `A` is at or above `_BAND_MEDIUM`, the value after it is at least `_BAND_MEDIUM`. That clamp is the "never to LOW on its own" guarantee; without it a complete forecast a day out (`L·F` at the 0.5 floor) would read 34 and LOW. A value already below `_BAND_MEDIUM` is multiplied without a clamp. `evaluate()` computes the agreement once, after the no-dark-window and no-dark-time returns and before confidence, and carries it on `Decision` (default `None`, set on every later path) so the producer can emit it. The factor is applied after the floor, like `K`, so the floor cannot rescue a disagreeing night. This widening of confidence's inputs is the decision recorded in the ADR step.

### DD5. The reason line is the decision's last line

`evaluate()` appends the agreement line after the gate reason or the `Score N/100.` line, on the wind gate, the overcast gate and the scored path alike, and before the producer's equipment notes. The no-dark-window and no-dark-time paths return before the measure runs, whatever the snapshot holds, so their agreement is empty and they add no line. The cloud-missing path has no filled cloud series, so it has no alternates either. Wording is pinned in the spec.

### DD6. The document gains `agreement` last, and the entry gains two keys last

`VerdictDocument.agreement: dict[str, Agreement]`, where `Agreement` has `band: AgreementBand` (a `StrEnum` of `AGREE`, `MIXED`, `DISAGREE`), `spread: int` and `providers: list[str]`. It is declared after `timeline`, so every key keeps its position in both the document and the attributes payload. `TimelineEntry` gains `cloud_cover_min` and `cloud_cover_max` after `precipitation_probability`; the producer fills them from `readings_at` with the same two-reading rule. Alternative: a nullable flat object. Rejected in the brainstorm (D4): a keyed object lets gusts follow additively.

### DD7. Goldens regenerate once, plus one new case

Every expected document changes because `agreement` and the two entry keys are always present. The goldens are regenerated once, in the task that adds the keys, and reviewed as a diff that touches only the new keys. A new case, `two_cloud_providers`, feeds the recorded Open-Meteo payload as `open_meteo` and a shifted copy as `open_meteo_hrrr`, so the fill, the alternate, the measure, the factor, the line and the band are pinned together.

## Risks / Trade-offs

- [Golden churn hides a real regression in the first regeneration] → Regenerate in its own commit after the key-adding task, with the diff reviewed for new keys only; the two-provider case lands in a later commit.
- [`round()` on a `.5` mean rounds to even, which could surprise a reader] → Document it beside `spread`. The band is decided on the rounded spread, so the line and the band can never disagree, and a tie moves both together.
- [Weighting by the lowest reading rewards an outlier optimistic model] → That is the intent: an optimistic voice is the one that would have sent Andrew out. Recorded in the brainstorm and the ADR.
- [Alternates grow memory for long forecasts] → Alternates hold the same hourly dict a filled series does; a handful of models at hourly resolution for a few days is a few thousand floats.
- [The attributes payload grows by one small object] → A few dozen bytes; far from the 16 KiB recorder limit the timeline exclusion protects.

## Migration & Rollback

N/A. No configuration, topic or entity changes. A reader that ignores unknown keys sees the same document as before.
