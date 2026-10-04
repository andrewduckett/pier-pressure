## Context

See proposal.md — Why. The requirement is in `specs/ha-delivery/spec.md`.

The adapter in `pierpressure/delivery/mqtt.py` already publishes a Top target
sensor. That sensor has its own state topic and attributes topic. Its
availability is a two-entry list with `availability_mode: all`. The first entry
is the shared last-will topic. The second is a template on the attributes payload
that requires a non-empty list. The Narrative sensor uses the same pattern, with an
`available` flag in its attributes.

`pierpressure/core/ranking.py` defines `TOP_N = 10`, the longest list the ranking
emits. The delivery package already imports from the core, so it can read `TOP_N`
directly. The core never imports delivery, and this change keeps it that way.

Nobody uses PierPressure in production yet. So the design picks the simplest shape
and does not guard against migration or dashboard edge cases.

## Goals / Non-Goals

**Goals:**

- Give each rank its own sensor, using the same patterns as the Top target and
  Narrative sensors.
- Keep the logic in Python, so unit tests cover it without a template engine.

**Non-Goals:**

- Making all ten ranks update in one MQTT message. Home Assistant may briefly
  show a mix of old and new ranks during a publish. That is acceptable.
- Making rank count configurable. The adapter publishes exactly `TOP_N` ranks.

## Decisions

### D1 — Each rank gets its own state and attributes topics

For rank `n` of pier `<pier>`, the adapter publishes:

```
discovery   homeassistant/sensor/pierpressure_<pier>/target_<n>/config
state       pierpressure/<pier>/target_<n>/state
attributes  pierpressure/<pier>/target_<n>/attributes
```

The entity name is `Target <n>` and the `unique_id` is
`pierpressure_<pier>_target_<n>`. With `has_entity_name`, Home Assistant derives
an entity id like `sensor.pierpressure_<pier>_target_3`.

- **Alternative considered:** point every rank sensor at the existing
  `top_target/attributes` topic, and pick out its entry with Jinja value
  templates. That adds no new state topics, and all ranks update at once. We
  rejected it because it moves the name-or-id rule into templates. Testing it
  would then need a template engine. With no users to protect, the per-rank
  topics are the simpler choice.

### D2 — Availability uses an `available` flag in the attributes

The rank discovery payload uses the same two-entry availability list as the
Narrative sensor. The second entry's template reads
`{{ 'online' if value_json.available else 'offline' }}`.

The attributes payload is flat, so a card can read a field without
descending into a nested object:

- **Filled rank:** `{"available": true, "rank": n, ...}` followed by the
  target's fields as they appear in the verdict document (`id`, `name`, `type`,
  `score`, `window`, `max_altitude`, `transit_time`, `moon_separation`,
  `size_arcmin`, `magnitude`, `surface_brightness`).
- **Empty rank:** `{"available": false, "rank": n}`.

The state is the target's display name for a filled rank, and an empty string
for an empty rank. Home Assistant shows the empty rank as unavailable, because
availability fails. This matches how the Top target sensor handles an empty list.

- **Alternative considered:** reuse the Top target's `count`-based template,
  for example `count > n - 1`. That would put the whole list's `count` into every
  rank's payload. We rejected it because the explicit `available` flag reads more
  clearly.

### D3 — Every publish writes every rank

`publish_verdict` loops over ranks 1 to `TOP_N` on every publish, filled or not.
Every message is retained. So when the list shrinks from 5 to 2, the adapter
overwrites ranks 3 to 5 with `available: false`, and their old targets don't stay
on screen.

### D4 — Display-name rule is shared with the Top target

One helper returns a target's name, or its id when the name is null. Both
`top_target_state` and the new rank state use it, so the two sensors can't drift
apart. This is a small refactor inside `mqtt.py`. The Top target's published
output is unchanged.

### D5 — Rank 1 duplicates the Top target, on purpose

Rank 1 always shows the same target as the Top target sensor. We keep both. The
Top target sensor stays for existing automations and the README's notification
example. Rank 1 keeps the numbered set complete for a card that lists ranks 1 to 10.

### D6 — Order of publishes

The adapter publishes the rank sensors' discovery configs alongside the other
discovery configs. It then publishes their states and attributes after the Top
target's. The order matters only for readability and test assertions. Home
Assistant doesn't depend on it.

## Risks / Trade-offs

- [Ten more entities per pier crowd the device page] → They are enabled by
  default, as agreed. A user can disable any rank in Home Assistant.
- [30 more retained messages per pier on every publish] → Each message is a few
  hundred bytes. The publish interval is minutes, so the broker load is trivial.
- [If `TOP_N` shrinks later, the old higher ranks stay retained on the broker] →
  `TOP_N` has no plans to change. If it does, the README's removal example
  shows how to clear the extra discovery topics.

## Migration Plan

None. The new entities appear on the first publish after deploy. To roll back,
clear the rank discovery topics as the README's removal example shows.
