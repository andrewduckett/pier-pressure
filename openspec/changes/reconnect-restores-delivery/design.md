## Context

See `proposal.md` for why this change is needed, and the `ha-delivery` delta spec
for the required behaviour.

The change builds on what #33 left in `pierpressure/delivery/mqtt.py`:

- `MqttDelivery.connect` sets four paho handlers: `on_pre_connect`, `on_connect`,
  `on_connect_fail` and `on_disconnect`. It then waits on a `threading.Event`
  until the broker answers the first time.
- Once that event is set, every handler returns at once. A comment says "later
  reconnects belong to #44".
- paho's network thread reconnects after an outage. It calls the same four
  handlers as at startup, and it pauses between attempts with the delays set by
  `reconnect_delay_set(1, 120)` (ADR-0018).

Three facts about paho 2.1 shape the design. Each was checked in the pinned
source:

- **`subscribe()` while disconnected is not queued.** It returns
  `MQTT_ERR_NO_CONN` and sends nothing. So subscriptions must be made again after
  the broker accepts the new connection.
- **paho calls `on_connect` on its network thread.** paho's documentation
  recommends subscribing inside `on_connect`, so that a reconnect restores the
  subscriptions.
- **`publish()` while disconnected returns `MQTT_ERR_NO_CONN`.** `_publish`
  raises `DeliveryError` for it, and the process stops. That is #43. This design
  does not change it.

The service (`pierpressure/service.py`) follows ADR-0012. paho's thread only puts
items on a `queue.Queue[str]` of pier IDs. The main thread does all computing and
publishing. It waits on the queue until an absolute deadline.

## Goals / Non-Goals

**Goals:**

- One set of handlers covers the first connection and every reconnect.
- Only the main thread publishes, including the replay and `online` after a
  reconnect.
- A reconnect costs only MQTT messages: no conditions fetch, no verdict, no
  explainer call.
- The tests drive a drop and a reconnect with the fake client, without sleeping.

**Non-Goals:**

- Watching paho's network thread after startup. See Risks.
- Changing the startup wait, its logging, or a login rejected at startup.
- Capping how often reconnects can happen. The drain in D3 already merges
  reconnects that arrive close together.

## Decisions

### D1. The handlers track three phases

`MqttDelivery` replaces the "outcome is set" check with a phase. Only paho's
thread changes the phase.

```
            first accept                 connection lost
 STARTING ---------------> CONNECTED --------------------> RECONNECTING
    |                          ^                               |
    | login rejected           |          accept               |
    v                          +-------------------------------+
 (connect raises)               login rejected, other refusal, socket failure:
                                log, stay in RECONNECTING, paho tries again
```

- **STARTING:** the handlers behave exactly as #33 wrote them.
- **CONNECTED:** `on_disconnect` logs the lost connection as a warning, then
  moves to RECONNECTING.
- **RECONNECTING:** `on_pre_connect` starts a new attempt for logging, as at
  startup. A failed attempt logs one warning through `_log_failed_attempt`. An
  accept logs "Reconnected to the MQTT broker at host:port" at info level, does
  D2, then moves to CONNECTED.

`_outcome_ready` stays. It still ends the startup wait. The phase only replaces
the handlers' "do nothing after startup" checks.

**Alternative: a separate set of handlers, swapped in after startup.** This makes
each set simpler. We rejected it because the swap happens on the main thread while
paho's thread may be calling a handler. One set of handlers with a phase has no
such window.

### D2. `on_connect` subscribes again, then signals the main thread

On an accept in RECONNECTING, `on_connect` does two things on paho's thread:

1. It subscribes again to every topic that `subscribe_refresh` registered.
2. It calls a reconnect listener that the service registered.

Subscribing does not publish, so it does not break ADR-0012's single-publisher
rule. Subscribing straight away also means a Refresh press is never lost while
the main thread is busy.

`subscribe_refresh` runs on the main thread and writes the topic map that
`on_connect` reads. A lock guards that map, and `on_connect` subscribes from a
copy. If both threads subscribe to the same topic, the broker keeps a single
subscription, so a race is harmless.

The listener is set with a new method, `MqttDelivery.on_reconnect(callback)`.
`__main__.py` registers `service.enqueue_reconnect` there, next to
`subscribe_refresh`. With no listener, a reconnect only subscribes again.

**Alternative: subscribe again on the main thread too.** This would keep every
broker write on one thread. We rejected it because the main thread can be busy
for the length of a recompute, and Refresh presses in that window would be lost.
paho is safe to call from its own callbacks.

### D3. The work queue carries a reconnect item

The queue becomes `queue.Queue[str | Reconnected]`. `Reconnected` is a one-value
marker type in `service.py`. `Service.enqueue_reconnect()` puts that marker on
the queue.

`_drain_refreshes` becomes `_drain`. It returns the set of pier IDs and whether
any reconnect marker was drained. So several reconnects close together become one
replay, just as repeated refreshes become one recompute.

When a drained batch holds a reconnect, the main thread handles it first:

1. `delivery.replay()` publishes each pier's last state again (D4).
2. `delivery.go_online()` publishes the retained `online`.

It then recomputes any piers in the same batch, as today. The reconnect does not
move the deadline, so it cannot delay the interval recompute.

A reconnect can happen after `connect` returns but before `run` reaches its loop.
The marker then waits on the queue. The startup sequence runs first: health
reset, `online`, a verdict for each pier. The loop then replays and publishes
`online` again. That is redundant but harmless, and it keeps the startup order
the spec requires.

**Alternative: a separate `threading.Event` for reconnects.** We rejected it. The
main thread blocks on the queue, so an event alone would not wake it before the
deadline. Polling both would undo ADR-0012's single wait.

### D4. The adapter remembers each retained message it publishes

`MqttDelivery` keeps a dictionary for each pier, from topic to payload. Every
retained publish for a pier records its topic and payload: the discovery configs,
states, attributes, narrative and health. `replay()` publishes every recorded
message again, retained, in the order the topics were first published. So
discovery configs go out before states, as on a first publish. The availability
topic is not recorded, because it belongs to no pier.

The adapter records a message after `_publish` succeeds. If a publish fails, the
process stops anyway (#43). Only the main thread publishes and replays, so the
dictionaries need no lock.

This replays exactly what the broker last received for each topic. It needs no
knowledge of verdict documents, narratives or health. A topic published only once,
such as a discovery config, is still replayed.

**Alternative: the service keeps the last document, narrative and health, and
calls `publish_verdict` and `publish_health` again.** This reuses the existing
methods. We rejected it because the service would keep a second copy of state it
does not otherwise need. It also could not replay the health reset unless it
tracked that separately.

**Alternative: call `publish_all()`.** We rejected it in the story. It fetches
conditions and may call the explainer on every reconnect.

### D5. The delivery adapter owns the login advice

`MqttDelivery` takes an optional `login_advice` argument. The default is today's
advice for the config file's login. `__main__.py` passes `SUPERVISOR_LOGIN_ADVICE`
when the broker came from the Supervisor.

Both rejections use this advice:

- **At startup**, `connect` raises `LoginRejected`, whose message uses the advice.
  `__main__.py` no longer swaps the advice itself.
- **During a reconnect**, `on_connect` logs an error with the same message. paho
  keeps trying. This logs one error for each rejected attempt, and paho pauses up
  to 120 seconds between attempts.

**Alternative: keep the swap in `__main__.py`, and pass the advice only for
reconnects.** We rejected it because the advice would then live in two places,
which could drift apart.

### D6. The fake client can drop the connection

`FakeMqttClient` gains `drop(script)`. It calls `on_disconnect` with paho's
"Unspecified error" reason, as paho does for a lost connection. It then plays the
script of attempts on the calling thread, as `loop_start` does. A test can then
check the log, the subscriptions, and what the service published after it drains
the queue.

The existing contract tests in `tests/test_paho_contract.py` check paho's startup
behaviour against a real client with a socket pair. One more contract test checks
that real paho calls `on_connect` again after the socket closes, and that
`subscribe` works from inside that callback.

## Risks / Trade-offs

- [After startup, nothing restarts paho's thread if it ends without a callback.]
  → That can happen only in one of paho's two immediate tries. Each happens at
  most once per process, and in practice at the first connection, while the
  startup wait still watches the thread. We accept the small remaining risk. A
  later change can add a thread check to the main loop if it ever shows up.
- [A publish during the outage still stops the process.] → That is #43. Until it
  lands, the replay helps only when the whole outage falls between two publishes.
  The interval sets how often that is true.
- [The replayed verdict can be up to one interval old.] → It is the same verdict
  the broker held before the outage, with its original generation time. The next
  interval or a Refresh press brings new data.
- [A connection that drops often causes many replays.] → Each replay is about
  thirty small messages per pier, with no network calls. The drain merges
  reconnects that arrive before the main thread runs.
- [A reconnect during a long recompute delays `online`.] → The main thread
  handles the marker after the recompute. The entities show as unavailable until
  then, which is accurate while state is stale.

## Migration Plan

No migration. The change ships in the next release image and add-on version.
Rolling back restores today's behaviour: no restore after a reconnect.
