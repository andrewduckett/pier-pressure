## 1. Scaffold & toolchain (design D1, D10)

- [x] 1.1 Create `pyproject.toml` (`[project]` with `requires-python >=3.12` and deps `pydantic>=2`, `paho-mqtt>=2`, `PyYAML`; dev deps `pytest`, `ruff`, `mypy`, `pre-commit`, `jsonschema`; `[tool.ruff]` and `[tool.mypy]` config) and `.python-version` pinned to 3.12. Verify `uv sync` succeeds and produces `uv.lock`.
- [x] 1.2 Create the package skeleton per D1 (`pierpressure/core/`, `pierpressure/delivery/`, `pierpressure/service.py`, `pierpressure/__main__.py`, `tests/`), with `core` importing nothing from `delivery`. Verify `uv run python -c "import pierpressure"` succeeds and a test asserts `pierpressure.core` has no `delivery` import.
- [x] 1.3 Create `Justfile` with recipes `install`, `lint`, `format`, `typecheck`, `test`, `run`, `check`. Verify `just --list` shows them and `just lint` runs ruff clean on the skeleton.
- [x] 1.4 Create `.gitignore` (Python, `.venv`, uv caches). Verify it ignores `.venv/` and `__pycache__/`.

## 2. Core: verdict document model (spec night-verdict; design D2, D3)

- [x] 2.1 Implement the verdict-document Pydantic models: `verdict` enum (GO/MAYBE/NO-GO), `score` (int 0–100 or null), `confidence {band: LOW/MEDIUM/HIGH, value: 0–100}`, `reasons` (list), `targets` (list), `dark_window {start,end}`, `pier`, `generated_at`; enforce fixed key order, tz-aware UTC (reject naive datetimes), and every key always emitted (null, never omitted). Verify a unit test serializes a gated NO-GO doc and asserts `score` is present-and-null, keys are in fixed order, `generated_at` ends with `Z`.
- [x] 2.2 Implement the `Clock` protocol with `SystemClock` (`datetime.now(timezone.utc)`) and `FixedClock(instant)`. Verify a unit test that `FixedClock` returns the pinned instant and `SystemClock` returns a tz-aware UTC datetime.
- [x] 2.3 Enforce field bounds via the model (score 0–100, confidence.value 0–100, band/verdict enums). Verify unit tests that out-of-range score/value and unknown enum values are rejected.

## 3. Core: configuration (spec night-verdict "Pier configuration validation"; design D8)

- [x] 3.1 Implement YAML config loading for `mqtt` (host/port/username/password with `${ENV}` override), `recompute.interval_seconds`, and `piers` (list of id/latitude/longitude/elevation_m) with range validation (lat -90..90, lon -180..180). Verify unit tests: a valid single-pier config is accepted; a config missing a field or out of range is rejected with a configuration error and yields no verdict.
- [x] 3.2 Implement per-pier validation isolation: each pier validated independently; an invalid pier is reported (logged) and skipped, valid piers continue; zero valid piers is a hard failure that exits non-zero. Verify unit tests matching the two multi-pier scenarios (one-invalid-among-valid; no-valid-pier).

## 4. Core: stub producer (spec night-verdict "Deterministic emission"; design D4)

- [x] 4.1 Implement `produce_verdict(pier, clock)` returning the M1 stub document (`verdict=MAYBE`, `score=50`, `confidence={LOW,0}`, one reason naming it a skeleton, `targets=[]`, `dark_window={null,null}`, `generated_at=clock.now()`). Verify a golden/determinism test: producing twice with the same pier and a `FixedClock` yields byte-identical documents and `generated_at` equals the pinned instant.
- [x] 4.2 Verify the producer rejects an invalid pier (config error, no document) via a unit test, keeping producer errors distinct from delivery errors (design D9).

## 5. Delivery: MQTT discovery & payloads (spec ha-delivery; design D5, D6)

- [x] 5.1 Implement discovery-payload builders for the verdict sensor, score sensor, and refresh button: shared `device` block per pier, `unique_id`/topics derived from the pier id, `has_entity_name: true`, availability referencing the LWT topic; for the score entity add an `availability_template` requiring non-null score with `availability_mode: all`. Verify a unit test validates each payload against Home Assistant's MQTT-discovery JSON schema (via `jsonschema`) and asserts stable unique_ids/topics on repeat builds (no duplicates).
- [x] 5.2 Implement state/attributes publishing: verdict state topic carries the verdict value; attributes topic carries the JSON document (reasons, score, confidence, dark_window, pier, generated_at); publish discovery, state, attributes, and availability with `retain=true`. Verify a fake-MQTT-client unit test asserts exact topics, retain flags, and that published verdict/score/confidence/reasons match the input document; and that a null-score doc publishes `score: null` in attributes.
- [x] 5.3 Implement availability: publish a retained `online` on connect and register a retained `offline` Last-Will (`will_set`) on the availability topic. Verify a unit test asserts the will is registered with the offline payload and retain flag, and the online message is published retained.
- [x] 5.4 Implement delivery failure handling: broker connect/publish failures are raised/reported, never reported as success (design D9). Verify a unit test that an unreachable broker produces a reported delivery failure.

## 6. Delivery: persistent service loop (spec ha-delivery "Persistent…", "On-demand refresh"; design D7)

- [x] 6.1 Implement the loop with a thread-safe `queue.Queue`: the paho callback (network thread) parses the pier id from the refresh command topic and enqueues it; the main thread waits `queue.get(timeout=max(0.0, deadline - time.monotonic()))` against an absolute monotonic deadline. Verify a unit test (fake clock/queue) that frequent refreshes do NOT reset the deadline and the periodic all-pier recompute still fires — i.e. no starvation.
- [x] 6.2 On a dequeued pier id, recompute+publish that pier only (deadline unchanged); on `queue.Empty`/deadline, recompute+publish all piers and reset the deadline; publish all piers once on startup. Verify unit tests: a refresh republishes exactly the target pier; the interval recompute republishes all piers with later `generated_at`.
- [x] 6.3 Drain/dedupe pending refreshes: collapse duplicate queued pier ids into a single recompute per iteration (round-3 suggestion). Verify a unit test that N identical queued refreshes result in one recompute for that pier.
- [x] 6.4 Subscribe to each pier's refresh command topic and confirm a command triggers an immediate republish with a current timestamp. Verify a unit test that a message on the refresh topic republishes with `generated_at` at/after the command time.

## 7. Entry point & container (design D9, D10)

- [x] 7.1 Implement `python -m pierpressure`: load config, connect to the broker, publish on startup, run the loop; exit non-zero on an unrecoverable startup failure (e.g. broker unreachable at boot). Verify a smoke test against a fake broker that startup publishes a verdict for the configured pier.
- [x] 7.2 Write the uv-based `Dockerfile` (install deps with uv, slim runtime layer running `python -m pierpressure`). Verify `docker build` succeeds and the built image's entrypoint is the module.

## 8. CI, hooks & docs (design D10, D11; Migration Plan)

- [x] 8.1 Create `.pre-commit-config.yaml` running `ruff check`, `ruff format`, and `mypy`. Verify `uv run pre-commit validate-config` passes (hook install happens once the repo is git-initialized).
- [x] 8.2 Create `.github/workflows/ci.yml` running `just check` on push/PR. Verify the workflow YAML parses and invokes `just check` (activates once the repo is pushed to GitHub).
- [x] 8.3 Write `README.md`: config example, the `${ENV}` password override, the MQTT entity list, an HA automation snippet that notifies when the verdict is not NO-GO at a chosen time, and the entity-removal procedure (publish empty retained payloads to the discovery topics). Verify the README contains each of these sections.
- [x] 8.4 Write the M1 manual HA acceptance checklist (design D11): the three entities appear under one device, verdict/score/confidence render, the refresh button republishes, a gated NO-GO shows score unavailable, and killing the container flips entities to unavailable. Verify the checklist file exists with these items.
- [x] 8.5 (Optional) Add an opt-in integration test marker exercising a real local broker (publish/subscribe + LWT). Verify it is skipped by default so `just test` is green on a machine with no broker.

## 9. Final verification

- [x] 9.1 Run `just check` (lint + typecheck + full pytest) and confirm it passes green.
- [x] 9.2 Deploy the container against the real HAOS broker and complete the manual HA acceptance checklist (8.4), recording the result — this is the end-to-end proof the walking skeleton exists.
