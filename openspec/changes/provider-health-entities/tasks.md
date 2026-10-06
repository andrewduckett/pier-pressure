Practice TDD: write the failing test first, then change the code. `just check` (ruff
lint, mypy strict, pytest) is the CI gate and must be green before the PR is marked
ready. Every golden verdict must stay byte-identical; no task regenerates a golden
file.

## 1. Health types and the fold rule

- [x] 1.1 Create `pierpressure/health.py` with frozen dataclasses `FetchOutcome` (provider key, display name, role, fetch time, ok flag, error, issue time) and `ProviderHealth` (provider key, display name, role, tracking start, latest status, latest fetch time, latest error, last success, issue time), plus `ProviderHealth.empty(...)` for a provider with no history. Verify with a test in `tests/test_health.py` that an empty record has null status, fetch time, error, last success, and issue time (design D2).
- [x] 1.2 Write tests for `fold(previous, outcome)` first: a success sets last success and issue time and clears the error; a failure keeps the earlier last success and issue time and sets the error; a success with no issue time gives a null issue time; every outcome replaces the latest status and fetch time. Then implement `fold` and verify the tests pass (design D2; spec "A failed fetch keeps the earlier success").
- [x] 1.3 Write tests for `describe_error(exc)` first: an `httpx.HTTPStatusError` for 503 gives `HTTPStatusError: 503 Service Unavailable`; a 503 whose server reason phrase contains the pier's latitude gives the standard phrase and no latitude; an unknown status code gives no phrase; a `ConnectError` whose message holds the request URL gives `ConnectError` only; a `ValueError` whose message holds a latitude gives `ValueError` only. Then implement it from an allowlist using `http.HTTPStatus`, and verify the tests pass (design D6; conditions spec error scenarios).
- [x] 1.4 Verify that `tests/test_core_boundary.py` still passes, so nothing in `pierpressure/core/` imports `pierpressure.health`.

## 2. Fetch outcomes from the conditions provider

- [x] 2.1 Give each source provider a provider key and display name (`open_meteo` / "Open-Meteo", `seven_timer` / "7Timer!") and add `key` and `name` to the conditions `Provider` protocol. Verify with a test that `build_provider()` exposes both providers' key, display name, and role (design D3).
- [x] 2.2 Write tests first in `tests/test_conditions_provider.py`: `CompositeProvider.get` returns a `FetchResult` holding the same `Conditions` as before and one `FetchOutcome` per provider; a raising source gives a failed outcome with `describe_error` text; an empty forecast gives a failed outcome with error `no readings returned`; readings with blank fields give a successful outcome. Inject a fixed `now` so fetch times are exact. Verify the tests fail (design D1; conditions spec scenarios).
- [x] 2.3 Change `_safe_fetch` to return the forecast and its `FetchOutcome`, and `get` to return `FetchResult`. Add an injectable `now` to `CompositeProvider` and `build_provider()`. Keep the full exception text in the existing warning log. Verify that the tests from 2.2 and every existing provider test pass.

## 3. Delivery

- [x] 3.1 Add `device_class` and `entity_category` (`diagnostic` or `config`) to `SENSOR_SCHEMA` in `pierpressure/delivery/ha_schema.py`. Verify that `tests/test_discovery.py` still passes.
- [x] 3.2 Write tests first for the health discovery builder: topic `P/sensor/pierpressure_<pier>/<provider>_health/config`, unique identity `pierpressure_<pier>_<provider>_health`, name "<display name> health", `device_class: timestamp`, `entity_category: diagnostic`, availability from the last-will topic only, and a payload that validates against `SENSOR_SCHEMA`. Then implement it in `pierpressure/delivery/mqtt.py` and verify the tests pass (design D5; spec "Health discovery is published per provider").
- [x] 3.3 Write tests first for the health state and attributes: the state is the last success in ISO 8601 with offset, or the literal `None`; the attributes carry provider, role, `tracking_since`, `status`, `last_fetch`, `last_error`, and `issued_at`, with nulls as the spec lists. Then implement them and verify the tests pass (spec "A successful fetch sets the last-success time").
- [x] 3.4 Add `MqttDelivery.publish_health(pier_id, healths)`, which publishes discovery, state, and attributes for each record, all retained. Verify with the fake client that every message is retained and that `publish_verdict` output is unchanged (spec "Existing entities and the verdict document are unchanged").
- [x] 3.5 Split `MqttDelivery.connect()` so it registers the last-will message and connects but no longer publishes `online`. Add `go_online()`, which publishes the retained `online` message. Update `tests/test_publish.py` (including the publish-failure test that relied on `online` inside `connect()`), `tests/test_main.py`, and any other test that expects `online` from `connect()`. Verify they pass (design D4).

## 4. Service wiring

- [x] 4.1 Write tests first in `tests/test_service.py` for startup order: with a fixed clock, `run()` publishes every pier's empty health (with `tracking_since` set to the clock time) before it calls `go_online()`, and calls `go_online()` before the first fetch. Verify the test fails (spec "Startup clears retained health before going online").
- [x] 4.2 Write a test first: when the startup health publish raises `DeliveryError`, `run()` raises and never calls `go_online()` or fetches. Verify it fails (spec "A failed startup reset does not go online").
- [x] 4.3 Write tests first for steady state: after each fetch the service folds that pier's outcomes and calls `publish_health` right after `publish_verdict`; a failure after an earlier success publishes the earlier last success; health is kept per pier, so one pier's failure does not change another pier's health. Verify they fail.
- [x] 4.4 Change the service: `ConditionsProvider` returns `FetchResult`; the service takes the configured providers and seeds health per pier; `run()` records `tracking_since`, publishes the reset, calls `go_online()`, then runs as before. The default no-conditions provider reports no providers, so no health is published and `run()` goes online at once. Add a small test helper that wraps bare `Conditions` for existing stubs. Verify that 4.1 to 4.3 and every existing service test pass (design D3, D4).
- [x] 4.5 Wire `__main__.py`: build the provider with the service clock's `now`, and pass its providers to the service. Verify with `tests/test_main.py` and `tests/test_integration.py`.
- [x] 4.6 Write a test that two verdicts produced from the same pier, instant, and snapshot, with different fetch outcomes, are byte-identical. Verify it passes, and that `tests/test_golden_verdict.py` and `tests/test_determinism.py` pass with no golden regenerated (conditions spec "Outcomes do not change the verdict").

## 5. README

- [x] 5.1 Add a "Watching provider health" section to `README.md`: what each health sensor and attribute means; that Open-Meteo's issue time and last success come from the same fetch; and the example automation from design D7, with a template trigger and a Home Assistant start trigger that share one condition, measuring unknown age from `tracking_since`. Tell readers to copy it for 7Timer! and to set the threshold to several recompute intervals. Verify that `tests/test_docs.py` passes.
- [x] 5.2 Add both health discovery topics to the "Removing the entities" loop in `README.md`, and add the health topics to the topic table in the `pierpressure/delivery/mqtt.py` module docstring. Verify by reading the diff.

## 6. Gate and manual check

- [ ] 6.1 Run `just check` and verify that ruff, mypy, and pytest are all green.
- [ ] 6.2 Run the five checks in design.md "Manual check in Home Assistant" against a real instance, and record the results in the PR. If check 3 fails, apply the fallback the design names and re-run the check.
