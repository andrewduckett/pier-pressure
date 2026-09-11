## Why

The conditions snapshot the core reads today is one flat hourly grid with two
issue-times bolted on the side (`base_issued_at`, `secondary_issued_at`). That
shape fights the domain: each source owns different fields (Open-Meteo gives cloud
and wind; 7Timer! gives seeing and transparency), so per-source freshness is
pushed into parallel side-channels and "which source contributed what" is implicit
in which fields happen to be present. A discarded second attempt at M3 modelled
conditions as one group per source and read far more clearly. This change adopts
that seam. It is an internal refactor: the verdict document, the delivery surface,
and every field's meaning are untouched, and the output is byte-identical.

## What Changes

- Replace the single `ConditionsSnapshot` / `HourlyConditions` grid with a
  **per-source group** model: a `Conditions` value holding an optional `BaseGroup`
  (the Open-Meteo cloud + wind source) and `SecondaryGroup` (the 7Timer! seeing +
  transparency source). Each group carries its own `GroupMeta` (source + issue
  time) and its own hourly readings; an individual hour-field stays independently
  present-or-absent. This mirrors today's two `SourceForecast`s and two issue-times
  promoted into the core model, so the transformation is minimal.
- Move per-source freshness from the two snapshot-level `*_issued_at` fields onto
  each group's `GroupMeta`, so each source's staleness travels with its own data.
  Freshness reads the base group's issue time exactly as today reads
  `base_issued_at`; the secondary source's issue time is carried for provenance
  but, as today, not consumed by freshness.
- Update the provider layer (`pierpressure/conditions/`) to build groups, the
  core (`core/scoring.py`, `core/producer.py`) to read groups, and `service.py`'s
  conditions-provider seam and empty fallback to speak the group model.
- **No behaviour change.** 7Timer! keeps its existing provider-side resample to
  the hourly grid; the cloud-clarity-weighted scoring is unchanged; the verdict
  document is byte-identical. A golden-output regression test over recorded
  fixtures locks this, alongside the existing determinism and verdict tests
  (adapted only to construct the group model).
- Remove the discarded M3 attempt (its rival `core/verdict.py`, its `providers/`
  package, its tests, and the duplicate `ADR-0005`), whose good idea this change
  keeps while its code — wired to a core model that no longer exists — is dropped.

Explicitly **out of scope** (parked, not adopted): the discarded attempt also
carried native-cadence seeing storage and a richer cloud model (low/mid/high
components with a separate high-thin cloud penalty). Both change the seeing or
cloud science and the score — they are science, not seam — so they are deferred
to a future conditions-tuning milestone, not pulled in here.

## Capabilities

### New Capabilities

_None._

### Modified Capabilities

_None._ This is a pure internal refactor with no spec-level behaviour change: the
`conditions` capability's observable behaviour — per-field availability, per-source
issue times, no single load-bearing source, caching within a staleness bound, and
a self-contained offline snapshot — is preserved exactly. The change therefore
sets `skip_specs: true`; no requirement changes, so no delta spec is written.

## Impact

- **Core:** `pierpressure/core/conditions.py` (the model), `core/scoring.py` and
  `core/producer.py` (read groups instead of the grid).
- **Provider layer:** `pierpressure/conditions/` — `provider.py`
  (`assemble_snapshot`, `CachingProvider`, `CompositeProvider`), `open_meteo.py`,
  `seven_timer.py` build and cache groups.
- **Service:** `pierpressure/service.py` — the `ConditionsProvider` type alias
  and the empty-conditions fallback.
- **Tests:** conditions-model, conditions-provider, scoring, producer, and any
  determinism/verdict fixtures that construct a snapshot; plus a new golden-output
  regression test.
- **Decision records:** ADR-0005 (`conditions-provider-edge-seam`) is refined by a
  new ADR recording the per-source-group shape; the duplicate untracked
  `0005-conditions-as-injected-snapshot.md` and the rest of the discarded attempt
  are removed.
- **No change** to MQTT topics/entities, the verdict document, dependencies, or
  the astronomy stack.
