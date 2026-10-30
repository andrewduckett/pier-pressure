## 1. Document contract

- [ ] 1.1 [easy] A `VerdictDocument` carries a `timeline` list of `TimelineEntry` values, empty by default and last in key order, where each entry has the ten keys in the spec's order, `time` as an aware UTC whole-second timestamp, altitudes rounded to 3 dp, seeing and transparency rounded to 2 dp, cloud and gust passed through unchanged, and a serialize-then-read-back round trip leaves every entry equal (verify: `uv run pytest tests/test_model.py -k timeline`)
- [ ] 1.2 [medium] `sky.altitudes_at(pier, times)` returns `[]` for no times without calling Skyfield, returns one `(sun, moon)` pair per hour that matches `_altitude_deg` at 3 dp, and reads at or below -18.0 after rounding for every hour inside the dark window (verify: `uv run pytest tests/test_sky_timeline.py`)
- [ ] 1.3 [medium] `produce_verdict` fills `timeline` with the sorted union of both groups' hours, null for the fields of a source that lacks the hour, an empty list for `Conditions(None, None)`, a full list without a dark window whose document minus `timeline` equals the empty-conditions document, and no change to any other field when hours outside the dark window are added; the docstring stops saying conditions are not consulted without a dark window (verify: `uv run pytest tests/test_producer_timeline.py`)
- [ ] 1.4 [easy] The golden fixtures are regenerated with `PP_WRITE_GOLDENS=1` in their own commit whose diff adds only a `timeline` key to each file, and the golden and determinism suites pass against them (verify: `uv run pytest tests/test_golden_verdict.py tests/test_determinism.py`)

## 2. Delivery [depends-on: 1]

- [ ] 2.1 [easy] `publish_verdict` publishes the document without `timeline` to the verdict attributes topic, byte-identical to `to_json()` with that key removed and to today's payload for an empty timeline, with `make_document` gaining a `timeline` parameter and the existing-entities pin in `tests/test_rank_targets.py` keeping its exact list by expecting the excluded form and filtering the Cloud cover topics (verify: `uv run pytest tests/test_publish.py tests/test_rank_targets.py`)
- [ ] 2.2 [medium] Every publish sends a retained Cloud cover discovery config on the pier's device, named `Cloud cover`, enabled by default, with `unit_of_measurement` `%`, a unique id and topics derived from the pier id, a two-entry availability list keyed on `value_json.available`, validating against `SENSOR_SCHEMA` extended with the unit key, and a republish introduces no new identity (verify: `uv run pytest tests/test_cloud_cover.py -k discovery`)
- [ ] 2.3 [medium] Every publish sends the Cloud cover state as the current hour's `cloud_cover` serialized as the document emits it, or `""`, and retained attributes `{available, hour, forecast}` where `forecast` mirrors the timeline entry for entry with nulls kept, `hour` is the matched entry's `time` or null, `available` is true exactly when `hour` is set, a later publish replaces the array, and 120 entries stay under 16 KiB (verify: `uv run pytest tests/test_cloud_cover.py`)

## 3. Documentation [depends-on: 2]

- [ ] 3.1 [parallel] [easy] `docs/night-timeline.md` explains the timeline, the Cloud cover sensor's `forecast` and `hour` attributes, that the state can lag by one recompute interval, why the Verdict attributes leave the timeline out, a recorder exclusion note, and one apexcharts-card example reading `forecast`, guarded by a `tests/test_docs.py` style test (verify: `uv run pytest tests/test_timeline_docs.py -k page`)
- [ ] 3.2 [parallel] [easy] `README.md` gains the Cloud cover row in the entity table, the two Cloud cover topics, the `verdict/attributes` topic relabelled as the document without `timeline`, the `timeline` row in the verdict document table and the sentence that the Verdict attributes exclude it, guarded by the same test module (verify: `uv run pytest tests/test_timeline_docs.py -k readme`)

## 4. Integration [depends-on: 3]

- [ ] 4.1 [easy] The whole gate is green: lint, strict types and the full suite including the core boundary and offline guards (verify: `mise run check`)

## Deviations Ledger

<!-- Dated notes on small departures from the plan, written during apply. Stop and ask the user about a large one. -->
