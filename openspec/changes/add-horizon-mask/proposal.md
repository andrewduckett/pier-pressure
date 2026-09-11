## Why

A real pier does not see open sky in every direction: trees, buildings, and hills
block parts of the horizon. Without a model of that terrain, M5's target ranking
would treat every direction as clear and recommend targets that are actually hidden
behind an obstruction — the misleading-recommendation failure PierPressure exists to
avoid. This change (milestone M4) builds the horizon mask now, as pier **site** data,
so M5 has a terrain-aware "is this target visible from here" test to consume. Running
multiple piers already works (delivery has been per-pier since M1); the horizon mask
is the missing site attribute.

## What Changes

- **New canonical horizon representation.** An ordered list of `(azimuth, altitude)`
  samples — azimuth measured from north (0°) clockwise through east, altitude in
  degrees — with linear interpolation between samples and cyclic wraparound across
  360°/0°. Every source of a horizon converts to this one shape.
- **A query seam, `alt_at(az)`.** The single thing M5 will call to learn how high the
  terrain rises in a given direction, so it can test whether a target clears it. M4
  has no consumer for this seam yet — it is built and unit-tested standalone.
- **Per-pier horizon configuration, three inputs, one canonical result:**
  - inline `points`: a list of `[az, alt]` pairs, hand-written or pasted;
  - a flat `min_altitude` floor (an imager's altitude limit with no terrain detail);
  - absent → flat 0° open sky (today's implicit behaviour, now explicit).
- **A NINA `.hrz` importer.** Parses the tool's `az alt` pair-per-line export into the
  same canonical samples, so a user can point at a horizon file they already exported.
  Stellarium and Telescopius are recognised format names but **not yet implemented**:
  they raise a clear "format not yet supported" error until a real export fixture
  lands (a fast-follow, kept out of this change so no format is guessed at).
- **No change to the verdict document.** `targets` stays empty; topics, entities, and
  the meaning of every existing field are untouched. In M4 the mask is configuration
  plus a query seam — nothing reaches the delivery surface until M5 has targets. This
  honours the "do not invent a document shape before the milestone that defines it"
  rule.

## Capabilities

### New Capabilities

- `horizon-mask`: the canonical per-pier horizon representation (sampled `(az, alt)`,
  north-zero clockwise, linear interpolation, cyclic wraparound), its query contract
  (`alt_at(az)`), its configuration inputs (inline `points`, a `min_altitude` floor,
  or absent → flat 0°), and its importers (NINA `.hrz` now; Stellarium and Telescopius
  recognised but not yet supported). Validation and the flat-horizon defaults live
  here.

### Modified Capabilities

- None. The verdict document and every night-verdict behaviour are unchanged: the
  horizon block is a new, separate part of a pier's configuration, owned and validated
  by the new `horizon-mask` capability, and it does not alter the existing
  pier-configuration, gate, score, or confidence requirements.

## Impact

- **New module** `pierpressure/core/horizon.py` (pure core). Parsers take horizon
  **text**, not file paths, so `produce_verdict` stays a pure, offline function — the
  `test_core_boundary` (no HA/MQTT imports) and `test_offline_guard` (no runtime
  network) guards continue to hold.
- **Config** `pierpressure/core/config.py`: `PierConfig` gains an optional `horizon`
  block (inline `points` | `min_altitude` | absent). A `.hrz` file reference is read at
  config-load time and parsed to canonical samples there, so no file I/O enters the
  core's verdict path. An invalid horizon is validated per-pier like the rest of the
  pier config: one bad entry never disables the others.
- **New ADR.** The canonical representation and azimuth convention (north-zero
  clockwise, linear interpolation, cyclic wraparound) are a hard-to-reverse contract
  that both the importers and M5's ranking bind to. ADR-0002 already anticipates
  "target altitude above the horizon mask" as a scoring term.
- **Tests.** Unit tests for the representation, interpolation and wraparound, the three
  config inputs, and the NINA importer against a real `.hrz` fixture under
  `tests/fixtures/`.
- **No new runtime dependency** (parsing is standard library); no verdict-document,
  topic, entity, or delivery change.
- **Roadmap.** M4 status flips to done in the PR that lands this change.
