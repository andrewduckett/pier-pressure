# PierPressure

PierPressure tells you each evening whether tonight is worth setting up for, and
what to point at from your pier. It publishes its verdict to Home Assistant over
MQTT, so you need an MQTT broker, such as the Mosquitto broker add-on.

This add-on runs the same image as a Docker install. You set it up on its
**Configuration** tab. For settings the tab does not show, such as a horizon
file, you add a `config.yaml` file. See
[Add settings with config.yaml](#add-settings-with-configyaml).

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
   and uses its host, port, username and password. You enter no password. To use
   another broker, see [Use a different broker](#use-a-different-broker).
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

## Add settings with config.yaml

The Configuration tab lists your piers. A `config.yaml` file can add the
settings the tab leaves unset. The add-on combines the two each time it starts.
The file is optional.

### Write the file

1. **Find the add-on's config folder.** Home Assistant creates it when you
   install the add-on. It is `/addon_configs/<id>_pierpressure`, where `<id>` is
   a short code for this repository. Open it with an add-on that can reach the
   `addon_configs` folder, such as Samba share or Studio Code Server.
2. **Write `config.yaml` in that folder.** Inside the add-on, the folder is
   `/config`, and the add-on reads `/config/config.yaml`. The file uses the same
   names as a Docker install, but holds only the settings you add.
3. **Restart the add-on.** When the file adds a setting, the log says:

   ```text
   Settings from the Configuration tab and config.yaml
   ```

### What the file can add

- **For a pier:** any pier setting the tab leaves unset. Examples are a horizon
  file (`horizon` with `file` and `format`), `go_threshold` and `max_gust`.
  List the pier under `piers:` with the same `id` as on the tab, and add only
  the settings you want.
- **For the whole add-on:** `explainer`, `mqtt.discovery_prefix` and
  `mqtt.base_topic`. The file can also set the broker, when the tab's broker
  fields are empty. See [With config.yaml](#with-configyaml).

**The file cannot add a pier.** Every pier in `config.yaml` must also be on the
tab, with the same ID. A file that lists piers while the tab lists none stops
the add-on with "Nothing is set up".

### Example: a horizon file

Say the tab lists the pier `backyard` and leaves its horizon fields empty. You
exported your horizon from NINA as `backyard.hrz`.

1. Put `backyard.hrz` in the add-on's config folder, beside `config.yaml`.
2. Write this `config.yaml`:

   ```yaml
   piers:
     - id: backyard
       horizon:
         file: backyard.hrz
         format: nina
   ```

3. Restart the add-on.

A relative `file:` path is read from the folder that holds `config.yaml`.

### Each setting comes from one place

If the tab and the file both set the same setting, the add-on stops. Its
configuration error names the setting and the pier. Clear the setting in one of
the two places, then restart.

A field you leave empty on the tab is not set. A value of 0 is set. Each row
below counts as one setting, so set it in one place only:

| Setting | On the Configuration tab | In `config.yaml` |
| --- | --- | --- |
| A pier's horizon | **Horizon floor** or **Horizon points** | the pier's `horizon` |
| A pier's equipment | any of the four equipment fields | the pier's `equipment` |
| The broker connection | **Host**, **Port**, **Username** or **Password** | `mqtt.host`, `mqtt.port`, `mqtt.username` or `mqtt.password` |
| The recompute interval | **Recompute interval** | `recompute` |

Every other setting, such as a pier's `latitude`, counts on its own. The tab
always sets the recompute interval, so a `recompute` block in the file is always
an error.

The error lists every problem it finds, so you can fix them all before you
restart. It names settings and piers, never their values.

## Use a different broker

By default, the add-on uses the Mosquitto broker add-on. To use another broker,
fill in the **MQTT broker** fields on the Configuration tab:

| Field | What to enter | Example |
| --- | --- | --- |
| **Host** | The broker's host name or IP address. | `broker.lan` |
| **Port** | The broker's port. Leave it empty for 1883, the usual MQTT port. | `1884` |
| **Username** | The name the add-on logs in with, if the broker needs a login. | `pierpressure` |
| **Password** | The password for that name. | |

**The host decides where the broker comes from.** When you set a host, the
add-on takes the host, port, username and password from the tab, all four
together, and does not ask the Supervisor. When you leave the host empty, you
must leave the other three empty too. The add-on then uses the broker in
`config.yaml`, if the file sets `mqtt.host`, or else the Mosquitto add-on. A
port, username or password without a host stops the add-on with a
configuration error.

**The password field hides its value on the tab.** Home Assistant's Supervisor
stores the value with the add-on's other saved settings. It is not written into
`config.yaml`.

After you save and restart, the log names the tab as the broker's source:

```text
MQTT broker from the Configuration tab: broker.lan:1884
```

### With config.yaml

You can set the broker in `config.yaml` instead, with `mqtt.host`. Leave the
tab's four broker fields empty; a broker set in both places stops the add-on.
The same rule applies: with a host, all four settings come from the file. The
log then says `MQTT broker from config.yaml`.

The file is plain text that anyone who can open the add-on's config folder can
read, and an add-on cannot replace `${PIERPRESSURE_MQTT_PASSWORD}` from its
environment. For a broker that needs a password, use the Configuration tab.

`mqtt.discovery_prefix` and `mqtt.base_topic` can be set only in the file. They
come from the file, or from their defaults, whichever broker you use. You can set
them without setting `mqtt.host`.

## If the add-on stops at startup

The add-on stops when it cannot start safely. Its log names the problem in a line
that starts with `Configuration error` or `Startup delivery failure`.

Some answers below say to set `mqtt.host`, or the broker settings. Set them on
the Configuration tab or in `config.yaml`, not in both. See
[Use a different broker](#use-a-different-broker).

| The log says | What it means | What to do |
| --- | --- | --- |
| Nothing is set up | The Configuration tab lists no piers. `config.yaml` cannot list piers on its own. | Add a pier on the Configuration tab, then restart the add-on. If the error names piers from `config.yaml`, add each one on the tab with the same ID, and keep only the extra settings in the file. |
| `/config/config.yaml` is not valid YAML | The file has a mistake at the line and column the log names. | Fix `config.yaml` at that place, then restart. |
| The Configuration tab and config.yaml do not combine | One or more problems, each named in the same line. | Fix each problem as the rows below say, then restart. |
| … is set on the Configuration tab and in config.yaml | The tab and the file both set the named setting. See [Each setting comes from one place](#each-setting-comes-from-one-place). | Clear the setting in one of the two places. |
| Pier … in config.yaml is not on the Configuration tab | The file lists a pier ID that the tab does not. | Add the pier on the tab with the same ID, or fix the ID in the file. |
| Pier … is listed more than once in config.yaml, or it names an entry in the piers list | A file pier is repeated, is not a list of settings, or has no ID. | List each pier once, each with an `id`. |
| It names `/data/options.json` | The saved Configuration tab values could not be read. This is rare. | Save the Configuration tab again. If the error stays, [report the problem](https://github.com/andrewduckett/pier-pressure/issues). |
| `mqtt.port`, `mqtt.username` or `mqtt.password` is set without `mqtt.host` | The tab or the file sets part of a broker without a host. | Set `mqtt.host` too, or remove the other broker settings. |
| No MQTT broker was found | No `mqtt.host` is set, and the Supervisor offered no broker within 60 seconds. | Install and start the Mosquitto broker add-on, or set `mqtt.host`. |
| The Supervisor refused access to the mqtt service | Home Assistant would not give this add-on the broker settings. | Set `mqtt.host`, and [report the problem](https://github.com/andrewduckett/pier-pressure/issues). |
| The broker requires TLS | The Supervisor's broker accepts only encrypted connections, which PierPressure does not support yet. | Set `mqtt.host` and `mqtt.port` to a broker listener without TLS. |
| The broker asks for another MQTT version | The Supervisor's broker needs an MQTT version other than 3.1.1. | Set `mqtt.host` and `mqtt.port` to a broker that accepts MQTT 3.1.1. |
| The MQTT broker rejected the login | The broker refused the username and password, or the user is not allowed to connect. | With the Mosquitto add-on, check that add-on. With your own broker, check the username and password, and the user's permissions on the broker. |

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

The Configuration tab has only the interval, the piers, with their horizon floor
or points and their equipment, and the broker, so far. Add any other setting,
such as a horizon file, in `config.yaml`. See
[Add settings with config.yaml](#add-settings-with-configyaml). For every
setting, see the
[Configuration section of the README](https://github.com/andrewduckett/pier-pressure#️-configuration).
