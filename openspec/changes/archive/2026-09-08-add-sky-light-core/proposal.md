## Why

M1 froze the verdict-document contract and the MQTT pipe with **stubbed** decision
values (`dark_window` null, no moon, `confidence {LOW, 0}`). M2 is the first
milestone that puts *real astronomy* behind that contract: it computes the
astronomical-night window and the moon's behaviour deterministically, so the
document begins to carry true sky facts. No weather, catalog, or ranking yet —
this milestone retires the **astronomy-data plumbing risk** (deterministic,
offline ephemeris) the way M1 retired the MQTT plumbing risk.

## What Changes

- **Real `dark_window`.** Compute astronomical night (sun below −18°) for the
  pier from the injected clock's date, filling `dark_window.start`/`end`. When
  there is no astronomical night (e.g. high-latitude summer), `dark_window` stays
  `{null, null}` — this is a valid outcome and the seed of M3's "no dark window"
  hard gate.
- **New `moon` object in the document.** Illumination fraction and phase name,
  plus the moon's behaviour *across the dark window* (whether it is above the
  horizon during astronomical night, and its rise/set instants within that
  window). This grows the contract; the pipe, topics, and entities are unchanged.

  *Additive growth, per the contract rule.* The durable contract rule in
  `openspec/config.yaml` freezes the delivery surface (topics, entities, entity
  mapping) and the meaning of existing fields, while explicitly allowing the
  document to grow **additively** as a milestone's science arrives. Adding `moon`
  is exactly that: it only grows the JSON attributes payload the verdict sensor
  already publishes — no topic, entity, or existing-field change. The rule also
  says to reserve a field's shape early only when it is already known; `targets`
  is deliberately **not** grown here because its shape is defined by M5's ranking,
  so inventing one now would be the churn the rule warns against.
- **No target work; `targets` stays `[]`.** The target alt/az night-grid engine
  is deferred to M5, where the catalog and ranking define what a target needs — it
  has no consumer in M2, so building it now would be dead code at risk of a
  rewrite. M2's sun and moon math already exercises the same Skyfield machinery
  (twilight/rise-set via `find_discrete`, positions via the ephemeris), so the
  deterministic-sky-math risk is retired without it.
- **Deterministic, offline sky math.** Skyfield with a **vendored, version-pinned
  ephemeris** and the built-in timescale; **zero runtime network access**. A
  fixed rounding rule (illumination to 2 dp, times to whole seconds; angular
  values to 2 dp when later surfaced) keeps output deterministic for a given
  platform and pinned library set, with CI guarding cross-platform drift.
- **First scientific dependency.** Adds Skyfield (Skyfield-only; Astroplan/Astropy
  deliberately *not* adopted — see design) plus the pinned ephemeris data.
- The stub producer body (`produce_verdict`) is replaced behind its existing
  signature. Signature, document key order, and the MQTT contract are unchanged.

## Capabilities

### New Capabilities
<!-- None. M2's only observable output is the verdict document, which is the
     existing night-verdict capability (modified below). No new capability. -->

### Modified Capabilities
- `night-verdict`: `dark_window` is now populated from real astronomical night
  (sun < −18°), including the null result when no astronomical night exists; the
  document gains a `moon` object (illumination, phase, and above-horizon
  behaviour across the dark window); and the document's astronomical fields are
  required to be computed deterministically and fully offline, with a defined
  rounding rule.

## Impact

- **Code.** `pierpressure/core/producer.py` (real sun/moon math replaces the
  stub); `pierpressure/core/model.py` (new `Moon` model + `moon` field; rounding
  at validation); a new core module for the ephemeris/almanac engine (twilight
  window + moon). `pierpressure/delivery/` is untouched (it publishes the
  document's JSON attributes generically).
- **Dependencies.** Add `skyfield` and a pinned ephemeris (as a locked dependency
  where possible, else vendored at build time with a checksum). Both captured in
  `uv.lock`. Container image grows by the ephemeris file (~tens of MB).
- **Contract.** The verdict document grows a `moon` object and starts emitting
  real `dark_window` values. Additive; topic scheme, entity mapping, and existing
  keys are unchanged.
- **Tests.** Pinned-instant determinism tests for known sites/dates; a
  no-astronomical-night edge test; an **offline-guard test** asserting the core
  makes no network access during `produce_verdict` (mirrors the existing
  core/delivery boundary test).
- **Sequencing.** `night-verdict` is a *modified* capability whose base still
  lives in the unarchived M1 change delta; M1's specs need syncing to main specs
  before M2's delta has a clean base (see summary).
