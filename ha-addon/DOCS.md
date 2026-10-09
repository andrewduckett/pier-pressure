# PierPressure

PierPressure tells you each evening whether tonight is worth setting up for, and
what to point at from your pier. It publishes its verdict to Home Assistant over
MQTT, so you need an MQTT broker, such as the Mosquitto broker add-on.

This add-on runs the same image as a Docker install. It has no options of its
own: all its settings live in one file, `config.yaml`.

## Set up the add-on

1. **Find the add-on's config folder.** Home Assistant creates it when you
   install the add-on. It is `/addon_configs/<id>_pierpressure`, where `<id>` is
   a short code for this repository. Open it with an add-on that can reach the
   `addon_configs` folder, such as Samba share or Studio Code Server.
2. **Write `config.yaml` in that folder.** Inside the add-on, the folder is
   `/config`, and the add-on reads `/config/config.yaml`. With the Mosquitto
   broker add-on, a minimal file needs no `mqtt:` block:

   ```yaml
   recompute:
     interval_seconds: 900
   piers:
     - id: backyard
       latitude: 51.50
       longitude: -0.12
       elevation_m: 30
   ```

   The add-on asks Home Assistant's Supervisor for the Mosquitto add-on's broker,
   and uses its host, port, username and password. No password goes in the file.
3. **Start the add-on.** Open its **Log** tab. The first line ends with its
   version, for example `PierPressure 2026.10.0`. A later line names the broker,
   for example
   `MQTT broker from the Supervisor's mqtt service: core-mosquitto:1883`.
4. **Find the entities.** Open **Settings → Devices & services → MQTT**. A device
   named `PierPressure <pier>` appears for each pier.

## Use a different broker

To use a broker other than the Mosquitto add-on, set `mqtt.host` in
`config.yaml`. The add-on then takes the host, port, username and password from
the file, all four together, and does not ask the Supervisor:

```yaml
mqtt:
  host: broker.lan
  port: 1883
  username: pierpressure
  password: your-broker-password
```

Write the password straight into the file. An add-on cannot set its own
environment variables, so `${PIERPRESSURE_MQTT_PASSWORD}` is not replaced. Anyone
who can open the add-on's config folder can read the password.

`mqtt.discovery_prefix` and `mqtt.base_topic` always come from the file, whichever
broker you use. You can set them without setting `mqtt.host`.

## If the add-on stops at startup

The add-on stops when it cannot start safely. Its log names the problem in a line
that starts with `Configuration error` or `Startup delivery failure`.

| The log says | What it means | What to do |
| --- | --- | --- |
| It names `/config/config.yaml` | The file is missing, or not valid YAML. | Write or fix `config.yaml`. |
| `mqtt.port`, `mqtt.username` or `mqtt.password` is set without `mqtt.host` | The file sets part of a broker. The add-on takes the broker settings from one place. | Set `mqtt.host` too, or remove the other broker settings. |
| No MQTT broker was found | The file names no `mqtt.host`, and the Supervisor offered no broker within 60 seconds. | Install and start the Mosquitto broker add-on, or set `mqtt.host`. |
| The Supervisor refused access to the mqtt service | Home Assistant would not give this add-on the broker settings. | Set `mqtt.host`, and [report the problem](https://github.com/andrewduckett/pier-pressure/issues). |
| The broker requires TLS | The Supervisor's broker accepts only encrypted connections, which PierPressure does not support yet. | Set `mqtt.host` and `mqtt.port` to a broker listener without TLS. |
| The broker asks for another MQTT version | The Supervisor's broker needs an MQTT version other than 3.1.1. | Set `mqtt.host` and `mqtt.port` to a broker that accepts MQTT 3.1.1. |
| The MQTT broker rejected the login | The broker refused the username and password, or the user is not allowed to connect. | With the Mosquitto add-on, check that add-on. With your own broker, check `mqtt.username`, `mqtt.password`, and the user's permissions on the broker. |

When the Mosquitto add-on is still starting, PierPressure waits up to 60 seconds
for it, and logs one line while it waits.

## If the add-on waits for the broker

PierPressure does not stop when it cannot connect to the broker. It tries again,
and waits longer after each failed try, up to 2 minutes. It publishes nothing
until the broker accepts. Each failed try logs a warning like this one:

```text
Could not connect to the MQTT broker at core-mosquitto:1883 (ConnectionRefusedError); trying again
```

After Home Assistant restarts, a few of these lines are normal while Mosquitto
starts. If they go on, check that the broker is running. With your own broker,
also check `mqtt.host` and `mqtt.port`.

## If the broker stops while the add-on runs

When the broker stops or restarts, PierPressure keeps running and tries to
reconnect, with the same pauses as at startup. Once the broker accepts it again,
PierPressure restores its delivery without a restart:

- The Refresh button works again.
- Each pier's last verdict and provider health are published again, so a broker
  that lost its saved messages gets them back.
- The entities come back online.

A reconnect does not compute a new verdict. The next update, or a Refresh press,
brings new data.

PierPressure restores its delivery only when the outage ends before its next
update. If the broker is still away when an update is due, the add-on can stop
with a `Delivery failure` line. Start the add-on again once the broker is back.

| The log says | What it means | What to do |
| --- | --- | --- |
| Lost the connection to the MQTT broker | The broker stopped, restarted, or became unreachable. PierPressure tries again. | Nothing, if a `Reconnected to the MQTT broker` line follows. If not, check that the broker is running. |
| The MQTT broker rejected the login, followed by `Trying again` | The broker refused a login that worked before. This can happen while the broker restarts. PierPressure keeps trying. | If the line repeats, check the login as the startup table above says. |
| The MQTT broker refused the subscription to a `refresh/command` topic | The broker does not let PierPressure listen for that pier's Refresh button. The button does nothing until this is fixed. | Allow the user to subscribe to the topic on the broker, then restart the add-on. |
| Could not subscribe to a `refresh/command` topic | PierPressure could not ask the broker for that subscription, usually because the connection dropped at that moment. | Nothing, if a `Reconnected to the MQTT broker` line follows. If not, restart the add-on. |

## More settings

The file has the same format as a Docker install. Horizon files can sit in the
same folder, because a relative `file:` path is read from the folder that holds
`config.yaml`. For every setting, see the
[Configuration section of the README](https://github.com/andrewduckett/pier-pressure#️-configuration).
