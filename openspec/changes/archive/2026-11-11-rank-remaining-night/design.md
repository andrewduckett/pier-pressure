## Context

`pierpressure/core/ranking.py` ranks in one pass per night:

1. A coarse scan samples every candidate's altitude and azimuth on a 5-minute
   grid across the dark window.
2. It finds each candidate's longest above-mask run and coarse-scores it.
3. It refines candidates top-down (exact edges, transit, peak) until ten pass
   the minimum-duration gate.

`rank_targets` takes `instant` but never uses it. The result is cached per
`(pier, horizon, equipment, dark window)` in a 16-entry LRU.

Measured on the London golden night (2026-09-08): 3,728 candidates, an 84-point
grid, about 4.2 s for an uncached ranking and effectively 0 s for a cache hit.
The container recomputes every pier on an interval, so a full rescan on every
refresh would cost seconds per pier.

`pierpressure/core/scoring.py` derives the scored window inline in `evaluate`:
it floors the instant to a whole second, then clamps it into the dark window.
The delivery adapter and the explainer prompt dump every `Target` field, so a new
field reaches Home Assistant and the narrative with no change there.

## Goals / Non-Goals

**Goals:**

- Rank, gate and score on each target's remaining window, as the delta specs
  say, with one definition of the scored window shared by the verdict and the
  ranking.
- Keep the expensive whole-night scan cached per night, so a mid-session
  recompute costs a vectorized lookup and the refinement of a few finalists,
  not a catalog rescan.
- Before dusk, emit exactly today's targets, plus `remaining_window`.

**Non-Goals:**

- Changing the grid step, the weights, the curves or the minimum duration.
- Changing what `window`, `max_altitude`, `transit_time` or `moon_separation`
  mean.
- Any card, delivery or explainer change. The card is #277.

## Test Seams

- **Primary test seam:** `rank_targets` against the real vendored catalog at
  pinned instants, offline, as `tests/test_ranking_pipeline.py` already does.
  Mid-session cases pin an instant inside the London golden night. The
  two-stretch case uses a horizon mask with a wall that hides a chosen target
  partway through the night.
- **Existing seams reused:** `geometry_for` (`tests/test_ranking_geometry.py`)
  for the remaining-window geometry. The scenarios that name a single factor
  (altitude, transit timing, window length) are asserted here: the remaining
  geometry's peak altitude, transit and length, fed to the existing pure
  sub-score functions. `Target` exposes only the combined `score`. The golden verdict suite
  (`tests/test_golden_verdict.py`) for the document shape, where
  `both_present_mid_session` shows the mid-session change end to end. The
  sub-score unit tests stay as they are.

## Scrutiny Tier & Blast Radius

- **Tier:** medium
- **Blast radius:** `pierpressure/core/ranking.py` (pipeline and cache),
  `pierpressure/core/model.py` (`Target` gains a field), and a small extraction
  in `pierpressure/core/scoring.py`. The verdict document grows by one field per
  target. The golden fixtures change. Delivery and the card are untouched.

## Decisions

### D1. One scored-window function, shared by the verdict and the ranking

Move the two lines in `evaluate` into a public `scored_window(instant, window)`
in `scoring.py`, and call it from both `evaluate` and `rank_targets`.
`rank_targets` keeps its signature.

- *Alternative:* the producer passes `decision.scored_window` into
  `rank_targets`. That couples ranking to the verdict's `Decision`, and makes
  ranking alone (the pipeline tests) need a verdict first.
- *Alternative:* `ranking.py` derives the window itself. Two copies of the clamp
  can drift, which is the bug class the glossary entry exists to prevent.

### D2. Split the pipeline into a cached night scan and a per-instant ranking

The night scan is computed once per `(pier id, location, horizon, dark window)`
and holds:

- the whole-night grid times;
- the moon's grid altitude and azimuth;
- for each candidate above the mask at one grid point or more: its altitude,
  azimuth and above-mask arrays;
- a memo of each candidate's refined whole-night `Geometry`, filled lazily for
  finalists.

Every call to `rank_targets` then ranks from the scan at its own scoring
instant. Equipment leaves the cache key, because the scan does not depend on it.
Field-of-view fit is applied per call, so two rigs on one pier share a scan and
still score differently.

Dropping candidates that never clear the mask at a grid point is safe. Such a
candidate's longest remaining run is at most the scoring-instant point, which is
shorter than one grid step and so far below the minimum.

- *Alternative:* cache the final list keyed on the instant. Every recompute is a
  new instant, so it would never hit.
- *Alternative:* cache per grid step, reusing a list for every instant in the
  same 5 minutes. That breaks "a recompute matches a fresh ranking at the same
  instant", and serves times up to 5 minutes stale.

### D3. The remaining grid is the scoring instant, then the grid points after it

Once the night has started, the remaining grid is the scoring instant followed
by every whole-night grid point later than it. The scan supplies the later
points. The instant's column comes from one vectorized Skyfield call: a `Star`
built from the scanned candidates' coordinate arrays, observed at that single
time, plus the moon at that time.

- Before dusk, the scored window starts at `dark_window.start`, which is already
  grid point 0. The remaining grid is the whole-night grid itself, so every
  coarse and refined value is computed exactly as today.
- When the scoring instant falls exactly on a grid point, it is not repeated.
- An empty scored window yields an empty list before any lookup.

The instant column is always computed the same way, cached or not, so a later
recompute and a fresh ranking at the same instant give byte-identical output.

### D4. Reuse the existing coarse pass and refinement over the remaining grid

The coarse pass, `observable_window`, `_refine` and the top-down walk run
unchanged over the remaining grid, with two parameter changes:

- The window factor's denominator is the scored window's length, not the dark
  window's.
- `_refine` gets the scored window as its clamp. A run at remaining index 0
  starts at the scoring instant, and the target is above the mask there by
  construction.

The transit used for the remaining window's peak and transit factor is the
crossing nearest the remaining window's midpoint, which `_transit_time` already
finds. A passed transit therefore scores 0.

The re-gate tests the refined remaining window against `MIN_USABLE_WINDOW`.
Each target that passes also gets its whole-night `Geometry` from the memo, for
`window`, `max_altitude`, `transit_time` and `moon_separation`. Before dusk, the
two geometries are the same object, so nothing is refined twice.

### D5. `remaining_window` is a required `TargetWindow` after `window`

`Target` gains `remaining_window: TargetWindow`, declared right after `window`,
so the serialized document reads `window` then `remaining_window`. It is always
present, because every listed target has one.

This is an additive contract field with a permanent meaning. The ADR step
records it, together with the reversal of ADR-0023's accepted constraint that
"the target list still judges the whole night".

### D6. The scan cache holds 8 nights

A scan holds three float64 or bool arrays per scanned candidate. That is about
5 MB on the London September night and about 18 MB on a 24-hour polar night. The
LRU bound drops from 16 to 8. That still covers eight piers through a night
rollover, and caps the worst case near 150 MB. Correctness never depends on a
hit: eviction only costs a rescan.

- *Alternative:* store float32 arrays to halve memory. Coarse values would then
  differ from today's float64 ones, and could change which candidates reach
  refinement. That would change pre-dusk output, against the "unchanged before
  dusk" decision.

## Risks / Trade-offs

- [Scan memory grows with the night length and the number of piers] → An 8-entry
  LRU, and only candidates that clear the mask are kept. The sizes are recorded
  in D6, so a later change can tune the bound.
- [More than eight piers thrash the cache and rescan every recompute] → It stays
  correct, just slower, as it is today past 16 piers. The bound is a module
  constant.
- [The coarse longest run can differ from the refined longest run] → The same
  approximation as today. The refined window is re-gated, and the 5-minute grid
  sits well below the 60-minute minimum.
- [The vectorized instant column differs in the last bits from a per-object
  call] → It feeds only the remaining grid, and is always computed the same way,
  so the output stays deterministic.
- [Scores and the top pick now move through the night, so Home Assistant
  automations on the top target can fire more than once] → Intended, and the
  same trade ADR-0023 accepted for the verdict score.
- [The pipeline cache tests count calls to `_rank`, which no longer scans] → Those
  tests are rewritten to count scans.

## Migration & Rollback

- **Document:** additive. Each target gains `remaining_window`. No consumer has
  to change, and Home Assistant attributes gain the key.
- **Golden fixtures:** regenerated in the same change. Pre-dusk fixtures change
  only by the new key.
- **Rollback:** revert the change. Nothing is stored, so a revert needs no data
  migration.
