## Why

After a broker outage, PierPressure reconnects but does not restore its delivery.
Every entity can stay unavailable, and the Refresh button stops working without
any error, until someone restarts PierPressure.

paho reconnects in the background (ADR-0018), but PierPressure ignores every
connection after the first one:

- **Entities stay unavailable.** If the broker published the last-will `offline`
  during the outage, nothing publishes `online` again.
- **Refresh stops working.** PierPressure connects with a clean session, so the
  broker forgets its subscriptions. PierPressure subscribes to the refresh
  commands only once, at startup.
- **Retained state can be lost.** A broker that restarts without saving its
  retained messages forgets every discovery config and state. Nothing publishes
  them again until the next interval.

Story: #44 "reconnect-restores-delivery — after a broker reconnect, entities come
back online and Refresh works".

## What Changes

- **PierPressure subscribes again after each reconnect.** It subscribes to every
  pier's refresh command topic as soon as the broker accepts the new connection.
  If the broker refuses a subscription, PierPressure logs a warning that names
  the topic, at startup and after each reconnect.
- **PierPressure publishes its last state again.** For each pier, it publishes
  the last verdict, narrative and provider health it published before the
  outage. It does not compute a new verdict and does not call the weather
  services. The next interval or a Refresh press brings new data, as today.
- **Then PierPressure goes online.** It publishes the retained `online`
  availability after it has published the state. One narrow exception remains.
  paho resends a message it was still sending when the connection dropped. If
  that message was `online`, it can reach the broker before the replayed state.
  The state follows within moments.
- **A login rejected during a reconnect is logged, not fatal.** The log line says
  the broker rejected the login, with the same advice as at startup. paho keeps
  trying. The same login worked before, so the cause is more likely temporary. A
  rejected login at startup still stops the process, as #33 decided.
- **PierPressure never stops trying to reconnect.** paho's network thread can
  end without notice after one rare kind of failed attempt. At startup,
  PierPressure already starts it again. It now keeps watching for this for as
  long as it runs.
- **The log shows the outage.** PierPressure logs when it loses the connection,
  each failed attempt to reconnect, and when it reconnects.

Out of scope:

- **A publish during the outage.** It still raises `DeliveryError`, which stops
  the process. That is #43. Until #43 lands, this change helps only when the whole
  outage falls between two publishes.
- **A stopped process that stays `online`, and publishes the broker never
  confirms.** That is #41.
- **A persistent session** (`clean_session=False`). It needs a fixed client ID,
  so two instances would disconnect each other. It also would not restore
  `online`.
- **Asking the Supervisor for the login again** after a rejection. This is a
  possible follow-up.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `ha-delivery`: adds a requirement that the process restores its delivery after
  each reconnect: refresh subscriptions, the last state, then `online`. A login
  rejected during a reconnect is logged, and the process keeps trying.

## Impact

- **Changed files:**
  - `pierpressure/delivery/mqtt.py`: the connection handlers act on every
    connection after the first. `MqttDelivery` remembers each pier's last publish
    so it can publish it again.
  - `pierpressure/service.py`: the main thread handles a "reconnected" item from
    the work queue. It publishes the remembered state, then `online`.
  - `pierpressure/__main__.py`: passes the login advice to the delivery adapter,
    so a later rejection gives the same advice as at startup.
  - `tests/conftest.py`: the fake client can drop the connection after startup
    and then accept it again.
- **Tests** cover these cases:
  - Refresh works again after a reconnect, and a refused subscription is logged.
  - The last state, then `online`, is published after a reconnect.
  - No verdict is computed and no weather service is called because of a
    reconnect.
  - The first connection still follows the startup order.
  - A login rejected during a reconnect is logged, and the process keeps running.
- **No change** to the verdict document, MQTT topics, entities, or entity mapping.
- **No new dependencies.**
