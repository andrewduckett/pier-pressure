## Why

PierPressure answers two questions: "is tonight worth setting up for?" and "what
should I point at from this pier?" Milestones M1 through M4 answered the first —
the verdict, score, dark window, moon, and horizon mask are all real. The second
question is still unanswered: the `targets` list has shipped as an empty stub
since M1. This change (milestone M5) fills it with a ranked list of deep-sky
objects worth imaging tonight, computed from the same offline, deterministic
astronomy the verdict already uses.

## What Changes

- **Vendor the OpenNGC catalog.** Commit the upstream OpenNGC data files as-is,
  with their license and attribution, and load them in the pure core. The
  committed bytes are the version pin, matching how the ephemeris is pinned.
- **Add a deep-sky object catalog loader.** A new pure-core module parses
  OpenNGC, filters to observable object types (galaxies, nebulae, clusters), and
  drops stars, duplicates, and non-existent entries. Objects fainter than a
  magnitude cutoff are excluded; objects with no recorded magnitude are kept.
- **Rank tonight's targets.** For each eligible object, the core computes its
  observable window (above the horizon mask and within astronomical night), its
  maximum altitude, its transit time, and its separation from the moon. It scores
  each survivor 0 to 100 from four weighted factors — altitude, window length,
  moon separation, and transit timing — then emits the top 10.
- **Fill the `targets` field.** The `targets` list changes from `list[str]` to a
  list of structured `Target` objects (id, name, type, score, window,
  max_altitude, transit_time, moon_separation). This is the additive fill the
  field was reserved for; no other verdict-document field changes. Recorded in an
  ADR.
- **Add a "top target" Home Assistant sensor.** A new MQTT-discovery sensor
  surfaces the top-ranked target, with the full ranked list as attributes. This
  is additive — no existing entity or topic changes.
- **Document target ranking for end users.** Explain in plain language what the
  targets are, how they are ranked, and why an object might be absent.

Out of scope for M5: equipment and field-of-view fit (a ranking factor deferred
until an equipment model exists), and the OpenNGC-beyond-Messier work is already
covered because the full catalog ships here.

## Capabilities

### New Capabilities
- `target-ranking`: Load the pinned deep-sky object catalog, filter it to
  eligible objects, gate and rank them against tonight's astronomy and horizon
  mask, and produce the ordered `Target` list.

### Modified Capabilities
- `night-verdict`: The `targets` field is no longer always empty. Its requirement
  changes from "present and empty until ranking exists" to "an ordered,
  bounded list of structured `Target` objects." The meaning of every other
  document field is unchanged.
- `ha-delivery`: Add one MQTT-discovery sensor for the top-ranked target. Every
  existing entity, topic, and mapping is unchanged.

## Impact

- **New dependencies:** the vendored OpenNGC data files (committed, no runtime
  fetch). No new Python package is required; the ranking uses the existing
  Skyfield stack.
- **Core:** a new `core/catalog.py` (loader and filter) and target-ranking logic;
  `produce_verdict` fills `targets` from it. The catalog loads like the ephemeris
  — cached, offline, deterministic.
- **Contract:** `targets` element shape defined (additive). All golden-output
  fixtures regenerate: only the `targets` array changes; every other field stays
  byte-identical.
- **Delivery:** one new discovery payload and state topic for the top-target
  sensor.
- **Docs:** new end-user documentation of target ranking; `docs/roadmap.md` M5
  status flips to done in the landing PR.
