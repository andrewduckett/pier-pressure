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
that starts with `Configuration error`.

| The log says | What it means | What to do |
| --- | --- | --- |
| It names `/config/config.yaml` | The file is missing, or not valid YAML. | Write or fix `config.yaml`. |
| `mqtt.port`, `mqtt.username` or `mqtt.password` is set without `mqtt.host` | The file sets part of a broker. The add-on takes the broker settings from one place. | Set `mqtt.host` too, or remove the other broker settings. |
| No MQTT broker was found | The file names no `mqtt.host`, and the Supervisor offered no broker within 60 seconds. | Install and start the Mosquitto broker add-on, or set `mqtt.host`. |
| The Supervisor refused access to the mqtt service | Home Assistant would not give this add-on the broker settings. | Set `mqtt.host`, and [report the problem](https://github.com/andrewduckett/pier-pressure/issues). |
| The broker requires TLS | The Supervisor's broker accepts only encrypted connections, which PierPressure does not support yet. | Set `mqtt.host` and `mqtt.port` to a broker listener without TLS. |
| The broker asks for another MQTT version | The Supervisor's broker needs an MQTT version other than 3.1.1. | Set `mqtt.host` and `mqtt.port` to a broker that accepts MQTT 3.1.1. |

When the Mosquitto add-on is still starting, PierPressure waits up to 60 seconds
for it, and logs one line while it waits.

## More settings

The file has the same format as a Docker install. Horizon files can sit in the
same folder, because a relative `file:` path is read from the folder that holds
`config.yaml`. For every setting, see the
[Configuration section of the README](https://github.com/andrewduckett/pier-pressure#️-configuration).
