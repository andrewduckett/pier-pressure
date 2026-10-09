Practice TDD: write the failing test first, then change the code. `just check` (ruff
lint, mypy strict, pytest) is the CI gate, and it must be green before the PR is
marked ready. The verdict document and the golden verdict files do not change.

## 1. Fake client and client protocol

- [x] 1.1 Extend `FakeMqttClient` in `tests/conftest.py` with `drop(script)` (design D6). It calls `on_disconnect` with paho's "Unspecified error" reason, then plays the script of attempts on the calling thread, as `loop_start` does. The script can end the thread with no callback (`THREAD_ENDS`). Verify that every existing test still passes.
- [x] 1.2 Give the fake an `on_subscribe` attribute, and make `subscribe()` return a result code and a message ID. Add a way to refuse a topic's subscription with a failure reason code, and a way to make `subscribe()` return a failure code. Verify that every existing test still passes.
- [x] 1.3 Add `on_subscribe` and the `subscribe()` return value to the `MqttClient` protocol in `pierpressure/delivery/mqtt.py`. Verify that mypy passes.

## 2. Pin paho's behaviour with a real client

- [ ] 2.1 Add a test to `tests/test_paho_contract.py`. After a real paho client has connected once, close its socket and accept a new one. Check that paho calls `on_connect` again, and that `subscribe` from inside that callback sends a SUBSCRIBE packet. Verify that it passes (design D6).
- [ ] 2.2 Add a test that, during a reconnect, an immediate try that cannot open a socket ends paho's thread with no callback and sets `_thread` to `None`. Verify that it passes (design D6, D7).
- [ ] 2.3 Add a test that a QoS 1 message with no acknowledgement when the socket closes is sent again after the reconnect, right after `on_connect` returns. Verify that it passes (design Risks, D6).

## 3. Connection phases and re-subscribing in `MqttDelivery`

- [ ] 3.1 Write tests first in `tests/test_reconnect.py`. After startup and a `drop` followed by an acceptance, every refresh topic is subscribed again, and a refresh message then reaches the refresh callback. Verify that the tests fail (spec "Refresh works again after a reconnect").
- [ ] 3.2 Write tests first for logging with `caplog`. A drop, two failed attempts, then an acceptance give one warning for the lost connection, one warning per failed attempt, and one info line for the reconnect. Each line names the host and port, and none contains the password. Verify that the tests fail (spec "The outage is logged").
- [ ] 3.3 Write tests first for a login rejected during a reconnect. "Not authorized" logs an error with the configured login advice, does not raise, and does not stop paho's loop. A later acceptance then reconnects. Verify that the tests fail (spec "A login rejected during a reconnect does not stop the process").
- [ ] 3.4 Implement design D1 and D2 in `MqttDelivery`: the STARTING, CONNECTED and RECONNECTING phases, re-subscribing from a copy of the topic map, and `on_reconnect(callback)`. Keep #33's startup behaviour unchanged. Verify that 3.1 to 3.3 pass, and that every #33 test in `tests/test_broker_wait.py` still passes.

## 4. Subscription checks

- [ ] 4.1 Write tests first. A refused SUBACK logs a warning that names the topic and the reason, both at startup and after a reconnect. A failure code from `subscribe()` logs a warning that names the topic. The process keeps running in both cases. Verify that the tests fail (spec "A refused subscription is logged").
- [ ] 4.2 Write a test first for the race in design D6. The fake's `subscribe()` starts a second thread that calls `on_subscribe` with a refusal, gives it a short time to run, then returns the message ID. The warning must name the topic. Verify that the test fails.
- [ ] 4.3 Implement the subscription lock and the map from message ID to topic (design D2). Verify that 4.1 and 4.2 pass.

## 5. Keep paho's thread running after startup

- [ ] 5.1 Write tests first. After startup, a `drop` whose script ends the thread with no callback makes the watcher log one failed attempt and call `loop_start` again. A later acceptance restores delivery. Use a short watcher interval or an injected wait, so the test does not sleep for a full second. Verify that the tests fail (spec "A failed immediate try during a reconnect is tried again").
- [ ] 5.2 Write a test first that `close()` stops the watcher before `loop_stop()`, and that no watcher thread is left running afterwards. Verify that the test fails.
- [ ] 5.3 Implement the watcher in design D7: a daemon thread started when `connect` returns, a stop event, and `close()` joining it first. Verify that 5.1 and 5.2 pass.

## 6. Replay the last state from the main thread

- [ ] 6.1 Write tests first for the adapter. After `publish_verdict` and `publish_health`, `replay()` publishes each pier's discovery configs, states, attributes, narrative and health again. Each has its last payload and the retain flag, in the order the topics were first published. `replay()` does not publish the availability topic. A pier never published replays nothing. Verify that the tests fail (spec "The last state is published again before online", "A broker that lost its retained messages gets them back").
- [ ] 6.2 Implement the per-pier record of retained publishes and `replay()` in `MqttDelivery` (design D4). Verify that 6.1 passes.
- [ ] 6.3 Write tests first for the service in `tests/test_service.py`. A `Reconnected` marker on the queue makes `run` call `replay()`, then `go_online()`. It calls no conditions provider and no explainer, and it does not move the interval deadline. Several markers drained together cause one replay. A marker drained with refreshes is handled before them. Verify that the tests fail (spec "Entities come back online after a reconnect", "A reconnect computes no new verdict").
- [ ] 6.4 Write a test first for a reconnect during startup. The marker is queued before `run` starts. `run` then publishes the health reset, `online` and the verdicts, then the replay, then `online` again. Verify that the test fails (spec "A reconnect during startup keeps the startup order", "The first connection is not a reconnect").
- [ ] 6.5 Implement design D3 in `pierpressure/service.py`: the `Reconnected` marker type, `enqueue_reconnect()`, and `_drain` returning the pier IDs and the reconnect flag. Verify that 6.3 and 6.4 pass, and that every existing service test still passes.
- [ ] 6.6 Write a test first for a message still being sent at the drop. With `online` already published, a drop and an acceptance still lead the service to publish the state, then `online`. The adapter removes nothing from the client. Verify that it fails, then passes once 6.5 is done (spec "A message still being sent at the drop does not change the order").

## 7. Login advice and entry point

- [ ] 7.1 Write tests first. `MqttDelivery(login_advice=...)` puts that advice in a startup `LoginRejected` message and in a reconnect's rejection log. Without the argument, the advice is today's advice for the config file's login. In `tests/test_main.py`, a broker from the Supervisor still gets the Mosquitto advice at startup. Verify that the tests fail (design D5).
- [ ] 7.2 Implement design D5. `MqttDelivery` takes `login_advice`, and `__main__.py` passes `SUPERVISOR_LOGIN_ADVICE` for a Supervisor broker and drops its own advice swap. `__main__.py` also registers `service.enqueue_reconnect` with `delivery.on_reconnect`, next to `subscribe_refresh`. Verify that 7.1 passes, and that every existing `tests/test_main.py` test still passes.
- [ ] 7.3 Update the docstrings in `pierpressure/delivery/mqtt.py`, `pierpressure/service.py` and `pierpressure/__main__.py`. Remove the "later reconnects belong to #44" comment. Verify by reading the diff.

## 8. Docs

- [ ] 8.1 Update `ha-addon/DOCS.md`. Say that PierPressure reconnects after a broker outage, and restores its entities and the Refresh button. Add rows for the lost-connection warning, a login rejected during a reconnect, and a refused subscription. Verify that `tests/test_docs.py` passes, and by reading the diff.

## 9. Verify and archive

- [ ] 9.1 Run `just check` and verify that it is green.
- [ ] 9.2 Do a manual check with a real Mosquitto broker. Start PierPressure from source and let it go online. Then stop the broker, start it again, and verify each of these:
  - PierPressure logs the lost connection, its attempts, and the reconnect.
  - The availability topic reads `online` again.
  - Pressing Refresh, or publishing to a refresh topic, recomputes that pier.

  Repeat with broker persistence turned off, and check that the discovery configs and states are retained again. Record the results in the PR description.
- [ ] 9.3 Archive the change. Verify that `openspec/specs/ha-delivery/spec.md` holds the new requirement, then flip PR #62 to ready.
