<!-- One task is one behavior, its test, and the code that passes it. -->

## 1. Alternates through the seam

- [x] 1.1 [easy] `Conditions` carries `alternates` per variable, default empty, and `readings_at(variable, time)` returns the values present for an hour, filled first then alternates in order; `hours()` still spans the filled series only (verify: `uv run pytest tests/test_conditions_model.py`) (✓ `uv run pytest tests/test_conditions_model.py` passed, 12 tests)
- [x] 1.2 [medium] `assemble_snapshot` keeps, for each variable, the series of every provider after the filling one that declares it and returned its bundle, in order; a blank column, a failed fetch and a losing bundle behave as the conditions delta's scenarios say, and the filled series is unchanged (verify: `uv run pytest tests/test_conditions_provider.py`) (✓ `uv run pytest tests/test_conditions_provider.py` passed, 69 tests)

## 2. The measure, the factor and the line [depends-on: 1]

- [ ] 2.1 [medium] `cloud_agreement(window, conditions)` returns the clarity-weighted mean gap over the scored window, weighting each counted hour by coverage times the clarity of its lowest reading, 0 when every weight is zero, `None` when no hour has two readings; `providers` lists only providers with a value in a counted hour (verify: `uv run pytest tests/test_scoring.py -k agreement`)
- [ ] 2.2 [easy] The band is decided on the rounded spread with `AGREE_MAX_GAP = 15` and `MIXED_MAX_GAP = 35`, justified beside the other tuning constants (verify: `uv run pytest tests/test_scoring.py -k band`)
- [ ] 2.3 [medium] `confidence` multiplies by `_A_MIXED = 0.90` or `_A_DISAGREE = 0.67`, clamped so a value at or above `_BAND_MEDIUM` before the factor stays at or above it; an alternate's issue time changes nothing (verify: `uv run pytest tests/test_scoring.py -k confidence`)
- [ ] 2.4 [medium] `evaluate` computes agreement once after the no-dark-window and no-dark-time returns, carries it on `Decision`, and appends the `Cloud agreement ...` line after the gate or score lines on the wind gate, overcast gate and scored paths, with ` Confidence lowered.` for mixed and disagree (verify: `uv run pytest tests/test_scoring.py -k reason`)

## 3. The document [depends-on: 1]

- [ ] 3.1 [parallel] [easy] `VerdictDocument.agreement: dict[str, Agreement]` is declared after `timeline` with `AgreementBand`, `spread` and `providers`, and `TimelineEntry` gains `cloud_cover_min` and `cloud_cover_max` as its last two keys, both round-tripping through JSON (verify: `uv run pytest tests/test_model.py -k "agreement or cloud_cover_min"`)

## 4. Producer and goldens [depends-on: 2, 3]

- [ ] 4.1 [medium] `produce_verdict` fills `agreement` from the decision, empty when none, and each timeline entry's `cloud_cover_min` and `cloud_cover_max` from `readings_at`, null for an hour fewer than two providers cover; hours only an alternate covers add no entry (verify: `uv run pytest tests/test_producer.py tests/test_producer_timeline.py`)
- [ ] 4.2 [easy] Regenerate the existing golden documents once and confirm the diff touches only the new keys (verify: `uv run pytest tests/test_golden_verdict.py`)
- [ ] 4.3 [medium] Add the `two_cloud_providers` golden case, feeding the recorded Open-Meteo payload as `open_meteo` and a shifted copy as `open_meteo_hrrr`, pinning the alternate, the agreement object, the reason line, the confidence factor and the timeline band in one document (verify: `uv run pytest tests/test_golden_verdict.py -k two_cloud_providers`)
- [ ] 4.4 [easy] The whole suite, lint and types pass, and the core boundary test still holds (verify: `mise run check`)

## Deviations Ledger

- 1.1: `readings_at` returns `(provider, value)` pairs, not bare values, so the agreement measure (2.1) can list the providers that gave a value in a counted hour without walking the series a second time.
