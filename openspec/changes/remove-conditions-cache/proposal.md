## Why

Issue #37. When a weather fetch fails, PierPressure reuses the last good forecast for
up to 12 hours. That hides a broken source for half a day, and a 12-hour-old cloud
forecast is no more useful than none. Worse, every pier shares one cache slot per
source. So with two piers, a failed fetch for one pier can use the other pier's
weather. Removing the cache makes a failure show at once, through the
missing-data rules the verdict already has.

## What Changes

- **BREAKING (behaviour):** a failed or empty fetch leaves that source's data
  unavailable until the next successful fetch. The system no longer reuses data from
  an earlier fetch. When Open-Meteo fails on a night with a dark window, the verdict
  becomes `MAYBE` with score 0 and "conditions unavailable" until it recovers. When 7Timer! fails, seeing and
  transparency drop out and confidence falls. The verdict document's shape and the
  delivery surface do not change.
- Remove `CachingProvider` and `MAX_STALENESS` from the conditions provider layer.
  Each source's provider feeds `CompositeProvider` directly.
- Remove the `conditions` requirement "Caching tolerates transient outages". Its
  forecast-horizon rule is not about caching, so it moves to the per-field
  availability requirement.
- Reword the durable constraint from "caching and graceful fallback" to "graceful
  fallback" wherever it is written down.
- Edit ADR 0005 in place. Remove the cache from its decision and consequences, and
  add a dated note that says why.
- Keep the freshness term in confidence unchanged. It reads only the base source's
  issue time. Without the cache that is always the fetch time, so the term stays at
  full strength in practice. A missing 7Timer! still lowers confidence, through the
  completeness term rather than freshness. Removing or retuning freshness is a
  separate change.

Out of scope:

- Retrying a failed fetch (#38).
- Retuning the confidence curve.
- Changing what Open-Meteo reports as its issue time.
- Provider health sensors (#25).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `conditions`: remove the caching requirement. Say that a failed fetch leaves its
  source unavailable rather than filled from an earlier fetch. Move the
  forecast-horizon rule into per-field availability. Drop the "reused after a failed
  refresh" clause from the issue-time requirement.

## Impact

- **Code:** `pierpressure/conditions/provider.py` and
  `pierpressure/conditions/__init__.py` lose `CachingProvider` and `MAX_STALENESS`.
  `pierpressure/core/` changes only in comments that tie the freshness curve to the
  cache.
- **Tests:** the cache tests in `tests/test_conditions_provider.py` and the
  staleness constant test in `tests/test_tuning_constants.py` go.
  `tests/test_golden_verdict.py` builds its stale case without the cache. Every
  golden verdict stays byte-identical, because the core does not change.
- **Docs:** `AGENTS.md`, `openspec/config.yaml`, `openspec/prd.md`,
  `openspec/discovery.md`, `README.md`, and ADR 0005. ADR 0006 also mentions
  caching, but it is deprecated, so it stays as written.
- **Users:** a short outage now shows in the verdict instead of being hidden. Users
  who notify on verdict changes may see a `MAYBE` and then a recovery.
- **Dependencies:** none.
