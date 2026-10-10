Practice TDD: write the failing test first, then change the code. `just check` (ruff
lint, mypy strict, pytest) is the CI gate, and it must be green before the PR is
marked ready. The verdict document and the golden verdict files do not change.

## 1. Pin paho's behaviour with a real client

- [x] 1.1 Add a test to `tests/test_paho_contract.py`. A real paho client's `publish()` returns an info object whose `wait_for_publish(timeout=...)` returns, without raising, when the message is not confirmed in time, and whose `is_published()` then returns `False`. Verify that it passes (design Context, D2).

## 2. The fake client

- [x] 2.1 Make `FakeMqttClient.publish` in `tests/conftest.py` return an info object with `rc`, `wait_for_publish(timeout)` and `is_published()`. A publish is confirmed at once by default. A test can mark one topic as unconfirmed. Record each `wait_for_publish` timeout, and record `publish`, `disconnect` and `loop_stop` in `calls`. Verify that every existing test still passes (design D4).

## 3. `close()` publishes `offline`

- [x] 3.1 Write tests first in `tests/test_reconnect.py`. While connected, `close()` publishes a retained `offline` at QoS 1 to the availability topic, waits for it with a two-second timeout, then disconnects, then stops the loop. Verify that the tests fail (spec "A planned stop publishes a retained offline before disconnecting", design D1).
- [x] 3.2 Write tests first: after a `drop` with no acceptance, `close()` publishes nothing and still disconnects and stops the loop. With `offline` unconfirmed, `close()` logs one warning, disconnects and returns without raising. Verify that the tests fail (spec "A stop while disconnected publishes nothing", "An unconfirmed offline message does not block the stop", design D2).
- [x] 3.3 Implement design D1 and D2 in `MqttDelivery.close()` in `pierpressure/delivery/mqtt.py`, with the two-second wait as a module constant. Update the `close()` and module docstrings. Verify that 3.1 and 3.2 pass, and that `test_close_stops_the_watcher_before_the_loop` and the rest of `tests/test_reconnect.py` still pass.

## 4. The entry point

- [x] 4.1 Write tests first in `tests/test_main.py`, with `StartupStub`. A SIGTERM during `service.run()` makes `main()` call `close()` and return 0. A SIGTERM raised from `subscribe_refresh()` does the same. Restore the SIGTERM handler after each test. Verify that the tests fail (spec "A termination signal stops the process cleanly", design D3).
- [x] 4.2 Implement design D3 in `pierpressure/__main__.py`. Install `signal.default_int_handler` for SIGTERM before `connect()`. Start the `try`/`finally` that calls `close()` right after `connect()` returns, so it covers `subscribe_refresh()`, the "started" log and `service.run()`. Remove the `pragma: no cover` from that `except KeyboardInterrupt`, and update the module docstring. Verify that 4.1 passes and every test in `tests/test_main.py` still passes.

## 5. Docs

- [x] 5.1 In `README.md`, replace "If the container stops, its last-will message marks every entity unavailable." Say that a stop marks every entity unavailable: a planned stop publishes `offline`, and a crash or lost connection triggers the last-will. Verify that `tests/test_docs.py` passes.

## 6. Verify

- [x] 6.1 Run `just check`, and verify that ruff, mypy and pytest are all green.
- [x] 6.2 Run PierPressure in a container against a local Mosquitto broker. Run `docker stop` on it. Verify that it stops within a few seconds, that its log shows "Shutting down", and that the retained availability on the broker reads `offline`. Record the result in this task.

  Result (2026-10-10, Mosquitto 2, the image built from this branch): before the
  stop, the retained `pierpressure/status` read `online`. `docker stop` returned
  in 0.2 s, and the container exited with code 0. Its log ended with "Shutting
  down". After the stop, the retained `pierpressure/status` read `offline`.
