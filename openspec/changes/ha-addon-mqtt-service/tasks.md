Practice TDD: write the failing test first, then change the code. `just check` (ruff
lint, mypy strict, pytest) is the CI gate and must be green before the PR is marked
ready. No golden verdict file changes, and the verdict document is untouched.

## 1. Split config loading in the core

- [x] 1.1 Write tests first in `tests/test_config.py` for `read_config(path)`: it returns the raw config and the folder that holds the file; it reports that the file names a broker host when `mqtt.host` is set, and not when the `mqtt:` block or its `host` is missing; it raises `ConfigError` telling the user to set `mqtt.host` when the file sets `mqtt.port`, `mqtt.username` or `mqtt.password` without it. Verify the tests fail (design D2; spec "Credentials without a host are rejected").
- [x] 1.2 Write tests first for `build_config(read, broker=None)`: with a file host, the file's host, port, username and password win and any `broker` is ignored; with no host and a `broker`, all four come from the broker and `discovery_prefix` and `base_topic` keep the file's values or defaults; a file with no `mqtt:` block works with a `broker`; with no host and no `broker`, the error matches today's missing-host error. Verify the tests fail (spec "The add-on uses the Supervisor's MQTT broker when the file names none").
- [x] 1.3 Implement `read_config` and `build_config` in `pierpressure/core/config.py`, and keep `load_config(path)` as `build_config(read_config(path))`. Verify that 1.1 and 1.2 pass, and that `tests/test_config.py`, `tests/test_horizon_config.py` (including the relative horizon file test, unchanged) and `tests/test_explainer_config.py` pass.
- [x] 1.4 Verify that `tests/test_core_boundary.py` passes, so `pierpressure/core/` still imports nothing that reaches the network.

## 2. Supervisor client

- [x] 2.1 Write tests first in `tests/test_supervisor.py`, using `httpx.MockTransport`, a fake monotonic clock and a fake sleep: a 200 response returns host, port, username and password; it sends `Authorization: Bearer <token>` to `http://supervisor/services/mqtt`; a missing username or password comes back as `None`. Verify the tests fail (design D3).
- [x] 2.2 Write tests first for the wait: HTTP 400, 404 and 5xx responses, a connection error, a timeout, a body that is not JSON, and a body with no host or port all retry; a later success returns the broker; no request starts later than 60 seconds after the first; the last pause is shortened so it does not end past that point; after the last failed request, the error says no MQTT broker was found and names both fixes; the first miss logs one line. Verify the tests fail (design D4; spec "The add-on waits a bounded time for the Supervisor's broker").
- [x] 2.3 Write tests first for immediate failures: HTTP 401 and 403 fail at once with the "access refused" message and no retry; `ssl: true` fails at once with the TLS message; a `protocol` other than `3.1.1` fails at once with a message naming it; a missing `protocol` counts as `3.1.1`. Verify the tests fail (design D4, D5).
- [x] 2.4 Write a test first that the production client is built with `trust_env=False`: with `HTTP_PROXY` and `ALL_PROXY` set, the request still goes straight to the Supervisor. Verify it fails (spec "Proxy settings do not reach the token").
- [x] 2.5 Implement `pierpressure/supervisor.py` with a 5-second `httpx` timeout per request. Verify that 2.1 to 2.4 pass, and that no error message or log line in those tests contains the password or the token.

## 3. Entry point and add-on config

- [x] 3.1 Write tests first in `tests/test_main.py`: with `SUPERVISOR_TOKEN` set and no `mqtt.host` in the file, `main` asks the Supervisor and connects to its broker; with a file host, it never asks; without `SUPERVISOR_TOKEN`, it never asks and the missing-host error is unchanged; a Supervisor failure logs a "Configuration error" and returns 1. Verify the tests fail (design D1, D2; spec "Outside an add-on, nothing changes").
- [x] 3.2 Write a test first that `main` logs the broker's source and `host:port` for both sources, and that the log never contains the password. Verify it fails (design D6; spec "The log names the broker's source without the password").
- [x] 3.3 Wire `pierpressure/__main__.py`: run `read_config`, ask the Supervisor only when `SUPERVISOR_TOKEN` is set and the file names no host, then run `build_config` and log the source. Verify that 3.1, 3.2 and every existing `tests/test_main.py` and `tests/test_integration.py` test pass.
- [x] 3.4 Write a test first in `tests/test_ha_addon.py` that the add-on config's `services` list contains `mqtt:want`, then add it to `ha-addon/config.yaml`. Verify that the test and every existing add-on test pass (spec "Add-on config declares the service").

## 4. Documentation

- [x] 4.1 Update `ha-addon/DOCS.md`: with the Mosquitto broker add-on, leave the `mqtt:` connection settings out and the add-on uses the Supervisor's broker; setting `mqtt.host` uses the file's settings instead, all four together; what each startup error means. Replace the minimal example and the "Write the password into the file" section to match. Verify by reading the diff.
- [x] 4.2 Update the add-on section of `README.md` the same way, in fewer words, and link to the add-on docs for details. Verify that `tests/test_docs.py` passes and by reading the diff.

## 5. Verify and archive

- [x] 5.1 Run `just check` and verify it is green.
- [ ] 5.2 After a release with this change, install that version of the add-on on a Home Assistant OS instance running the Mosquitto add-on, with a `config.yaml` that has no `mqtt:` block. Verify that the log names `core-mosquitto:1883` as coming from the Supervisor's `mqtt` service, and that a device appears for each pier. If no release is available before archive, record this check as pending in the PR description.
- [ ] 5.3 At archive, update the Purpose paragraph of `openspec/specs/ha-addon/spec.md`: the add-on runs the released image with the user's own config file, and its only behaviour of its own is to use the Supervisor's broker when the file names none. A delta spec cannot change a Purpose. Verify by reading the archived spec (design Migration Plan).
