Practice TDD: for each behavior, write the failing test first, then implement.
`just check` (ruff lint + format, mypy strict, pytest) is the CI gate and must be
green before the PR.

## 1. Vendor the OpenNGC catalog

- [x] 1.1 Commit the upstream OpenNGC data file(s) (main plus addendum) under a data directory packaged with the wheel, unmodified, and verify the committed bytes match the upstream release (record the version/commit in a NOTICE).
- [x] 1.2 Add the OpenNGC license and attribution (CC-BY-SA-4.0) to the repo, and verify share-alike compatibility with the repo's own license before merge; verify a NOTICE names the source and version.
- [x] 1.3 Configure packaging (hatch) to include the data file(s) in the wheel, and verify a built wheel contains them.

## 2. Catalog loader (core/catalog.py)

- [x] 2.1 Write failing tests for parsing OpenNGC rows: sexagesimal J2000 RA/Dec to hours/degrees, object type, magnitude and size (blank magnitude allowed), against real committed rows including the addendum.
- [x] 2.2 Implement the parser and verify the parsing tests pass.
- [x] 2.3 Write failing tests for eligibility filtering: keep galaxies/nebulae/clusters, drop stars/duplicates/non-existent, exclude objects fainter than the magnitude cutoff, keep unknown-magnitude objects. Implement the filter and verify the tests pass.
- [x] 2.4 Implement a cached, offline loader mirroring the ephemeris loader in `core/sky.py`, and verify a test that the catalog loads with no network and that two loads yield an identical object set and coordinates (determinism).

## 3. Target contract (core/model.py)

- [x] 3.1 Write failing tests for a `Target` model with `id`, `name` (nullable), `type`, `score` (0-100), `window {start, end}`, `max_altitude`, `transit_time`, `moon_separation`, including whole-second UTC times and fixed rounding, and a serialize/round-trip test.
- [x] 3.2 Implement `Target` and change `VerdictDocument.targets` from `list[str]` to `list[Target]`; verify the model tests pass and JSON key order is stable.

## 4. Ranking engine

- [x] 4.1 Write failing tests for per-target geometry: observable window (above mask AND astronomical night, clamped to dusk/dawn), max altitude and its instant, `transit_time` via meridian-transit finding (including a circumpolar daytime transit), and moon separation at the max-altitude instant within the window.
- [x] 4.2 Implement the geometry (reusing `core/sky.py` and `horizon.is_above`) and verify the geometry tests pass, including the circumpolar clamped-window case completing without error.
- [x] 4.3 Write failing tests for the four sub-scores (altitude `sin(alt)`, window fraction, moon coupling with the per-instant moon-up check, transit centering) and the weighted 0-100 score. Implement and verify.
- [x] 4.4 Write failing tests for the gates: an object never above the mask is absent, a sub-minimum-duration object is absent, and every emitted target's window meets the minimum. Implement gating and verify.
- [x] 4.5 Implement the pipeline — coarse grid scan over ~14k candidates, top-10 by score with `id` tie-break, then score-ordered refine walk (root-find window edges and transit, re-gate on the exact window, promote until 10 pass). Verify a test that all emitted targets are refined and gate-satisfying.
- [x] 4.6 Verify a determinism test: the same `(pier, instant)` yields a byte-identical target list; and an empty list when the selected night has no dark window.
- [x] 4.7 Add the per-night ranking cache keyed by `(pier, selected night)` and verify a test that two recomputes within one night produce identical lists and reuse the cache.

## 5. Producer integration

- [x] 5.1 Fill `targets` from the ranking in `produce_verdict`, and verify a test that only `targets` changes: assert `verdict`, `score`, `confidence`, `reasons`, `dark_window`, and `moon` are byte-identical to the prior stubbed output for the same inputs.
- [x] 5.2 Regenerate all golden-output fixtures and verify the golden test passes with populated `targets` and unchanged other fields.

## 6. Delivery: top-target sensor

- [x] 6.1 Write failing tests for a top-target MQTT-discovery sensor: state is the top target's name (id when no common name), attributes carry the ordered list and top target's fields, discovery payload validates against HA's sensor schema, retained, identity derived from the pier id.
- [x] 6.2 Implement the sensor in `delivery/mqtt.py` / `delivery/ha_schema.py` and verify the tests pass, including unavailability when the target list is empty and no change to the existing verdict/score/refresh entities.

## 7. End-user documentation

- [x] 7.1 Write plain-language (ISO 24495) end-user documentation of target ranking (README section or `docs/` page): what the targets are and each field's meaning, how ranking works in plain terms (the four factors), why an object may be absent (too faint, never clears the horizon, up too briefly), and how it appears in Home Assistant. Verify the doc exists and covers each point.

## 8. Roadmap, tuning, and final gate

- [x] 8.1 Update `docs/roadmap.md` M5 to record that equipment/FOV-fit is deferred (with magnitude as a candidate filter only this milestone), and flip M5 status to done in the landing PR. Verify the roadmap reflects the shipped scope.
- [x] 8.2 Validate the default sub-score weights against a known night (for example, that a well-placed autumn target such as M31 ranks sensibly), adjust if needed, and record the chosen weights. Verify the ranking output is reasonable on the sample night.
- [x] 8.3 Verify `just check` is green (ruff lint + format, mypy strict, pytest), the core/delivery boundary test still passes (no HA/MQTT imports in the core, including `core/catalog.py`), and the full pipeline runs offline.
