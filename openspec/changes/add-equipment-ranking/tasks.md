## 1. Equipment config (pier-equipment capability)

- [x] 1.1 Write failing tests for a `Rig` config: a valid rig loads on a pier, and a zero or negative `focal_length_mm`, `sensor_width_mm`, `sensor_height_mm`, or `reducer` raises the repo's config error. Verify the tests fail for the right reason (no `Rig` yet).
- [x] 1.2 Add a `Rig` model to `core/config.py` (`focal_length_mm`, `sensor_width_mm`, `sensor_height_mm`, `reducer=1.0`, each `Field(gt=0.0)`) and an optional `rig: Rig | None = None` on `PierConfig`. Verify 1.1's tests pass and existing config tests are unaffected.
- [x] 1.3 Write failing tests for field-of-view derivation: a known rig yields the expected width/height angles within tolerance, a reducer below 1.0 widens the field, and the result is identical across two calls. Verify they fail (no derivation yet).
- [x] 1.4 Implement the pure FOV derivation (`f_eff = focal * reducer`; `FOV_axis = 2·atan(sensor/(2·f_eff))`, both axes; expose the short edge). Verify 1.3's tests pass.

## 2. Catalog: surface brightness and size

- [x] 2.1 Write a failing parser test: a row with `SurfBr` yields a `surface_brightness`, a blank `SurfBr` yields `None`, and `MajAx` still yields `size_arcmin`. Verify it fails (field not parsed yet).
- [x] 2.2 Parse `SurfBr` in `core/catalog.py` and add `surface_brightness: float | None` to `CatalogObject`; leave the `MAGNITUDE_LIMIT` candidate filter and its role unchanged. Verify 2.1's test passes and the existing catalog tests still pass.

## 3. New ranking sub-scores

- [x] 3.1 Write failing unit tests for the FOV-fit sub-score over `r = size / fov_short`: a speck scores a low floor, the sweet band scores ~1.0, an oversize object decays without a cliff, and the output stays within `[0, 1]`. Verify they fail (no sub-score yet).
- [x] 3.2 Implement `fov_fit` sub-score (framing curve, clamped `[0, 1]`) in `core/ranking.py`. Verify 3.1's tests pass.
- [x] 3.3 Write failing unit tests for the brightness sub-score: a brighter object scores higher on each scale, the surface-brightness path and the integrated-magnitude path each map through their **own** anchors (a mid surface-brightness object is not scored as fainter than a mid magnitude object), and the output stays within `[0, 1]`. Verify they fail.
- [x] 3.4 Implement the `brightness` sub-score with separate per-scale anchors (surface brightness where known, else magnitude), clamped `[0, 1]`. Verify 3.3's tests pass.

## 4. Weight renormalisation over known factors (ADR-0010)

- [x] 4.1 Write failing tests for the six-factor combine: no rig drops FOV (five factors), unknown size drops FOV, unknown brightness drops brightness, both unknown yields geometry-only, the live weights renormalise to sum to 1, and every result stays within `[0, 100]`. Verify they fail (still four fixed weights).
- [x] 4.2 Replace the fixed four-weight `combined_score` with base six-weight scoring that renormalises over the live factors for each `(pier, target)`; add `WEIGHT_BRIGHTNESS` and `WEIGHT_FOV` base constants. Verify 4.1's tests pass.
- [x] 4.3 Round the derived field of view and the pre-scaled renormalised score to a fixed decimal precision before the final integer scaling (design D9), and round the emitted `size_arcmin`/`magnitude`/`surface_brightness` to the document's fixed precision. Verify a test that a score sitting near an integer `.5` boundary is stable under a small epsilon perturbation of a sub-score, and that the emitted numeric fields serialise at the fixed precision.

## 5. Wire ranking to equipment and the document

- [x] 5.1 Thread the pier's rig and each object's `size_arcmin`/`magnitude`/`surface_brightness` through the coarse scan and refinement so `fov_fit` is computed only when a rig is configured and the object has a size, and `brightness` only when a brightness value is known. Verify an integration test ranks a rig-configured pier and a rig-less pier without error.
- [x] 5.2 Add the rig fields to `ranking.py`'s `_cache_key`, and write a test that the same pier and instant with two differently-framing rigs produces different scores or ordering (the target-ranking "A rig change changes the ranking" scenario). Verify the test passes.
- [x] 5.3 Add additive `size_arcmin`, `magnitude`, `surface_brightness` fields to `Target` in `core/model.py` (present always, serialised as `null` when the catalog records none) and populate them in ranking. Verify a serialization test shows all three keys present, `null` when the catalog lacks them, and every existing `Target` field unchanged.
- [x] 5.4 Add equipment-aware `reasons[]` entries (for example well-framed and bright) where the inputs are known. Verify a target with a rig and a size emits the framing reason and output stays deterministic.

## 6. Validation night, goldens, and pinned values

- [x] 6.1 Choose the six base weights and the framing- and brightness-curve anchors on a documented validation night (the method of M5's task 8.2), recording the night and the rationale inline with the constants. Verify the top-ten on that night is defensible — a well-framed bright target ranks as expected, and the recorded reasoning is checked in.
- [x] 6.2 Re-baseline the golden target-list outputs and extend the pinned-value tests to cover the new FOV, brightness, and renormalisation constants (S3). Verify the golden and determinism tests pass byte-identically for the pinned instant.

## 7. Full gate

- [x] 7.1 Confirm the pure-core boundary test still passes: no Home Assistant or MQTT imports enter the new equipment, catalog, or ranking code. Verify the boundary test is green.
- [x] 7.2 Run `just check` (ruff lint + format, mypy strict, pytest) and confirm it is green before opening the PR.
- [x] 7.3 When landing the change, flip `docs/roadmap.md` M6 status to `done` in the same PR. Verify the roadmap reflects the shipped milestone.
