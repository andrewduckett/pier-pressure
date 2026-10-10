## Why

When PierPressure stops cleanly, Home Assistant keeps showing it as online. The
process disconnects from the broker with a clean DISCONNECT. The broker sends the
last-will only when a connection ends unexpectedly. So the retained availability
stays `online`, and every entity keeps showing its last state as if it were
current.

Two kinds of stop take this path today: a Ctrl-C, and an unexpected error in the
service loop. An add-on stop avoids it only by accident. The image runs Python as
PID 1 with no SIGTERM handler, so the process ignores SIGTERM. After the grace
period, SIGKILL drops the connection, and the broker sends the last-will. Every
stop, restart and update of the add-on waits out that grace period.

#43 and #44 made the running process resilient to broker outages. This change
makes the availability honest when the process stops.

Story: #41 "stop-goes-offline — a stopped process goes offline in Home
Assistant".

## What Changes

- **A clean stop publishes `offline` first.** Before it disconnects, the delivery
  adapter publishes a retained `offline` to the availability topic. It waits a
  short time for the broker to confirm it, then disconnects.
- **A stop while disconnected publishes nothing.** The broker has already sent
  the last-will, so the availability already reads `offline`.
- **A stop never fails on the `offline` message.** If the broker does not confirm
  it in time, the adapter still disconnects and the process still exits.
- **SIGTERM stops the process the same way as Ctrl-C.** An add-on stop then goes
  through the clean stop at once, instead of waiting for SIGKILL.

Out of scope:

- **Waiting for the broker to confirm each ordinary publish.** The first draft of
  #41 asked for this. #43 decided that a publish never raises, and that the
  replay after a reconnect repairs a lost message. That decision stands.
- **A move to MQTT 5** to use its "disconnect with will message" option.
- **An init process in the image**, or a new config option.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `ha-delivery`: "Availability reflects process liveness via last-will" now also
  covers a planned stop. The process publishes a retained `offline` before it
  disconnects cleanly.

## Impact

- **Changed files:**
  - `pierpressure/delivery/mqtt.py`: `close()` publishes `offline`, waits for the
    broker's confirmation, disconnects, then stops paho's loop.
  - `pierpressure/__main__.py`: `main()` handles SIGTERM the same way as Ctrl-C.
  - `tests/conftest.py`: the fake client can confirm a publish, or leave it
    unconfirmed.
- **Tests** cover these cases:
  - A clean stop publishes a retained `offline` before it disconnects.
  - A stop while disconnected publishes nothing.
  - A stop still finishes when the broker does not confirm `offline`.
  - SIGTERM ends `main()` through the clean stop, with exit code 0.
- **No change** to the verdict document, MQTT topics, entities, or entity mapping.
- **No new dependencies.**
