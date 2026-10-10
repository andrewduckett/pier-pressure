## Context

See `proposal.md` for why this change is needed. See the `ha-delivery` delta spec
for the required behaviour.

The change touches two places:

- `MqttDelivery.close()` in `pierpressure/delivery/mqtt.py`. Today it stops the
  watcher thread, calls paho's `loop_stop()`, then `disconnect()`. It publishes
  nothing.
- `main()` in `pierpressure/__main__.py`. It catches `KeyboardInterrupt` around
  `connect()` and around `service.run()`, and calls `delivery.close()` in a
  `finally` block. It installs no SIGTERM handler.

`MqttDelivery` tracks the connection in `_phase`: `STARTING`, `CONNECTED` or
`RECONNECTING`. Only paho's network thread changes it. Only the main thread
publishes (ADR-0012).

Four facts about paho 2.1 and the runtime shape the design. Each was checked in
the pinned source or the Python documentation:

- **A clean DISCONNECT suppresses the last-will.** This is MQTT 3.1.1 behaviour,
  and PierPressure uses MQTT 3.1.1.
- **`MQTTMessageInfo.wait_for_publish(timeout)` blocks until the broker confirms
  a QoS 1 message, or until the timeout.** It raises `RuntimeError` if paho did
  not queue the message, and `ValueError` if paho's queue was full. It returns
  silently on a timeout. `is_published()` then tells whether the broker
  confirmed the message.
- **paho needs its network thread to send and confirm a message.** `close()`
  stops that thread today before it disconnects. The thread must stay up until
  the `offline` message is confirmed or the wait ends.
- **Python delivers signals to the main thread only.** A handler that raises
  `KeyboardInterrupt` interrupts the main thread wherever it is, including a
  blocking `queue.get(timeout=...)` in the service loop.

## Goals / Non-Goals

**Goals:**

- Every planned stop while connected publishes a retained `offline` before it
  disconnects. This is a best effort: a broker that never receives it keeps
  `online`.
- A stop never hangs on the broker, and never raises from `close()`.
- An add-on stop finishes in a few seconds, not after the SIGKILL grace period.

**Non-Goals:**

- Confirming ordinary publishes. #43 decided that a publish never raises, and
  the replay after a reconnect repairs a lost one.
- A graceful drain of in-flight verdict publishes. A stop can cut a pier's
  publish short. Every message is a full retained state, and `offline` makes the
  entities unavailable anyway.
- Handling a second signal during `close()`. The wait is short, and the
  container runtime sends SIGKILL after its grace period.

## Decisions

### D1. `close()` publishes `offline` while paho's thread still runs

`close()` follows this order:

1. Set `_closing` and stop the watcher thread, as today.
2. If `_phase` is `CONNECTED`, publish a retained `offline` to the availability
   topic at QoS 1, and wait for the broker to confirm it (D2).
3. Call `disconnect()`.
4. Call `loop_stop()`.

Disconnecting before stopping the loop lets paho's thread send the DISCONNECT
packet. Today's order, `loop_stop()` first, works only because paho writes the
packet directly once the thread has stopped.

`close()` calls paho's `publish` directly, not `_send`. `_send` holds every
publish while the phase is `RECONNECTING`, and it logs refusals for the next
update to repair. Neither fits a stop, because no update comes after it.

The `offline` message is not recorded for the replay. Nothing replays after a
stop.

**Alternative considered: send `offline` in every phase.** In `RECONNECTING`,
paho would queue the message and never send it, because the process exits
first. In `STARTING`, the broker has not accepted the connection yet. So the
publish happens only in `CONNECTED`.

**Alternative considered: MQTT 5 "disconnect with will message".** The broker
would then send the last-will on a clean disconnect. That needs a protocol
change across the adapter and its tests. Publishing `offline` gives the same
result with no protocol change.

### D2. The wait for the broker's confirmation is two seconds, and never raises

`close()` calls `wait_for_publish(timeout=2.0)` on the `offline` message's info.
It treats every outcome the same way: the stop goes on. On a timeout,
`RuntimeError` or `ValueError`, it logs one warning, then disconnects.

Two seconds is long enough for a local broker to confirm one message. It is
well inside Docker's default grace period of 10 seconds before SIGKILL. The
value is a module constant, not a config option.

If the broker never confirms `offline`, the outcome is no worse than today. The
broker may still have received it. If it did not, the retained availability
stays at its last value until the next start.

### D3. SIGTERM raises `KeyboardInterrupt` in the main thread

`main()` installs `signal.default_int_handler` for SIGTERM before it connects.
That handler raises `KeyboardInterrupt`, which `main()` already handles: it logs
"Shutting down", calls `close()`, and returns 0. The same code path then serves
Ctrl-C, SIGTERM, and an unexpected error in the loop.

Today `subscribe_refresh()` and the "started" log sit between the `connect()`
block and the `try` around `service.run()`. A signal there would skip
`close()`. So the `try`/`finally` that calls `close()` starts right after
`connect()` returns, and covers `subscribe_refresh()`, the log and
`service.run()`.

The handler goes in `main()`, not in the delivery adapter or the service. Only
the entry point owns the process, and tests that build a `Service` directly
keep their default signal handling.

**Alternative considered: an init process (`tini`, or `docker run --init`).**
An init process forwards SIGTERM, but Python still needs a handler to run
`close()`. The handler alone fixes the problem, with no change to the image.

**Alternative considered: a stop event that the service loop checks.** That
would let the loop finish its current pier first. It needs a new path through
`Service.run()` and its queue. A stop does not need a finished pier (see
Non-Goals), so the simpler handler wins.

### D4. The fake client confirms publishes, unless a test says otherwise

`FakeMqttClient.publish` returns an info object with `wait_for_publish` and
`is_published`. By default the message is confirmed at once. A test can mark a
topic as unconfirmed, so `wait_for_publish` returns at once with the message
unconfirmed, as paho does after a timeout. The fake records the calls, so tests
can check that `offline` comes before `disconnect`, and `disconnect` before
`loop_stop`.

## Risks / Trade-offs

- **A stop during a slow conditions fetch interrupts it.** →
  `KeyboardInterrupt` unwinds the fetch, and the `finally` block still runs
  `close()`. The fetch result is not needed after a stop.
- **A drop that paho has not detected yet.** `_phase` can read `CONNECTED` just
  after the link died. → The wait ends after two seconds, and the broker sends
  the last-will when it notices the dead link.
- **The broker never receives `offline`.** The DISCONNECT that follows then
  suppresses the last-will, and the broker keeps `online`. → Accepted. This
  needs a broker that confirms nothing for two seconds yet stays connected, and
  the outcome is no worse than today.
- **A reconnect between the phase check and `disconnect()`.** `close()` then
  skips `offline` and disconnects cleanly, so the broker keeps `online`. →
  Accepted. The window is a few microseconds, and a lock for it is out of
  proportion to the risk.
- **The `except KeyboardInterrupt` in `main()` is no longer interactive-only.**
  → Its `pragma: no cover` comes off, and a SIGTERM test covers it.
- **A new ADR is not needed.** The choice is small and easy to reverse, and the
  code and spec explain it.
