## Context

See proposal.md — Why. The verdict document, dark window, moon behaviour
(`core/sky.py`), and the horizon mask (`core/horizon.py`) are all real and pure.
The `targets` field has shipped as an empty `list[str]` since M1. This design fills
it, reusing the existing offline, deterministic astronomy.

Constraints that shape the approach:

- **Pure, deterministic core.** Same `(pier, instant)` yields a byte-identical
  document. Astronomy is offline from a version-pinned ephemeris; a test guards
  the core against Home Assistant and MQTT imports.
- **Additive contract growth.** The delivery surface and the meaning of existing
  fields are frozen. `targets` was reserved but never shaped; M5 defines its
  element shape (recorded in adr.md).
- **Existing patterns to follow.** The ephemeris loads via a cached loader inside
  `core/sky.py`. The horizon takes text, not file paths. Conditions are passed
  into `produce_verdict` because they are I/O; static offline data is loaded
  inside the core.

## Goals / Non-Goals

**Goals:**

- Fill `targets` with the top 10 ranked deep-sky objects for the selected night.
- Load a version-pinned OpenNGC catalog offline and deterministically.
- Rank on four astronomy factors, reusing the dark window, horizon mask, and moon.
- Add one additive "top target" Home Assistant sensor.

**Non-Goals:**

- **Equipment and field-of-view fit.** Deferred until an equipment model exists;
  no `fov_fit` field is reserved (do not shape a field before its milestone).
- **Brightness as a ranking term.** Magnitude is a candidate filter only this
  milestone; brightness weighting arrives with the equipment work.
- **A catalog-source interface.** One real catalog ships here; a seam would be
  premature abstraction. Messier is a view over OpenNGC (its `M` column), not a
  second source.
- **Per-target prose reasons.** The structured fields are the explanation; the
  M6 LLM layer turns them into prose.

## Decisions

### D1 — Vendor the full OpenNGC catalog, loaded like the ephemeris

Commit the upstream OpenNGC data files as-is, with their license and attribution,
and parse them in a new pure module `core/catalog.py`. A cached loader (mirroring
`_ephemeris()` in `core/sky.py`) reads the bundled files once into an immutable
in-memory table. The committed bytes are the version pin.

- **Why not a Messier subset:** the full catalog is the milestone's stated
  ambition; Messier is derivable as a filter over it.
- **Why not the `pyongc` package:** it adds a dependency for data we can vendor,
  and makes determinism depend on the package keeping coordinate values stable
  across releases. A committed file is the tighter pin and keeps the 6-dependency
  surface lean.
- **Why load inside the core, not pass it in:** the catalog is static offline
  data, exactly like the ephemeris — unlike conditions, which are I/O handled
  outside the core. `produce_verdict`'s signature is unchanged.

The loader filters to observable types (galaxies, nebulae, clusters), drops
stars, duplicates, and non-existent entries, and applies the magnitude cutoff
(keeping unknown-magnitude objects). OpenNGC RA/Dec are sexagesimal J2000 strings;
they are parsed to hours/degrees and built into Skyfield `Star` objects, which
handle precession to the evaluation instant. Magnitude and size are stored but
not emitted — future fuel for FOV and brightness work.

### D2 — The `Target` element shape (additive fill)

Each target object carries: `id`, `name` (nullable), `type`, `score` (0–100,
unbanded), `window {start, end}`, `max_altitude`, `transit_time`, and
`moon_separation`. Every field is a value M5 actually computes; the structure is
the explainability. The `list[str]` → `list[Target]` change is additive fill of a
reserved-but-shapeless stub, not a meaning change — recorded in adr.md. M5 fills
`targets` only; verdict, score, confidence, reasons, dark_window, and moon stay
byte-identical, so in every golden fixture only the `targets` array changes.

### D3 — Ranking pipeline: gate, geometry, score, bound, refine

For the selected night's dark window and the pier's horizon mask:

1. **Candidate filter** (in the loader): eligible type, and magnitude at or
   brighter than the cutoff (unknown magnitude kept).
2. **Geometry, on a coarse fixed time grid** across dusk→dawn: sample each
   candidate's altitude and azimuth, test `horizon.is_above(az, alt)` at each
   grid point, and derive the observable window and the maximum altitude within it
   (with the instant of that maximum, used for moon separation). The grid step is
   a named constant. The `transit_time` is NOT read from this night grid: the
   meridian crossing can fall in daylight for a circumpolar target, outside the
   grid. It is computed separately by meridian-transit finding over the day around
   the instant — the same Skyfield facility already used for the sun's transit in
   `core/sky.py` (`almanac.meridian_transits`) — so a daytime transit is captured.
3. **Gates:** a candidate must clear the mask within the dark window (non-empty
   window) for at least the minimum duration. The observable `window` is the
   longest contiguous above-mask interval within astronomical night, bounded by
   the dark-window edges — a target already above the mask at dusk, or still above
   it at dawn (including a circumpolar target above the mask all night), has its
   window clamped to the dusk/dawn boundary. An irregular skyline can produce more
   than one above-mask interval, and the longest is the one an observer plans
   around.
4. **Score:** four sub-scores in [0, 1], combined by weights, scaled to 0–100
   and rounded to an integer (see D4).
5. **Bound and order:** keep the top 10 by score, ties broken by `id`.
6. **Refine the finalists:** for the 10 emitted targets only, replace the
   grid-resolution window edges and transit with Skyfield root-finding —
   `find_maxima` for the meridian transit, and zero-crossings of
   `alt(t) − mask.alt_at(az(t))` for the window edges. A window edge with no mask
   crossing inside the dark window (a target already above the mask at dusk, still
   above it at dawn, or circumpolar) is clamped to the dark-window boundary rather
   than left undefined, so refinement never fails on a target that does not cross
   its mask. Refinement runs over the score-ordered candidates: each is refined,
   its minimum-duration gate re-checked against the exact window, and one whose
   refined window falls below the minimum is dropped; the walk continues down the
   ordered candidates until 10 have passed or the pool is exhausted. Every emitted
   target is therefore both refined (exact whole-second times, consistent with
   moonrise/moonset) and gate-satisfying — the list never mixes exact and
   grid-resolution targets. The walk refines at most 10 plus the few dropped, so
   root-finding cost stays far below the ~14k candidate scan.

### D4 — Sub-scores and weights

- **Altitude** = `sin(max_altitude)` — the inverse-airmass transmission proxy;
  rewards high transits, punishes low skimmers. Alternative (linear in altitude)
  ignores the fast low-altitude falloff.
- **Window** = `observable_duration / dark_window_duration` — circumpolar-all-
  night approaches 1.
- **Moon** = `1 − moon_impact × (1 − sep_score)`, where
  `sep_score = clamp(separation / 90°, 0, 1)` and `moon_impact = illumination`
  when the moon is above the horizon at the target's **maximum-altitude instant
  within the dark window**, else 0. That instant — not the meridian transit, which
  can fall in daylight for a circumpolar target — is also where `moon_separation`
  is measured. Reuses the computed `moon` object and self-neutralizes on a new moon
  or when the moon is down at that instant.
- **Transit** = `clamp(1 − |transit − window_mid| / (window_len / 2), 0, 1)` —
  1 at window centre, 0 at an edge or outside; modest weight because it
  correlates with altitude. `transit_time` is the meridian crossing for that day,
  which can fall in daylight for a circumpolar target; such a transit lies outside
  the observable window, so this sub-score is 0 — the correct penalty for a target
  whose best moment is not during darkness.

Default weights: altitude 0.35, window 0.30, moon 0.25, transit 0.10. These are
tuning constants, like the verdict's `go_threshold`; a task validates them against
a known good night before the milestone is done.

### D5 — Determinism and performance

Determinism holds from the committed catalog, the pinned ephemeris, fixed-step
grid, fixed rounding (score to integer, degrees to a fixed precision as
`core/model.py` and `core/horizon.py` already do), whole-second times, and the
`id` tie-break. The ranking parameters — magnitude cutoff, minimum window
duration, sub-score weights, and grid step — are fixed module constants this
milestone, so they are pinned by the application version and do not vary per pier.
The ranking therefore depends only on `(pier, selected night)`, so it is cached
per that key: recomputes within one night (denser near dusk) reuse one ranking. If
any ranking parameter becomes per-pier or user configuration later, the cache key
MUST include it. The cache is a performance optimization only; correctness does
not depend on it.

### D6 — Delivery: an additive top-target sensor

Add one MQTT-discovery sensor: state is the top target's name (its `id` when no
common name), attributes carry the full ordered list and the top target's fields.
Identity derives from the pier identifier, like the existing entities; it is
published retained. When `targets` is empty the sensor resolves to unavailable via
its availability declaration, mirroring how the score entity handles a null score.
No existing entity, topic, or mapping changes.

## Risks / Trade-offs

- **~14k candidates × a time grid is heavy** → coarse grid scan, per-night cache,
  and root-finding only on the top 10. Determinism is unaffected.
- **CC-BY-SA-4.0 licensing of OpenNGC** → commit the upstream files with a NOTICE
  and attribution; confirm share-alike compatibility with the repo's license
  before merging. A dedicated task covers this.
- **OpenNGC data quirks** (blank magnitudes, coordinate/type edge cases) → keep
  unknown-magnitude objects, and test the parser against real rows including the
  addendum.
- **Untuned weights and cutoffs** → set sane defaults, then validate ranking
  against a known autumn night (for example, is M31 ranked sensibly) before done.
- **Every golden fixture regenerates** → only the `targets` array changes; a test
  asserts the other fields are byte-identical to guard the additive-only claim.

## Migration Plan

Additive and behind no flag. On deploy, the verdict document gains a populated
`targets` array and Home Assistant gains one new auto-discovered sensor; existing
entities are untouched. Rollback is reverting the change — the prior version
emits `targets: []` again, and the top-target sensor stops being published (Home
Assistant marks it unavailable). No data migration.
