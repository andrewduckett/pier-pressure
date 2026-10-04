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
   `/config`, and the add-on reads `/config/config.yaml`. A minimal file for the
   Mosquitto broker add-on:

   ```yaml
   mqtt:
     host: core-mosquitto
     username: pierpressure
     password: your-broker-password
   recompute:
     interval_seconds: 900
   piers:
     - id: backyard
       latitude: 51.50
       longitude: -0.12
       elevation_m: 30
   ```

   `core-mosquitto` is the Mosquitto add-on's host name inside Home Assistant.
   Use a Home Assistant user, or a login from the Mosquitto add-on's settings.
3. **Start the add-on.** Open its **Log** tab. The first line ends with its
   version, for example `PierPressure 2026.10.0`.
4. **Find the entities.** Open **Settings → Devices & services → MQTT**. A device
   named `PierPressure <pier>` appears for each pier.

If the add-on stops straight away, read its log. A configuration error that
names `/config/config.yaml` means the file is missing or not valid.

## Write the password into the file

Outside Home Assistant, `config.yaml` can read the broker password from an
environment variable, as `${PIERPRESSURE_MQTT_PASSWORD}`. An add-on cannot set
its own environment variables, so write the password straight into the file.
Anyone who can open the add-on's config folder can read it.

## More settings

The file has the same format as a Docker install. Horizon files can sit in the
same folder, because a relative `file:` path is read from the folder that holds
`config.yaml`. For every setting, see the
[Configuration section of the README](https://github.com/andrewduckett/pier-pressure#️-configuration).
