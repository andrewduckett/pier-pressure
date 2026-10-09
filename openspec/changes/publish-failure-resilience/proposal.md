## Why

A broker outage can stop PierPressure for good. If an interval tick or a Refresh
press comes during the outage, paho reports that it is not connected. The delivery
adapter then raises `DeliveryError`, and the process exits. On the Home Assistant
add-on the watchdog is off by default. So PierPressure stays stopped, with no
verdicts, until someone restarts it.

#44 made PierPressure restore its delivery after a reconnect. But that works only
when the whole outage falls between two publishes. This change closes that gap.
#44's replay is what makes it safe: after a reconnect, PierPressure publishes each
pier's last state again, so nothing a publish missed during the outage stays
missing.

Story: #43 "publish-failure-resilience — a failed MQTT publish never stops
PierPressure".

## What Changes

- **A publish never stops the process.** The delivery adapter no longer raises
  `DeliveryError` for a publish result code. A code other than success or "not
  connected" is logged as a warning that names the topic. The process keeps
  running.
- **The adapter holds publishes while it knows it is disconnected.** It records
  each retained message for the replay, but does not hand it to paho. After the
  reconnect, the replay sends the latest payload of every topic, then `online`.
  This keeps paho's queue small during a long outage. So a cap on that queue is
  not needed, and the replay is never rejected because the queue is full.
- **Every retained message is recorded for the replay, whatever paho says.**
  Today the adapter records a message only when paho accepts it. Then a later
  replay could send an older payload.
- **The startup health reset needs no retry.** The process still publishes the
  reset before `online`. If the connection drops in between, the replay after the
  reconnect sends the reset health, then `online`. Nothing goes online with stale
  health, and the process does not exit.
- **`main()` no longer treats a delivery error from the service loop as fatal.**
  `DeliveryError` stays only for a login the broker rejects at startup.

Out of scope:

- **Waiting for the broker to confirm each publish, and going `offline` on a
  clean stop.** That is #41. Its "raise if not confirmed" part conflicts with this
  change, and a comment on #41 says so.
- **Invalid topics or payloads.** paho raises `ValueError` for these. They are
  programming errors, and they still stop the process.
- **A persistent session** (`clean_session=False`).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `ha-delivery`:
  - "Delivery failures are reported, not swallowed": a failed publish is
    reported in the log, and the process keeps running.
  - "Provider health is exposed as diagnostic entities": a startup reset that
    cannot be sent no longer makes the process exit. It is sent before `online`
    once the broker reconnects.
  - "The process restores delivery after a reconnect": it now covers an outage
    during which the process publishes. A publish during the outage is held for
    the replay.

## Impact

- **Changed files:**
  - `pierpressure/delivery/mqtt.py`: `_send` never raises for a result code.
    `_publish` records first, and skips paho while the connection is down.
  - `pierpressure/service.py`: the `_reset_health` docstring loses the exit
    promise. The loop itself does not change.
  - `pierpressure/__main__.py`: no longer catches `DeliveryError` from `run()`.
  - `tests/conftest.py`: the fake client can report "not connected" for a
    publish.
- **Tests** cover these cases:
  - An interval publish during an outage does not stop the process, and the
    latest state is published after the reconnect.
  - A publish with an unexpected result code is logged, and the process keeps
    running.
  - A drop between the first connection and the startup reset still sends the
    reset health before `online`.
- **No change** to the verdict document, MQTT topics, entities, or entity mapping.
- **No new dependencies.**
