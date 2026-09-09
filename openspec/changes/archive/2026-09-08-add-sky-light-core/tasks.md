## 1. Dependencies and offline-guard scaffolding

- [x] 1.1 Add `skyfield` and a version-pinned ephemeris to the project (preferred: ephemeris as a lockfile-pinned dependency loadable from its installed path; fallback: a `just fetch-ephemeris` task with a SHA-256 checksum — see design D2). Update `pyproject.toml` and `uv.lock`. Verify `uv sync` succeeds and a throwaway script loads the ephemeris and `load.timescale(builtin=True)` from local data with no network.
- [x] 1.2 Add a pytest offline-guard helper that patches socket creation to raise on any network attempt. Verify (a) a test that deliberately opens a socket under the guard fails, and (b) importing Skyfield + loading the pinned ephemeris/timescale under the guard succeeds.

## 2. Verdict-document contract (`core/model.py`)

- [x] 2.1 Add a `MoonPhase` `StrEnum` with the eight standard phases (new, waxing crescent, first quarter, waxing gibbous, full, waning gibbous, last quarter, waning crescent). Verify a unit test asserts the exact set of values and their string forms.
- [x] 2.2 Normalize precision at validation (design D3): in the shared datetime field-validator also apply `.replace(microsecond=0)`, and change `_iso_z` to `isoformat(timespec="seconds")`; round the illuminated fraction to 2 dp via an `AfterValidator`. Verify unit tests that (a) a datetime with microseconds is stored and serialized at whole-second precision, (b) `generated_at` from a microsecond-bearing instant round-trips (`doc == model_validate(doc.to_json())`), and (c) existing M1 model tests still pass.
- [x] 2.3 Add the `Moon` pydantic model (`illumination: float` 0–1 @2dp; `phase: MoonPhase`; `up_during_dark: bool | None`; `rise`/`set`: `datetime | None`) with `rise`/`set` carrying the same aware-UTC + `microsecond=0` validator as `DarkWindow`, and add the `moon` field to `VerdictDocument`. Verify unit tests for field presence, bounds, null handling, timestamp normalization, and JSON round-trip equality.

## 3. Sky engine (`core/sky.py`) — pure, offline, deterministic

- [x] 3.1 (Test first) Write `dark_window(pier, instant)` tests for pinned site/instant pairs covering: a normal mid-latitude night (start<end, correct dusk/dawn); instant already within night selects the current night (end = first dawn at/after instant); continuous non-night → `(None, None)`; continuous astronomical night → non-null window anchored to the local solar day and stable across two instants in the same period; a grazing sub-second night collapsing to `start>=end` → `(None, None)`; and the `abs(latitude)==90` pole fallback to the UTC-day anchor. Then implement `dark_window`. Verify all tests pass under the offline guard.
- [x] 3.2 (Test first) Write `moon_info(pier, dark_window, instant)` tests covering: illumination in [0,1] @2dp; phase-octant mapping including the 0°/360° new-moon wrap and negative-difference `mod 360`; `up_during_dark` true/false against a known window; `rise`/`set` non-null only within the window and using the geometric-centre-at-0° threshold; and all across-window fields null when `dark_window` is null (illumination/phase still present). Then implement `moon_info`. Verify all tests pass under the offline guard.

## 4. Producer wiring (`core/producer.py`)

- [x] 4.1 Replace the stubbed `dark_window`/`moon` in `produce_verdict` with calls into `core/sky.py`, keeping `verdict`/`score`/`confidence`/`targets` as the existing M1 stubs and preserving the signature and document key order. Verify a producer test asserts a real `dark_window` and `moon` for a pinned site/instant and that the module boundary test (core imports no delivery) still passes.

## 5. Determinism, offline, and CI verification

- [x] 5.1 Add determinism tests: two `produce_verdict` runs with the same pier and pinned instant yield byte-identical `to_json()` (including `generated_at`, `dark_window`, and `moon`), and the whole `produce_verdict` call runs under the offline guard with no network access. Verify these tests pass.
- [x] 5.2 Run `just check` (ruff lint + format check, mypy, pytest with integration deselected) and confirm it is green locally — the CI gate. Verify by capturing passing output.

## 6. Packaging and docs

- [x] 6.1 If the build-time ephemeris route (fallback) is used, wire `just fetch-ephemeris` (with checksum) into both the Docker build and local dev setup, and confirm the container runs fully offline. Verify a clean `just install` + fetch + `uv run python -m pierpressure` against a config produces a document with a real `dark_window`/`moon` and no network egress. (Skip if the ephemeris is a locked dependency.)
- [x] 6.2 Update the README's verdict-document / MQTT-attributes section to document the new `moon` object and the now-real `dark_window` (including the null cases). Verify the README describes every field the document now emits.
