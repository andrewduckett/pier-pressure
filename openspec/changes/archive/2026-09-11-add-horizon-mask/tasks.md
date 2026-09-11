## 1. Canonical horizon representation (`pierpressure/core/horizon.py`)

- [x] 1.1 Write failing tests for building a `Horizon` from `(az, alt)` samples: samples are sorted by azimuth, each altitude is rounded to the module's fixed precision at construction, equal-rounded duplicate azimuths are dropped, and conflicting-rounded duplicates raise — verify the tests fail (module absent).
- [x] 1.2 Implement the immutable `Horizon` value (sorted samples, altitude rounding at construction, dedup/conflict rules, a defined precision constant) and verify the 1.1 tests pass.
- [x] 1.3 Write failing tests for `alt_at(az)`: an azimuth equal to a sample returns that altitude; between two samples returns their linear interpolation; the wrap arc (greatest az back to least, crossing 360/0) interpolates across the seam; a single-sample horizon returns that constant altitude at every azimuth; an input azimuth of exactly 360 behaves as 0; the returned altitude is rounded to the fixed precision.
- [x] 1.4 Implement `alt_at(az)` (linear interpolation, cyclic wrap, single-sample constant, azimuth normalization, rounded result) and verify the 1.3 tests pass.
- [x] 1.5 Write a failing test then implement the above/below classification (a point is above the horizon when its altitude `>=` `alt_at(az)`, so a grazing point is visible), and verify it passes.

## 2. Horizon sources: floor, default open sky, inline points

- [x] 2.1 Write failing tests then implement builders for a flat `min_altitude` floor (constant altitude everywhere) and the default open sky (flat 0), each expressed as the degenerate single-sample `Horizon`; verify both query flat.
- [x] 2.2 Write failing tests then implement the inline-`points` builder and its validation: unordered pairs are accepted and ordered; azimuth outside 0–360 or altitude outside 0–90 is rejected; azimuth 360 normalizes to 0 with the dedup/conflict rule; at least one pair is required. Verify the tests pass.

## 3. NINA `.hrz` importer and unsupported formats

- [x] 3.1 Commit a real exported NINA `.hrz` file under `tests/fixtures/`; write a failing test that importing it yields a `Horizon` whose queries match the equivalent inline-points horizon. This test pins the actual file format (delimiter, comment token, ordering) — treat any deviation it reveals as the spec of the format.
- [x] 3.2 Write failing tests then implement the NINA text parser (input is file text, not a path): blank lines and `#`-comment lines are ignored; azimuth 360 is normalized to 0 (deduplicated); altitude below 0 is clamped to 0; a line that is neither blank, a comment, nor a parseable pair raises. Verify against the fixture and the edge cases.
- [x] 3.3 Write a failing test then implement the format registry so `stellarium` and `telescopius` are recognized names that raise a clear "format not yet supported" error; verify the message and that no silent open-sky fallback occurs.

## 4. Config integration (`pierpressure/core/config.py`)

- [x] 4.1 Write failing tests for a `PierConfig.horizon` block that is exactly one of `points`, `min_altitude`, or a file reference `{file, format}` (absent → flat 0): configuring more than one source makes the pier invalid, and an invalid horizon invalidates only its own pier while valid piers still load (per-pier isolation). Verify the tests fail.
- [x] 4.2 Implement `PierConfig.horizon` with the mutual-exclusivity and range validation, resolving to canonical samples. Wire `load_config` to pass the config file's directory as Pydantic validation context; a file reference is read and parsed inside per-pier validation so a missing/unreadable/malformed file raises `ValidationError` and reuses the existing `validate_piers` log-and-skip. Verify 4.1 passes.
- [x] 4.3 Write a failing test then verify a relative horizon file path resolves against the config file's directory (not the process working directory) by loading from an unrelated working directory; confirm the file is found.

## 5. Contract and guardrails

- [x] 5.1 Write a test that a verdict produced for a pier with a horizon configured is byte-identical (`to_json()`) to one produced for the same pier, instant, and conditions with no horizon, and that `targets` is empty in both — locking the no-document-change guarantee. Verify it passes.
- [x] 5.2 Verify the pure-core and offline guards still pass unchanged (`tests/test_core_boundary.py`, `tests/test_offline_guard.py`): horizon parsing lives at config load, and `produce_verdict` performs no new I/O.
- [x] 5.3 Run `just check` (ruff lint + format, mypy strict, pytest) and verify it is green.

## 6. Roadmap

- [x] 6.1 In the PR that lands this change, flip milestone M4 status to `done` in `docs/roadmap.md`.
