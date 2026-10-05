## Context

See proposal.md — Why. The requirements are in `specs/conditions/spec.md`.

Today `build_provider()` in `pierpressure/conditions/provider.py` wraps each source
in a `CachingProvider`, then hands both to a `CompositeProvider`. `__main__.py`
builds this stack once and shares it across every pier.

`CompositeProvider._safe_fetch` already turns any exception into an empty
`SourceForecast`. `assemble_snapshot` already turns an empty forecast into a `None`
group. The core already reads a `None` group as "this source's fields are
unavailable". So the path a failed fetch needs already exists. The cache only sits
in front of it.

The core never sees the cache. It receives a snapshot with an issue time per source,
and its freshness term in confidence decays with that age. The decay runs from 1
hour to 12 hours (`_F_FRESH_HOURS`, `_F_STALE_HOURS` in `pierpressure/core/scoring.py`).
A comment ties the 12-hour point to the cache's `MAX_STALENESS`.

## Goals / Non-Goals

**Goals:**

- Remove the cache with no change to the core's logic or to any verdict computed
  from a given snapshot.
- Prove that with the existing golden verdict tests, byte for byte.

**Non-Goals:**

- Changing how `_safe_fetch` logs or classifies errors. Provider health (#25) will
  build on it.
- Changing when or how often the service fetches.

## Decisions

### D1 — Delete the cache rather than disable it

Remove `CachingProvider` and `MAX_STALENESS`. `build_provider()` passes
`OpenMeteoProvider()` and `SevenTimerProvider()` straight to `CompositeProvider`.

- **Alternative considered:** keep the class and set `max_staleness` to zero. That
  leaves dead code with no caller and a constant with no meaning. It also keeps the
  shared-slot bug one config change away. Deleting it is simpler.

### D2 — Keep the freshness term and its 12-hour stale point

The freshness term stays as it is. Without the cache it still measures something
real: how old each source's data was when it was issued. That matters for 7Timer!,
whose issue time is its model run. Only the comment changes. It will describe the
12-hour point as the age at which data reaches the freshness floor, with no link to
a cache.

- **Alternative considered:** drop the freshness term now that the cache is gone.
  That would change confidence for 7Timer! data and every golden verdict. It is a
  tuning change with its own evidence to gather, so it stays out of this change.

### D3 — Build the stale golden case directly, and rename it

The `over_stale_cache` golden case builds an 11-hour-old base forecast by priming a
`CachingProvider` and then failing it. The core only sees an old issue time. So the
case builds the same forecast directly with `_base_full(issued_at=_STALE_ISSUED)`.

The case is renamed `stale_issued_base`, because no cache is involved any more. Its
two golden files move with `git mv`, with their contents unchanged:

```
tests/fixtures/golden/expected/over_stale_cache.json --> stale_issued_base.json
tests/fixtures/golden/stub/over_stale_cache.json     --> stale_issued_base.json
```

The `stub/` copy is read by `tests/test_producer_targets.py`. If both files pass
unchanged under the new name, the core's output did not change.

- **Alternative considered:** keep the old name. That keeps the diff smaller, but a
  case named after a cache that no longer exists misleads the next reader.

### D4 — Edit ADR 0005 in place

ADR 0005 records the provider-edge seam, and that decision still holds. Only its
mention of caching becomes untrue. The change removes "caching" from the Decision
paragraph and replaces the consequence "A provider outage is buffered by cache".
The new text says an outage shows as missing data and lower confidence, not a crash.
A dated note at the end names this change and says why.

- **Alternative considered:** a new ADR that supersedes part of 0005. The ADR
  template only supports superseding a whole ADR. A second ADR for one sentence adds
  more to read than it explains. The user chose to edit in place.

### D5 — No retry

A failed fetch is not retried within the same recompute. The source stays
unavailable until the next recompute. #38 tracks a possible retry, once the health
sensors in #25 show how often one-off failures happen.

## Risks / Trade-offs

- [A one-off network error now drops the verdict to `MAYBE` until the next
  recompute] → This is the intended, honest behaviour. The PR description calls it
  out so it reaches the release notes. #25 makes the failure visible, and #38 can
  add a retry if failures prove common.
- [Another file still mentions the conditions cache after the change] → A task
  searches the repo for the cache terms and checks each hit. Mentions of the
  explainer's own cache are a different thing and stay.

## Migration Plan

No data or configuration migrates. The cache lived only in memory, so a deploy
simply starts without it. To roll back, revert the change's commits.
