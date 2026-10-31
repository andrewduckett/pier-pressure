## Context

`pierpressure/delivery/mqtt.py` already publishes one timeline sensor, Cloud
cover, through five functions written for that one key:
`cloud_cover_state_topic`, `cloud_cover_attributes_topic`,
`build_cloud_cover_discovery`, `cloud_cover_state` and `cloud_cover_attributes`.
A private helper, `_current_hour_entry`, finds the entry for the hour that holds
`generated_at`, and returns nothing when that entry's `cloud_cover` is null.
`publish_verdict` sends the Cloud cover discovery, state and attributes after the
rank sensors, all retained.

Every value the new sensors need is already a flat field of `TimelineEntry`, and
the core rounds altitudes and qualities when it builds the entry. So the value
on the entry is already the number the document emits, and the adapter only
reads it. The retained-message replay after a reconnect resends whatever
`_publish` recorded, so new retained topics need no replay code of their own.

`tests/test_cloud_cover.py` drives `MqttDelivery` with `FakeMqttClient` and the
`make_document` and `make_timeline` helpers in `tests/conftest.py`.
`tests/test_timeline_docs.py` guards the docs page and the README.

## Goals / Non-Goals

**Goals:**

- One code path builds all nine timeline sensors, so the eight new ones cannot
  drift from Cloud cover.
- Cloud cover's topics, discovery payload, state and attributes stay
  byte-identical.

**Non-Goals:**

- No change to the core, the verdict document or `TimelineEntry`.
- No change to `SENSOR_SCHEMA`. The new payloads use only fields it already
  describes.
- No sensors for #136's weather variables, though the table this design adds is
  where they will go.

## Test Seams

- **Primary test seam:** `MqttDelivery.publish_verdict` on a `FakeMqttClient`,
  read back through the published topics, in a new `tests/test_timeline_sensors.py`
  parametrized over the eight keys. The pure functions it calls (discovery,
  state, attributes) are tested at the same level as `tests/test_cloud_cover.py`
  tests them.
- **Existing seams reused:** `tests/test_cloud_cover.py` stays unchanged and
  proves Cloud cover is unchanged. `tests/test_timeline_docs.py` gains the docs
  checks.

## Scrutiny Tier & Blast Radius

- **Tier:** medium. One module on an established pattern, but it adds entities
  and topics to the frozen delivery surface, so names, unique identities and
  topics cannot be changed once released.
- **Blast radius:** `pierpressure/delivery/mqtt.py`; the retained MQTT topics
  per pier; `README.md` and `docs/night-timeline.md`. The core is untouched.

## Decisions

### DD1: A table of timeline sensors drives one generic code path

A module-level tuple of frozen descriptors, one per sensor, holds the key, name,
unit (or none) and icon. Generic functions take a descriptor or a key:
the two topic helpers, the discovery builder, the state and the attributes.
`publish_verdict` loops over the table. Cloud cover is the table's first row.

- **Alternative:** copy the five Cloud cover functions eight times. Rejected:
  forty near-identical functions, and every later variable (#136) adds five more.
- **Alternative:** a generic path for the eight new sensors only, leaving Cloud
  cover as it is. Rejected: two paths for one behavior is exactly the drift DD1
  exists to prevent.

### DD2: The Cloud cover functions stay as thin delegates

`build_cloud_cover_discovery`, `cloud_cover_state`, `cloud_cover_attributes` and
the two Cloud cover topic helpers keep their names and signatures, and each
calls the generic function with the `cloud_cover` row. `tests/test_cloud_cover.py`
then runs unchanged against the new path, which is the strongest proof that
Cloud cover did not change.

- **Alternative:** delete them and update the Cloud cover tests to the generic
  names. Rejected: editing the regression tests in the same change that could
  break the behavior weakens what they prove. A later change can remove the
  delegates.

### DD3: Topics, object ids and unique ids use the timeline key

For key `k`: state `B/<pier>/k/state`, attributes `B/<pier>/k/attributes`,
discovery `P/sensor/pierpressure_<pier>/k/config`, unique id
`pierpressure_<pier>_k`. This is the scheme Cloud cover already uses, so its
topics fall out of the same rule. With `has_entity_name` and a name that slugs
to the key (brainstorm D4), Home Assistant's entity id is
`sensor.pierpressure_<pier>_k`.

### DD4: The value is read from the entry by key, checked by a test

The generic functions read `getattr(entry, key)`. A unit test asserts every
table key is a `TimelineEntry` field whose type is a number or null, so a typo
or a renamed field fails the suite rather than raising at publish time.

- **Alternative:** each descriptor carries an accessor such as
  `lambda e: e.cloud_low`. Typed, but it repeats each key twice per row and
  still needs the key for topics. The test gives the same safety with one name
  per row.

### DD5: The current-hour lookup is split from the null check

`_current_hour_entry` becomes a lookup that returns the entry for the current
hour whatever its values. The state and `hour` then treat a null value for the
sensor's own key as unknown. This makes `hour` per variable (brainstorm D3):
Seeing can be unknown while Cloud low has a value in the same hour.

### DD6: Publish order follows the table, after Cloud cover's current place

The loop sends each sensor's discovery, state and attributes in table order, at
the point where Cloud cover is sent today. Cloud cover is first, so every
message before and including it keeps its position.

### DD7: Icons

Cloud layers use `mdi:weather-cloudy`, like Cloud cover. Wind gust uses
`mdi:weather-windy`, Seeing `mdi:eye`, Transparency `mdi:telescope`, Sun
altitude `mdi:weather-sunny` and Moon altitude `mdi:weather-night`. Icons are
cosmetic, and a user can change them in Home Assistant.

### DD8: Documentation

- `docs/night-timeline.md`: the Cloud cover section becomes a section on the
  timeline sensors, with a table of the nine entity ids, units and what the
  state means, including that an altitude state is for the start of the current
  hour. The recorder example lists all nine entities.
- `README.md`: one entity row for the eight new sensors, the topic table row
  and discovery-topic pattern widened to the nine keys, and the nine keys in the
  "Removing the entities" loop.
- The `mqtt.py` module docstring's topic table gains the timeline sensor rows.

No dashboard YAML beyond the existing Cloud cover example: that is #135.

## Risks / Trade-offs

- [Folding Cloud cover into the table changes its payload or topic by accident]
  → `tests/test_cloud_cover.py` runs unchanged (DD2), and a new test compares
  the Cloud cover discovery payload with its literal current value.
- [A sensor with no unit, such as Seeing, shows its history as text values
  rather than a line graph] → Accepted (brainstorm D5). Charts read the
  `forecast` attribute, not history, and the recorder note suggests excluding
  the sensors.
- [Each recompute now sends 24 more retained messages per pier] → Each is a few
  kilobytes at most, under the 16 KiB limit a spec scenario checks, and they go
  out once per recompute interval.
- [An entity name that does not slug to its key gives a mismatched entity id]
  → A test asserts each name, lower-cased with spaces as underscores, equals
  its key.

## Migration & Rollback

No data changes shape. On the first publish after upgrade, Home Assistant
creates the eight sensors from their retained discovery messages. To roll back,
deploy the earlier image; the eight retained discovery messages stay on the
broker, so the entities stay too, shown as unavailable. Clear them with the
README's "Removing the entities" loop.
