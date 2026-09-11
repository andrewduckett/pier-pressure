## Context

See proposal.md — Why. The core reads conditions as one flat `ConditionsSnapshot`:
a tuple of `HourlyConditions` (each hour holding `cloud_cover`, `wind_gust`,
`seeing`, `transparency`, any of them `None`) plus two snapshot-level issue times,
`base_issued_at` and `secondary_issued_at`. The provider layer
(`pierpressure/conditions/`) builds it: `OpenMeteoProvider` and `SevenTimerProvider`
each parse to a `SourceForecast`, `CompositeProvider` fetches both independently,
and `assemble_snapshot` unions them by top-of-hour key. 7Timer!'s 3-hourly astro
data is resampled to hourly **in its provider** (each value held across its three
hours). The core's scoring already treats cloud/wind as the load-bearing spine and
seeing/transparency as optional polish, scored as a cloud-clarity-weighted mean.

The frozen contract (the verdict document and the MQTT delivery surface) is not in
play here. This change restructures the *input* value the provider hands the core.

## Goals / Non-Goals

**Goals:**

- Model conditions as one group per source: `Conditions{cloud, wind, seeing}`,
  each an optional group carrying its own `GroupMeta` (source + issue time) and its
  own hourly readings.
- Make per-source freshness intrinsic — each group self-stamps — retiring the two
  parallel `*_issued_at` side-channels.
- Keep the verdict **byte-identical** for equal inputs, proven by a golden-output
  regression test plus the existing determinism/verdict tests.
- Remove the discarded M3 attempt from the tree.

**Non-Goals (design-level boundaries):**

- No native-cadence seeing storage — 7Timer! stays resampled-to-hourly in its
  provider, so the clarity-weighted mean is unchanged (this is what keeps the
  output byte-identical; see Decisions).
- No richer cloud model (low/mid/high, high-thin penalty), no scoring changes, no
  document changes. Deferred to a future conditions-tuning milestone.
- No change to caching, fallback, or the composite fetch behaviour beyond
  re-expressing them over groups.

## Decisions

### D1 — The per-source group model

One group per source — the source is the unit that actually fetches, fails,
caches, and stamps an issue time, so it is the honest grouping boundary:

```
GroupMeta(source: str, issued_at: datetime | None)               # aware UTC
BaseHour(time, cloud_cover: float | None, wind_gust: float | None)     # Open-Meteo
SecondaryHour(time, seeing: float | None, transparency: float | None)  # 7Timer!
BaseGroup(meta: GroupMeta, hours: tuple[BaseHour, ...])          # + .at(time) -> hour|None
SecondaryGroup(meta: GroupMeta, hours: tuple[SecondaryHour, ...])   # + .at(time) -> hour|None
Conditions(base: BaseGroup | None, secondary: SecondaryGroup | None)
```

This is today's two `SourceForecast`s (base = cloud/wind, secondary =
seeing/transparency) promoted into the core model, each self-stamped with its own
issue time. "Base" and "secondary" name the source *role* (the load-bearing spine
vs the optional polish), not a vendor — the core still never learns a source's
scale or resolution.

Two absence levels, both preserved from today:

- **Group present iff its source returned rows.** A group is `None` exactly when
  its source contributed no hour rows at all — the same condition as today's
  `base.readings`/`secondary.readings` being empty (which is what makes today's
  `base_issued_at` `None`). A source that returned rows but left a field empty
  yields a present group whose hours carry `None` for that field.
- **Per-field absence within a present group.** A `BaseHour` may have
  `cloud_cover=None` while `wind_gust` is set, and vice versa — the per-field stamp
  the verdict degrades against.

`Conditions(None, None)` is the canonical empty value (today's empty
`ConditionsSnapshot()` and the service's `_no_conditions` fallback).

*Why per-source over per-field (cloud/wind/seeing/transparency each their own
group):* per-field would duplicate one issue time across the two base fields and
re-create a cloud-vs-wind presence asymmetry (a source can return one base field
without the other), which is exactly the edge that would break byte-identical
freshness. Grouping by source keeps a source's fields, presence, and issue time
atomic — matching how today's `base_issued_at` already survives on *any* base
reading — and adds no more structure than today has. Per-field's only extra
benefit (a future source supplying one field but not its pair) is speculative and
belongs to whatever milestone introduces such a source.

### D2 — Freshness reads the base group's issue time, exactly as today

`base_issued_at` becomes `conditions.base.meta.issued_at`; `secondary_issued_at`
becomes `conditions.secondary.meta.issued_at`. Behaviour preservation is precise
here, and easy to get wrong: today's `confidence()` derives freshness from
`snapshot.base_issued_at` **only** — the base source's issue time — and never reads
`secondary_issued_at`. The refactor's freshness factor reads
`conditions.base.meta.issued_at if conditions.base else None`, falling back to the
maximally-stale floor only when the whole base group is absent.

Because base group presence follows "source returned rows" (D1), this is a
faithful mirror of today: today's `base_issued_at` is retained whenever the base
source returned *any* reading — cloud **or** wind — so if Open-Meteo ever returns
wind without cloud, freshness is preserved. Grouping cloud and wind into one base
group keeps that atomic: the base group (and its issue time) is present on any base
reading, so freshness never tanks on a cloud-only gap. This is the round-2 Critical,
resolved at the model level rather than by a special-case in the freshness code.

The secondary group's `meta.issued_at` is carried for provenance but, as today, is
**not** consumed by freshness. Do **not** introduce an "oldest issue time across
groups" helper: folding the (typically older) 7Timer! issue time into freshness
would lower confidence whenever 7Timer! lags Open-Meteo, changing the verdict and
breaking the byte-identical guarantee.

### D3 — 7Timer! stays resampled-to-hourly; scoring is untouched (the byte-identical hinge)

The seeing/transparency score is a per-hour cloud-clarity-weighted mean. That
weighting is entangled with the hourly grid: each seeing hour is weighted by that
hour's cloud clarity. Keeping 7Timer!'s existing provider-side hourly resample
means the secondary group carries the same hourly-held values the flat grid did, so
the weighted mean — and therefore the score, band, and confidence — is unchanged
by construction. The base and secondary groups are both hourly-keyed, so the
scoring cross-references cloud and seeing by hour via each group's `.at(time)`. Moving to native cadence was considered and deferred (proposal
Non-Goals) precisely because it would re-open this number.

### D4 — Behaviour preservation is proven, not asserted

Add a golden-output regression test: recorded Open-Meteo + 7Timer! fixtures →
build `Conditions` → `produce_verdict` at a pinned instant → assert the full
verdict document matches a committed golden. Land this characterization test
against the *current* flat-grid code first (so the golden is captured from known-good
behaviour), then refactor under it. Existing determinism/verdict/scoring/producer
tests are adapted only where they construct a snapshot.

The golden suite MUST cover the degradation and partial-coverage paths, not only
the happy path where both sources are present — absence and misalignment are
exactly where a per-group model is most likely to drift. At minimum:

- both-present;
- secondary-absent (7Timer! missing → seeing unavailable);
- base-absent (Open-Meteo missing → the low-confidence MAYBE path, exercising the
  D2 freshness floor);
- **base returns wind but no cloud** — the round-2 Critical case: the base group is
  present, so its issue time still drives freshness (verdict unchanged);
- **gappy coverage** — a source covers only part of the dark window, so some hours
  have a base hour but no matching secondary hour (and vice versa), proving the
  cross-group `.at(time)` alignment holds and never crashes or misaligns;
- empty conditions; and an over-stale cache.

Each case asserts that verdict, gates, band, score, confidence, and `reasons[]` are
byte-identical across the refactor.

### D5 — Delete the discarded attempt rather than salvage it

The untracked `core/verdict.py` + `providers/` import a `Conditions`/`CloudGroup`
core model that was overwritten out of the tree and exists in no commit, so the
code cannot import or run; it also carries a rival decision layer we are not
adopting. We keep its *idea* (this design) and delete its *code*. Files removed:
`pierpressure/core/verdict.py`, `pierpressure/providers/`, `tests/test_verdict.py`,
`tests/test_conditions.py`, `tests/test_provider_*.py`, and
`docs/adr/0005-conditions-as-injected-snapshot.md`.

### D6 — Absence and cross-group reads preserve today's None-handling

Three implementation invariants keep the group model byte-identical where the flat
grid was quietly forgiving:

- Each group exposes an `.at(time) -> hour | None` lookup (built once over its
  hours, like today's `ConditionsSnapshot._by_time`), so scoring reads a slot in
  O(1) rather than scanning a tuple. Group hours are kept sorted/uniquely-keyed by
  top-of-hour, matching the current grid.
- Every read of a group's meta or hours guards the `None` group first — e.g.
  `conditions.base.meta.issued_at if conditions.base else None` — so an absent
  source yields the same `None`/floor the flat snapshot produced from a missing
  `*_issued_at`, never an `AttributeError`.
- `optional_term_mean` and the completeness/coverage helpers correlate the base
  group's cloud and the secondary group's seeing by hour timestamp *across* the two
  groups. Seeing stays hourly-held (D3), so the keys align; a slot present in one
  group but not the other is skipped exactly as today's `snapshot.at(slot)` miss is
  skipped. The D4 gappy-coverage golden case locks this.

## Risks / Trade-offs

- **Wide mechanical touch across core, provider, service, and tests** → land the
  D4 golden test first as a safety net, then refactor in small steps each kept
  green; the frozen contract means any output drift is a caught regression, not a
  silent one.
- **Grouping cloud and wind together loses their per-field distinction** → it does
  not: a `BaseHour` stamps `cloud_cover` and `wind_gust` independently, so
  "cloud present, wind absent" (and the reverse) is still expressed. The group is
  the source/issue-time/fetch unit; the field is still the availability unit.
- **Naming collision risk** — the package `pierpressure.conditions` (impure) and
  the module `pierpressure.core.conditions` (pure model) already coexist; the new
  names live in the latter and change no import path, so no new collision.

## Migration Plan

1. Land the D4 golden-output test against current code (captures known-good).
2. Introduce the group model in `core/conditions.py` alongside the old types.
3. Migrate the provider layer to assemble groups; migrate `core` reads and
   `service.py` seam/fallback.
4. Delete `ConditionsSnapshot`/`HourlyConditions` and adapt remaining tests.
5. Delete the discarded attempt (D5).
6. `just check` green, golden unchanged.

Rollback: this is a refactor behind a frozen contract with no schema or data
migration; reverting the change's commits fully restores prior behaviour.

## Open Questions

None that affect the specs, approach, or task breakdown. The seeing-cadence and
richer-cloud questions are deliberately deferred (proposal Non-Goals), not open.
