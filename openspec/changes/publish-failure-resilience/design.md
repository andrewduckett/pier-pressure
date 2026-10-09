## Context

See `proposal.md` for why this change is needed. See the `ha-delivery` delta spec
for the required behaviour.

The change builds on what #44 left in `pierpressure/delivery/mqtt.py` and
`pierpressure/service.py`:

- `MqttDelivery` tracks the connection in `_phase`: `STARTING`, `CONNECTED` or
  `RECONNECTING`. Only paho's network thread changes it. `_on_disconnect` moves it
  to `RECONNECTING` and logs the lost connection. `_on_reconnect_answer` moves it
  to `CONNECTED`, subscribes again, then tells the service.
- `MqttDelivery._publish` calls `_send`, then records a pier's retained message in
  `_retained`. `_send` raises `DeliveryError` for any result code other than
  success, so a refused message is never recorded.
- `MqttDelivery.replay` sends every recorded message again, in the order the
  topics were first published. The service then calls `go_online`.
- Only the main thread publishes (ADR-0012). paho's thread puts a reconnect marker
  on the work queue, and the main thread replays.

Four facts about paho 2.1 shape the design. Each was checked in the pinned source:

- **paho queues a QoS 1 publish made while disconnected.** `publish()` stores the
  message and returns `MQTT_ERR_NO_CONN`. paho sends it after the reconnect.
- **paho resends queued messages in the order they were published.**
  `_messages_reconnect_reset_out` walks its outgoing messages in insertion order.
- **paho's outgoing queue has no limit by default.** `max_queued_messages` is 0.
  With a limit, a publish beyond it returns `MQTT_ERR_QUEUE_SIZE` and paho drops
  the message. paho also returns `MQTT_ERR_QUEUE_SIZE` when a message ID is still
  in use. Message IDs wrap at 65,535.
- **paho detects a drop late.** It notices a dead socket on its next read, write
  or keepalive. Until then, `publish()` can return success for a message that
  paho will have to send again.

One pier's publish is about 47 messages: discovery, verdict, score, ten ranks,
narrative, and two providers' health.

## Goals / Non-Goals

**Goals:**

- No publish result code stops the process.
- paho's queue stays small, however long an outage lasts.
- The replay after a reconnect sends the latest payload of every topic.
- Reset health always reaches the broker before `online`. With no drop, the
  startup order is unchanged: reset health, then `online`, then verdicts.

**Non-Goals:**

- Confirming that the broker received a message (#41).
- Removing duplicate messages. A message can reach the broker twice after a
  reconnect: once from paho's queue, then again from the replay. Every message is
  a full retained state, so a duplicate is harmless.

## Decisions

### D1. The adapter holds publishes while it knows it is disconnected

`_send` checks `_phase` first. When the phase is `RECONNECTING`, `_send` returns
without calling paho. This covers every publish path: verdicts, health, `online`,
and the replay itself.

A held retained message is still recorded (D2), so the replay sends it. A held
`online` is not recorded. The service publishes `online` after the replay, so it
is not lost.

The ordering works because of the order in `_on_reconnect_answer`. It sets the
phase to `CONNECTED` first, and only then tells the service. So every message
held before the switch is in `_retained` before the replay reads it. Every
message after the switch goes straight to paho.

The connection can drop again during the replay. Then `_send` holds the rest of
the replay and `online`. The held `online` is not recorded, but the next
reconnect puts a new marker on the queue. Its replay then sends the state, then
`online`.

The main thread reads `_phase` without a lock. A single attribute read is atomic
in Python, also in the free-threaded build. A stale read costs at most one
message handed to paho just after a drop, which paho queues and resends.

Alternatives considered:

- **Hand everything to paho and cap its queue.** This was the first plan. It
  fails at the reconnect. After a long outage the queue is full of old messages.
  The replay and `online` then hit the cap and paho drops them. So the state the
  broker ends up with is old, and `online` never arrives. The cap would also have
  to scale with the number of piers.
- **Hand everything to paho with no cap.** A long outage then grows the queue
  without limit: about 47 messages per pier on each interval. Once more than
  65,535 messages are waiting, message IDs clash, and paho drops messages
  anyway. The replay also sends all of them a second time.
- **Track "connected" in a new flag.** `_phase` already says this, and only one
  thread writes it. A second flag would need its own rules for ordering.

### D2. Every retained message is recorded before it is sent

`_publish` records the message in `_retained` first, then calls `_send`. Today it
records only after paho accepts the message. Then a refused message leaves an
older payload in `_retained`, and the next replay would send that older payload.

Recording first means `_retained` always holds the latest payload the core
produced. That is what the replay should restore.

### D3. `_send` logs a refused publish and never raises

`_send` handles each result code from paho as follows:

| Result code | Meaning | Action |
|---|---|---|
| `MQTT_ERR_SUCCESS` | Sent, or queued behind messages in flight | None |
| `MQTT_ERR_NO_CONN` | paho saw the drop first; the message is queued | Log at debug level |
| Any other code | paho did not take the message | Log a warning naming the topic and `mqtt.error_string(rc)` |

`MQTT_ERR_NO_CONN` needs no warning. `_on_disconnect` logs the lost connection,
and the message is queued. Any other code is rare. With no cap, it means a
message ID clash. The replay after the next reconnect repairs it, and so does
the next interval.

`DeliveryError` stays in the module. `connect` still raises it, and its
`LoginRejected` subclass, before the service loop starts.

Alternative considered: **raise, and let the service catch it per pier.** That
keeps one pier's failure from blocking the others. But a raise now has no reader
that can act on it. The log is the report the spec asks for.

### D4. The startup health reset needs no retry

The service keeps its startup order: `_reset_health`, `go_online`, `publish_all`.
A drop at any point in that order is repaired without a retry loop:

```
 connect ok
     |
     +-- drop seen before the reset -----> reset held (D1), online held,
     |                                     verdicts held; reconnect -> replay
     |                                     (health, verdicts), then online
     |
     +-- drop not yet seen by paho ------> reset, online queued in paho in that
                                           order; reconnect -> paho sends them,
                                           then replay, then online
```

In both paths, reset health reaches the broker before `online`. That is the rule
the startup reset exists for. In the first path, the broker receives the replay
order (health, verdicts, then `online`), not the startup order. This is the order
every reconnect already uses. The service keeps no new state, and `run()` does
not change.

Alternative considered: **retry the reset with a back-off before going online.**
That adds a second retry loop beside paho's own (ADR-0018). It would also need a
test for its schedule. It gains nothing that D1 and the replay do not already
give.

### D5. `main()` stops catching `DeliveryError` from `run()`

Nothing in `run()` raises `DeliveryError` after D3. The `except DeliveryError`
around `service.run()` goes, together with its comment about the startup reset.
`main()` still catches `DeliveryError` from `connect()`.

An exception that is not a `DeliveryError` still ends the process, as today. For
example, paho raises `ValueError` for an invalid topic. That is a programming
error, and stopping is the right response.

## Risks / Trade-offs

- [paho detects a drop late, so a few messages reach paho's queue after the
  socket died] → paho queues and resends them in order. The replay then repeats
  them. The window lasts until paho notices, at most one keepalive.
- [A message can reach the broker twice] → Every message is a full retained
  state, so Home Assistant shows the same value. This is already true after a
  reconnect today.
- [A warning-level refusal while connected leaves one topic stale until the next
  interval or reconnect] → It needs a message ID clash, which needs about 65,000
  messages waiting. D1 keeps the queue far smaller.
- [`_retained` keeps every topic's latest payload] → It already does after #44.
  Its size depends on the number of piers, not on the length of an outage.

## Migration Plan

No migration. The change ships in the next release image and add-on version. A
rollback restores the old behaviour: a publish during an outage stops the
process.
