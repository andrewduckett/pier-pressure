## Why

Issue #24. Tonight's ranked target list reaches Home Assistant only as JSON
attributes on the Top target sensor. Stock dashboard cards can't show those
attributes as a list. So a user whose top target doesn't suit them can't see the
other choices without a custom card. One sensor per rank lets users put the whole
list on any card.

## What Changes

- Add one sensor per rank to each pier's device: **Target 1** to **Target 10**.
  Ten is the ranking's `TOP_N`.
- Each rank sensor's state is that target's display name. The display name is the
  common name, or the catalogue id when the catalogue records no common name. This
  is the same rule the Top target sensor uses.
- Each rank sensor carries its rank and that target's ranking details as JSON
  attributes.
- A rank with no target tonight shows as `unavailable`, never as a placeholder.
  Every publish updates all ten ranks. So when the list shrinks, a rank that
  had a target earlier in the night becomes unavailable instead of keeping its old
  target.
- The adapter enables all ten sensors by default.
- Update the README entities table, the MQTT topics table, and the
  entity-removal example to include the rank sensors.

Out of scope:

- A custom Lovelace card.
- Any change to the Top target sensor, the other entities, or the verdict
  document. The rank sensors are additive.
- The Home Assistant acceptance checklist that the issue mentions. PR #32 removed
  that checklist, so there is nothing to update.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `ha-delivery`: add a requirement that exposes each rank of the target list as
  its own sensor entity.

## Impact

- **Code:** `pierpressure/delivery/mqtt.py` gains topic helpers, a discovery
  builder, and state and attribute helpers for rank sensors. `MqttDelivery.publish_verdict`
  publishes them. The adapter reads `TOP_N` from `pierpressure/core/ranking.py`.
- **Tests:** a new test module covers the rank sensors' discovery, state,
  attributes, and availability, and checks that existing entities are unchanged.
- **MQTT traffic:** each publish adds 30 retained messages per pier. Each of the
  10 ranks gets a discovery config, a state message, and an attributes message.
- **Docs:** `README.md`.
- **Dependencies:** none.
