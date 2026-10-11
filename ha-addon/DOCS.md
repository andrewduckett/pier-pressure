# PierPressure

PierPressure tells you each evening whether tonight is worth setting up for, and
what to point at from your pier. It publishes its verdict to Home Assistant over
MQTT, so you need an MQTT broker, such as the Mosquitto broker add-on.

This add-on runs the same image as a Docker install. You set it up on its
**Configuration** tab. For settings the tab does not have yet, you can write a
`config.yaml` file instead.

## Set up the add-on

1. **Open the add-on's Configuration tab.**
2. **Check the recompute interval.** It is how often PierPressure recomputes the
   verdict, in seconds. The default, 900, is 15 minutes.
3. **Add a pier.** Under **Piers**, add an entry for each place you observe from.
   Give it:
   - an **ID**, a short name such as `backyard`. Use only letters, digits and
     underscores, because the ID becomes part of the MQTT topics and entity IDs.
   - its **latitude** and **longitude** in degrees. North and east are positive.
   - its **elevation** above sea level, in metres.
   - optionally, its **horizon**. See [Set a pier's horizon](#set-a-piers-horizon).
   - optionally, its **equipment**. See
     [Set a pier's equipment](#set-a-piers-equipment).
4. **Save, then start the add-on.** The add-on reads the tab only when it starts.
   If it is already running, restart it when Home Assistant offers to, or from
   the **Info** tab.
5. **Check the log.** Open the **Log** tab. The first line ends with the
   version, for example `PierPressure 2026.10.0`. Later lines name where the
   settings and the broker came from:

   ```text
   Settings from the Configuration tab
   MQTT broker from the Supervisor's mqtt service: core-mosquitto:1883
   ```

   The add-on asks Home Assistant's Supervisor for the Mosquitto add-on's broker,
   and uses its host, port, username and password. You enter no password.
6. **Find the entities.** Open **Settings → Devices & services → MQTT**. A device
   named `PierPressure <pier>` appears for each pier.

## Set a pier's horizon

Trees and buildings hide the low sky. A pier's horizon tells PierPressure where
the sky is blocked, so it suggests only targets you can see. A pier with no
horizon has an open, flat horizon at 0°.

Each pier on the Configuration tab has two optional horizon fields. Fill in one
of them at most:

- **Horizon floor** is one altitude, in degrees from 0 to 90, that applies in
  every direction. For example, `15` hides everything lower than 15°.
- **Horizon points** is a list of `[azimuth, altitude]` pairs, in degrees, on one
  line. Azimuth runs from 0 (north) through 90 (east). Between two points, the
  horizon runs in a straight line. For example:

  ```text
  [[0, 10], [90, 25], [180, 5], [270, 15]]
  ```

  The text must start with `[[` and end with `]]`. Otherwise the tab does not
  save it.

**The two fields cannot be used together.** If a pier sets both, or its points
cannot be read, the add-on skips that pier and logs an error that names it. The
other piers still publish. To find the error, open the **Log** tab and look for
`Skipping invalid pier`.

## Set a pier's equipment

A pier's equipment is your telescope and camera. With it, PierPressure also
ranks targets on how well they fit your field of view, and says how the top
pick fits. A pier with no equipment ranks targets without this.

Each pier on the Configuration tab has four optional equipment fields:

| Field | What to enter | Example |
| --- | --- | --- |
| **Focal length** | The telescope's focal length, in millimetres. | `400` |
| **Sensor width** | The camera sensor's width, in millimetres. | `23.5` |
| **Sensor height** | The camera sensor's height, in millimetres. | `15.7` |
| **Reducer or barlow** | The factor of a focal reducer or barlow, with no unit. Leave it empty if you use neither. | `0.8` |

**Set focal length, sensor width and sensor height together.** If a pier sets
some equipment fields but not all three, the add-on skips that pier and logs an
error. **An empty reducer means 1.0**, so a pier without a reducer or barlow
needs only the other three. Every value must be above 0.

The log names a field by its `config.yaml` name, not its label on the tab. For
example, a pier with no sensor height logs these lines, shortened here:

```text
Skipping invalid pier 'backyard': 1 validation error for PierConfig
equipment.sensor_height_mm
  Field required [type=missing, ...]
```

To find the field to fix, match the log's name to the tab's label:

| Label on the tab | Name in the log and in `config.yaml` |
| --- | --- |
| Focal length | `equipment.focal_length_mm` |
| Sensor width | `equipment.sensor_width_mm` |
| Sensor height | `equipment.sensor_height_mm` |
| Reducer or barlow | `equipment.reducer` |

The other piers still publish. When no pier is left, the add-on stops with a
configuration error.

**Before you go back to an older add-on version,** clear the four equipment
fields and save. An older version does not know these fields, and might skip
each pier that still holds them. After you upgrade again, enter the values
again.

## The form or the file

The add-on takes its settings from one place, never a mix of the two:

- **When the Configuration tab lists at least one pier,** the add-on uses only
  the tab. It does not read `config.yaml`. If that file exists, the log warns
  that it is ignored, and the add-on starts as usual.
- **When the Configuration tab lists no piers,** the add-on reads `config.yaml`,
  and ignores the tab's interval.

So to use a setting the tab does not have, such as a horizon file or your own
broker, remove the piers from the tab, and list them in `config.yaml` with that
setting.

## Set up with config.yaml instead

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

3. **Leave the Configuration tab's pier list empty, and start the add-on.** The
   log says `Settings from config.yaml`.

## Use a different broker

To use a broker other than the Mosquitto add-on, set up with `config.yaml`, and
set `mqtt.host` in it. The add-on then takes the host, port, username and
password from the file, all four together, and does not ask the Supervisor:

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

Some answers below say to set `mqtt.host`. That setting lives in `config.yaml`,
which is read only while the Configuration tab lists no piers. When you set up on
the tab, the log says so, and tells you to move your piers into the file too.

| The log says | What it means | What to do |
| --- | --- | --- |
| Nothing is set up | The Configuration tab lists no piers, and `/config/config.yaml` does not exist. | Add a pier on the Configuration tab, then restart the add-on. |
| It names `/config/config.yaml` | The tab lists no piers, and the file is not valid YAML. | Fix `config.yaml`, or add your piers on the Configuration tab. |
| It names `/data/options.json` | The saved Configuration tab values could not be read. This is rare. | Save the Configuration tab again. If the error stays, [report the problem](https://github.com/andrewduckett/pier-pressure/issues). |
| `mqtt.port`, `mqtt.username` or `mqtt.password` is set without `mqtt.host` | The file sets part of a broker. The add-on takes the broker settings from one place. | Set `mqtt.host` too, or remove the other broker settings. |
| No MQTT broker was found | No `mqtt.host` is set, and the Supervisor offered no broker within 60 seconds. | Install and start the Mosquitto broker add-on, or set `mqtt.host`. |
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
- Each pier's latest verdict and provider health are published again, so a broker
  that lost its saved messages gets them back.
- The entities come back online.

A reconnect does not compute a new verdict. The next update, or a Refresh press,
brings new data.

An outage of any length does not stop the add-on. PierPressure still computes
each update while the broker is away. It holds the results and publishes them
once the broker is back.

| The log says | What it means | What to do |
| --- | --- | --- |
| Lost the connection to the MQTT broker | The broker stopped, restarted, or became unreachable. PierPressure tries again. | Nothing, if a `Reconnected to the MQTT broker` line follows. If not, check that the broker is running. |
| The MQTT broker rejected the login, followed by `Trying again` | The broker refused a login that worked before. This can happen while the broker restarts. PierPressure keeps trying. | If the line repeats, check the login as the startup table above says. |
| The MQTT broker refused the subscription to a `refresh/command` topic | The broker does not let PierPressure listen for that pier's Refresh button. The button does nothing until this is fixed. | Allow the user to subscribe to the topic on the broker, then restart the add-on. |
| The MQTT client did not send the publish to a topic | The MQTT client refused one message. This is rare. PierPressure keeps running. | Nothing. The next update, or the next reconnect, publishes that topic again. |
| Could not subscribe to a `refresh/command` topic | PierPressure could not ask the broker for that subscription, usually because the connection dropped at that moment. | Nothing, if a `Reconnected to the MQTT broker` line follows. If not, restart the add-on. |

## More settings

The Configuration tab has only the interval and the piers, with their horizon
floor or points and their equipment, so far. For any other setting, such as a
horizon file, set up with `config.yaml`. The file has the same format as a Docker install. Horizon
files can sit in the same folder, because a relative `file:` path is read from the folder that holds
`config.yaml`. For every setting, see the
[Configuration section of the README](https://github.com/andrewduckett/pier-pressure#️-configuration).
