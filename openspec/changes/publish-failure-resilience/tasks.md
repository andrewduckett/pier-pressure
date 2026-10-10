Practice TDD: write the failing test first, then change the code. `just check` (ruff
lint, mypy strict, pytest) is the CI gate, and it must be green before the PR is
marked ready. The verdict document and the golden verdict files do not change.

## 1. Pin paho's behaviour with a real client

- [x] 1.1 Add a test to `tests/test_paho_contract.py`. A real paho client that has lost its connection returns `MQTT_ERR_NO_CONN` for a QoS 1 `publish()`, keeps the message, and sends it after the reconnect. Verify that it passes (design Context, D3).

## 2. The fake client

- [x] 2.1 Let `FakeMqttClient` in `tests/conftest.py` return a chosen result code for publishes to one topic, as `fail_subscribe` does for subscriptions. Keep `publish_rc` for every topic. Verify that every existing test still passes.

## 3. `MqttDelivery` never raises for a publish

- [ ] 3.1 Write tests first in `tests/test_publish.py`. Replace `test_publish_failure_rc_is_reported`: a refused publish (for example `MQTT_ERR_QUEUE_SIZE`) logs one warning that names the topic and paho's error text, and does not raise. A publish that returns `MQTT_ERR_NO_CONN` logs no warning and does not raise. No log line contains the broker password. Verify that the tests fail (spec "A refused publish is logged and the process keeps running", design D3).
- [ ] 3.2 Write tests first in `tests/test_replay.py`. A retained message that paho refuses is still recorded, and the next `replay` sends its payload. A later payload for the same topic replaces it. Verify that the tests fail (design D2).
- [ ] 3.3 Write tests first in `tests/test_reconnect.py`. After a `drop` with no acceptance, `publish_verdict`, `publish_health` and `go_online` hand nothing to the client, and `replay` hands nothing to the client. After the next acceptance, `replay` sends the held payloads. Verify that the tests fail (spec "Nothing is handed to the MQTT client while the process knows it is disconnected", design D1).
- [ ] 3.4 Implement design D1 to D3 in `pierpressure/delivery/mqtt.py`: `_publish` records first, `_send` returns at once while the phase is `RECONNECTING`, and `_send` logs instead of raising. Update the module and method docstrings that say a refused message is not recorded. Verify that 3.1 to 3.3 pass, and that every test in `tests/test_reconnect.py`, `tests/test_replay.py` and `tests/test_broker_wait.py` still passes.

## 4. The service and the entry point

- [ ] 4.1 Write tests first in `tests/test_service_reconnect.py`, with the real `MqttDelivery` and the fake client. A drop, then an interval recompute, then an acceptance: the service does not raise, and after the reconnect the client receives the new verdict state and attributes for each pier, then `online` last. Verify that the test fails (spec "A publish during an outage does not stop the process", "State published during an outage is restored after the reconnect").
- [ ] 4.2 Write a test first: a drop after `connect` and before `run`, then an acceptance. The client receives each provider's reset health before `online`, and `run` does not raise. Replace `test_a_failed_startup_reset_raises_and_never_goes_online` in `tests/test_service.py`, which expects the old exit. Verify that the new test fails (spec "A failed startup reset does not go online", design D4).
- [ ] 4.3 Update the `_reset_health` docstring and the provider-health paragraph of the module docstring in `pierpressure/service.py`, which promise an exit. Verify that 4.1 and 4.2 pass, and that every test in `tests/test_service.py` and `tests/test_service_reconnect.py` still passes.
- [ ] 4.4 Remove the `except DeliveryError` around `service.run()` in `pierpressure/__main__.py`, and its comment (design D5). Keep the `DeliveryError` handling around `connect()`. Update the module docstring if it mentions the exit. Verify that every test in `tests/test_main.py` passes, and add one if no test covers a `LoginRejected` from `connect` still returning 1.

## 5. Docs

- [ ] 5.1 Update "If the broker stops while the add-on runs" in `ha-addon/DOCS.md`. Remove the sentence that says the add-on can stop if the broker is still away when an update is due. Say that PierPressure keeps running, and that each pier's latest verdict appears once the broker is back. Verify that `tests/test_docs.py` and `tests/test_ha_addon.py` pass.

## 6. Verify

- [ ] 6.1 Run `just check`, and verify that ruff, mypy and pytest are all green.
- [ ] 6.2 Run PierPressure against a local Mosquitto broker with a short interval. Stop the broker for longer than one interval, then start it again. Verify that the process does not exit, that the log shows the lost connection and the reconnect, and that the retained verdict state on the broker carries the generation time of the recompute made during the outage. Record the result in this task.
