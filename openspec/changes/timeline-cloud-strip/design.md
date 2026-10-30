## Context

- `VerdictDocument` in `pierpressure/core/model.py` is a Pydantic model whose field order is the frozen key order. Angles use the `Degrees` type (3 dp at validation); `moon.illumination` uses a 2 dp type; timestamps are aware UTC at whole seconds and serialize through `iso_z`.
- `produce_verdict` in `pierpressure/core/producer.py` is a pure function of `(pier, clock, conditions)`. `Conditions` holds one optional group per source, each with `hours` keyed by top of hour and an O(1) `at()` lookup.
- `pierpressure/core/sky.py` already owns the observer, the ephemeris and `_altitude_deg(pier, target, when)`, evaluated one instant at a time.
- `MqttDelivery.publish_verdict` in `pierpressure/delivery/mqtt.py` publishes `document.to_json()` to the verdict attributes topic, and the Score sensor reads `value_json.score` from that same topic. The rank sensors are the pattern for an additive entity: a two-entry availability list keyed on an `available` flag in the attributes payload, republished on every publish.
- `ha_schema.SENSOR_SCHEMA` is permissive about extra keys but lists the keys we emit.
- Golden fixtures under `tests/fixtures/golden/expected/` pin whole documents byte for byte and regenerate with `PP_WRITE_GOLDENS=1`.
- The service fetches conditions on every recompute, dark window or not.

## Goals / Non-Goals

**Goals:**

- Add the timeline as the last field of the document without touching any existing field's value or position.
- Compute all per-hour altitudes in the core, offline, with the existing observer and ephemeris.
- Deliver one Cloud cover sensor using the existing separate-entity pattern, and keep the verdict attributes payload a strict subset of the document.
- Keep one test seam per layer, reusing the fixtures and fakes that exist.

**Non-Goals:**

- Sensors for the other timeline variables (#134), new Open-Meteo variables (#136), the dashboard (#135), the Markdown strip (#137).
- A whole-timeline MQTT topic (brainstorm D3).
- Any change to the scoring, gates, confidence or ranking.

## Test Seams

- **Primary test seam:** `produce_verdict` driven with `make_conditions` and the golden raw payloads at a pinned instant (`tests/test_producer.py`, `tests/test_golden_verdict.py`). It proves the timeline's coverage, order, nulls, precision and determinism from outside the core.
- **Existing seams reused:** `MqttDelivery` with `FakeMqttClient` and `make_document` (`tests/test_publish.py`, `tests/test_rank_targets.py` pattern) for discovery, state, attributes and availability; `tests/test_sky_moon.py` style unit tests for the per-hour altitudes; `tests/test_docs.py` style guard for the new docs page; `tests/test_core_boundary.py` and `tests/test_determinism.py` unchanged.

## Scrutiny Tier & Blast Radius

- **Tier:** medium
- **Blast radius:** `pierpressure/core/model.py`, `producer.py`, `sky.py`; `pierpressure/delivery/mqtt.py`, `ha_schema.py`; every golden fixture; `README.md` and one new docs page. The frozen contract grows by one field and one entity. No config, no settings, no persistence, no new dependency.

## Decisions

### D1. `TimelineEntry` model, appended as the document's last field

Add `TimelineEntry` to `model.py` with `extra="forbid"` and the keys from the spec in that order. `sun_altitude` and `moon_altitude` are `Degrees`. `seeing` and `transparency` get a new `Quality` type, `float` with an `AfterValidator` rounding to 2 dp, like `IlluminatedFraction` but without the 0 to 1 bound enforced beyond what the provider layer already guarantees. `time` carries the same aware-UTC whole-second validator and `iso_z` serializer as the other timestamps. `VerdictDocument.timeline: list[TimelineEntry] = Field(default_factory=list)` goes after `moon`, so every existing key keeps its position and a document without a timeline still validates.

Alternatives: a `TypedDict` or plain dict (loses the validation-time rounding that keeps the in-memory and JSON forms equal); reusing `BaseHour` and `SecondaryHour` as nested objects (ties the contract to the core's internal grouping, which brainstorm D1 rejected).

### D2. Per-hour altitudes in `sky.py` as one vectorised evaluation

Add `altitudes_at(pier, times) -> list[tuple[float, float]]` to `sky.py`: build one Skyfield `Time` array from the sorted hours with `ts.from_datetimes`, observe the sun and the moon once each through the existing `_observer`, and return `(sun_altitude, moon_altitude)` per hour. Geometric centre altitude, apparent place, no refraction, matching `_altitude_deg`. Rounding happens in the model, not here.

Alternatives: calling `_altitude_deg` 72 times for each body (correct, but about 150 single-instant Skyfield evaluations per recompute per pier; the vector call is the same arithmetic in one pass). Computing altitudes in the producer (would spread astronomy outside `sky.py`).

### D3. The producer builds the union of hours

In `produce_verdict`, after the existing calls: collect `{h.time for h in conditions.base.hours}` and the same for `secondary`, guarding `None` groups; sort; look each hour up with `at()`; combine with the altitudes from D2 into `TimelineEntry` values. A `None` group contributes no hours and null fields. Tests prove the union, the order and the nulls through this seam.

Alternative: a helper in `core/conditions.py` returning the union (fine too, but the producer is the one place that already combines the groups with the astronomy).

### D4. The verdict attributes payload is the document minus `timeline`

In `publish_verdict`, publish `document.model_dump_json(exclude={"timeline"})` to the attributes topic instead of `document.to_json()`. Pydantic keeps the remaining keys in declaration order, so the payload is byte-identical to today's for a document with no timeline. `to_json()` itself stays the whole document, because the document is the core's contract and the exclusion is a delivery rule.

Alternative: a `to_attributes_json()` on the model (puts a Home Assistant limit into the core's vocabulary, which ADR 0001 keeps out).

### D5. Cloud cover sensor follows the rank-sensor pattern

New topic helpers `cloud_cover_state_topic` and `cloud_cover_attributes_topic` (`pierpressure/<pier>/cloud_cover/state|attributes`). `build_cloud_cover_discovery` emits name `Cloud cover`, `unique_id` `<node>_cloud_cover`, `unit_of_measurement: "%"`, `icon: mdi:weather-cloudy`, the device block, and the two-entry availability list keyed on `value_json.available`. No `state_class` and no `device_class`: the value is a forecast that is rewritten every recompute, so long-term statistics would be noise. `cloud_cover_state(document)` returns the current hour's value as a string, or `""`. `cloud_cover_attributes(document)` returns `{"available": bool, "current": value | None, "forecast": [{"datetime", "value"}, ...]}`, with `available` re-asserted first as the rank attributes do. Both are published retained on every `publish_verdict`, after the rank sensors and before the narrative. `SENSOR_SCHEMA` gains `unit_of_measurement`.

The current hour is `generated_at` with minutes, seconds and microseconds zeroed, compared with each entry's `time`.

Alternatives: putting the forecast on the Verdict entity (the recorder limit forbids it); a `weather` entity (MQTT has no weather platform); `state_class: measurement` (adds statistics churn for a forecast value).

### D6. Golden fixtures regenerate once, additively

Regenerate the eight expected documents with `PP_WRITE_GOLDENS=1` in their own commit, after the core change lands and before delivery work. The reviewed diff must add a `timeline` key to each file and change nothing else.

### D7. Documentation

New page `docs/night-timeline.md`: what the timeline is, the Cloud cover sensor and its `forecast` array, why the Verdict attributes leave the timeline out, one apexcharts-card example, and a note that the sensor is rewritten every recompute so users may exclude it from the recorder. A `tests/test_docs.py` style guard checks the page exists and names the sensor, the attribute and the card. `README.md`: a Cloud cover row in the entity table, the two new topics, and the verdict document section gains the `timeline` row and the sentence that the Verdict attributes exclude it.

### D8. ADR 0025 records the timeline

The timeline's shape, that it is additive, that it is evidence beside the verdict (ADR 0023 stands), that the verdict attributes exclude it, and the consequence that MQTT carries it per variable. Written in the ADR step.

## Risks / Trade-offs

- [The Cloud cover attributes payload could grow past the recorder limit] → 72 entries at about 50 bytes each is about 4 KiB. A test asserts the payload for 72 entries stays under 16 KiB.
- [Golden regeneration can hide an unintended change] → the regeneration commit is separate and its diff is reviewed as timeline-only; the existing determinism tests still run against the new goldens.
- [Per-hour astronomy slows a recompute] → one vectorised evaluation per body (D2); a test pins the altitudes against the dark window's sign change so the vector call is proven equal to the single-instant path.
- [An existing consumer reads the whole document from the attributes topic] → the README said the attributes hold the whole document; it now says they hold everything but the timeline. No existing key moves, so every existing template keeps working.
- [The Score sensor reads the attributes topic] → the exclusion keeps `score` in place; the existing Score tests cover it.

## Migration & Rollback

N/A for data. Deploying publishes one new retained discovery config and two new retained topics per pier. Rolling back leaves a retained Cloud cover entity in Home Assistant until its discovery topic is cleared, the same as every other entity (see the README's removal section).
