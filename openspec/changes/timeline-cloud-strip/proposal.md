## Why

PierPressure already fetches hourly cloud, wind, seeing and transparency and computes the dark window and the moon, but publishes only the verdict and its summary fields. None of the hourly series reaches Home Assistant, so no card can draw the night as a strip. This story is the walking skeleton of epic #130. It carries the hourly readings through the document, the MQTT adapter and one chart card in a single pass. Every later story then adds variables or cards to a path that already works.

## What Changes

- The verdict document gains an additive `timeline` field: one entry per clock hour across the union of the hours both providers returned, sorted ascending (D4). Each entry is flat: `time`, `sun_altitude`, `moon_altitude`, `cloud_cover`, `cloud_low`, `cloud_mid`, `cloud_high`, `wind_gust`, `seeing`, `transparency`, with null where a source lacks the hour (D1).
- The core computes sun and moon altitude per hour from the pinned ephemeris, rounded like the other emitted angles, so the document stays byte-identical (D1).
- The timeline fills whenever a provider returned rows, dark window or not. It is evidence beside the verdict and carries no verdict of its own; ADR 0023 stands (D5, D8).
- The Verdict entity's attributes exclude the timeline, so they stay under the recorder's 16 KiB limit. Every existing attribute key stays. After this change no MQTT topic carries the whole timeline; Home Assistant sees it per variable, which #134 completes (D3).
- A new ordinary **Cloud cover** sensor on the pier's device. Its state is the cloud cover for the hour containing `generated_at`. Its attributes hold `hour` (the hour the state belongs to) and a `forecast` array of `{datetime, value}` with one entry per timeline hour, null where the hour has no value. When the current hour is missing or null its state is unknown, and it stays available so the forecast still reaches charts (D2, D6).
- A new ADR records the timeline's shape, its evidence-not-verdict rule, the attribute exclusion and the per-variable delivery consequence (D8).
- A short docs page with one apexcharts-card example reading the `forecast` array, plus README rows for the new sensor and the attribute change (D7).
- The golden fixtures are regenerated once, additively (D9).

No existing field, topic, entity or mapping changes meaning. Nothing is breaking.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `night-verdict`: the document carries a `timeline` with the shape, coverage, ordering, null and precision rules above, computed offline and deterministically.
- `ha-delivery`: a Cloud cover sensor is published per pier with the state, `forecast` attribute and availability rules above; the verdict entity's attributes exclude the timeline while keeping every existing key.

## Impact

- `pierpressure/core/model.py`: a timeline entry model and the `timeline` field on `VerdictDocument`, with 2 dp rounding for seeing and transparency.
- `pierpressure/core/sky.py`: per-hour sun and moon altitude from the existing observer and ephemeris.
- `pierpressure/core/producer.py`: builds the timeline from the union of both groups' hours.
- `pierpressure/delivery/mqtt.py`: the Cloud cover discovery, state and attributes, published on every verdict publish; the verdict attributes payload without the timeline. `pierpressure/delivery/ha_schema.py` gains the unit key.
- `tests/`: new tests for the timeline, the per-hour altitudes, the sensor and the attribute exclusion; golden fixtures regenerated; the existing determinism and boundary tests keep passing.
- `docs/decisions/`: one new ADR. `docs/`: one new page. `README.md`: the entity table and the verdict document section.
- No new dependencies. No network at runtime. The astronomy per hour adds a few dozen Skyfield altitude evaluations per recompute.
