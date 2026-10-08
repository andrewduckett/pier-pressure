Practice TDD: write the failing test first, then change the code. `just check` (ruff
lint, mypy strict, pytest) is the CI gate and must be green before the PR is marked
ready. No golden verdict file changes, and the verdict document is untouched.

## 1. Fake client and client protocol

- [x] 1.1 Extend `FakeMqttClient` in `tests/conftest.py` to follow paho (design D5). It records `connect_async(host, port)` and the delays passed to `reconnect_delay_set`. It holds the `on_pre_connect`, `on_connect`, `on_connect_fail` and `on_disconnect` handlers. It takes a script of attempt outcomes: socket failure, refusal with a reason name, connection closed before an answer, thread ended with no callback, and acceptance. Its `loop_start()` plays the script at once on the calling thread, calling the handlers in paho's order. A script that ends without an outcome leaves the fake's thread "ended". With no script, it accepts at once, so every existing test keeps working. Verify that every existing test still passes.
- [x] 1.2 Update the `MqttClient` protocol in `pierpressure/delivery/mqtt.py`: drop `connect`, and add `connect_async`, `reconnect_delay_set` and the four handler attributes. Verify that mypy passes.

## 2. Wait for the broker in `MqttDelivery.connect`

- [x] 2.1 Write tests first in `tests/test_publish.py`: `connect` calls `will_set`, then `reconnect_delay_set(1, 120)`, then `connect_async` with the configured host and port, then `loop_start`. It returns once the script accepts, and has published nothing. Replace `test_unreachable_broker_is_reported_as_a_failure`: three socket failures, then an acceptance, make `connect` return with no error. Verify the tests fail (spec "The broker starts after the process", "Nothing is published while attempts fail", "The pauses grow to a limit").
- [x] 2.2 Write tests first for temporary failures: a "Server unavailable" refusal and a connection closed before an answer are each followed by an acceptance, and `connect` returns. Verify the tests fail (spec "A broker that is not ready is tried again", "A broker that closes the connection is tried again").
- [x] 2.3 Write tests first for rejected logins: "Bad user name or password" and "Not authorized" each make `connect` call `loop_stop` and raise `DeliveryError`. The message names the broker's host and port, the reason, and the advice from design D3. A test checks that the message never contains the password. Verify the tests fail (spec "A wrong username or password stops the process", "An unauthorized client stops the process").
- [x] 2.4 Write tests first for logging with `caplog`. Each failed attempt gives exactly one warning naming the host and port. This holds for a socket failure (with the error's class name), a refusal (with the reason name) and a closed connection. A socket failure followed by paho's `on_disconnect` still gives one line. No line contains the password. Verify the tests fail (spec "Each failed attempt is logged"; design D4).
- [x] 2.5 Write a test first for the ended thread: a script that ends the thread with no callback makes `connect` log one failed attempt, call `loop_start` again, and return when the second run accepts. Verify the test fails (spec "A failure during an immediate try is tried again"; design D2).
- [x] 2.6 Implement design D1 to D4 in `MqttDelivery`: the event and outcome slot, the per-attempt logged flag, the handlers, the 1-second wait slices, the thread check through one helper that reads paho's `_thread`, and the thread restart. The handlers ignore every call after the first outcome. Verify that 2.1 to 2.5 pass.

## 3. Pin paho's behaviour with a real client

- [ ] 3.1 Write a test in a new `tests/test_paho_contract.py`: a real paho client, with `_create_socket` replaced by one end of a `socket.socketpair()`, has a live thread in `_thread` after `connect_async` and `loop_start`. Verify that it passes with the offline guard in place, and that `loop_stop` cleans up (design D2).
- [ ] 3.2 Add a test in the same file: the test plays the broker and answers the first CONNECT with CONNACK code 1. paho then sends a second CONNECT for MQTT 3.1 at once, and does not call `on_connect`. Then add a test where that second socket cannot open: paho's thread ends, and `_thread` is `None`. Verify both pass (design Context, D5).
- [ ] 3.3 Add a test in the same file: with an empty client ID, CONNACK code 2 makes paho send a second CONNECT at once with a generated client ID, and not call `on_connect`. Verify it passes (review round 3, suggestion 2).
- [ ] 3.4 Write a test with a real paho client that its `on_connect` reason codes for MQTT 3.1.1 codes 4 and 5 equal the names `MqttDelivery` compares against. Verify it passes (design D3).

## 4. Entry point and docs

- [ ] 4.1 Write a test first in `tests/test_main.py`: when `connect` raises `DeliveryError` for a rejected login and the broker came from the Supervisor, the logged error also tells the user to check the Mosquitto add-on. With a broker from the file, it does not. Verify it fails, then implement it in `pierpressure/__main__.py` (design D3).
- [ ] 4.2 Update the `pierpressure/__main__.py` docstring and the `MqttDelivery.connect` docstring. They should say that the process waits for the broker, and stops only when the broker rejects its login (design D6). Verify by reading the diff.
- [ ] 4.3 Update `ha-addon/DOCS.md`. Say that PierPressure keeps trying to reach the broker and logs each attempt. Add a row for the "Could not connect to the MQTT broker" warning (check `mqtt.host` and `mqtt.port`), and one for the rejected-login error. Fix the line that says every startup error starts with `Configuration error`. Verify that `tests/test_docs.py` passes, and by reading the diff.

## 5. Verify and archive

- [ ] 5.1 Run `just check` and verify it is green.
- [ ] 5.2 Do a manual check with a real broker. Start PierPressure from source while the broker is stopped. Verify that each attempt logs a warning, with growing gaps. Start the broker, and verify that PierPressure goes online and publishes a verdict for each pier. Then restart it with a wrong password, and verify that it exits with the rejected-login error. Record the result in the PR description.
- [ ] 5.3 Archive the change. Verify that `openspec/specs/ha-delivery/spec.md` holds the new requirement, then flip PR #61 to ready.
