# 🔭 PierPressure

PierPressure answers two questions every evening: **"Is tonight worth setting up
for?"** and **"What should I point at from this pier?"** It puts the answer in Home
Assistant, where you can show it on a dashboard and send notifications from it.

For each pier you configure, it:

- works out tonight's astronomical darkness and what the moon is doing
- reads cloud, wind, seeing, and transparency forecasts
- gives a verdict of `GO`, `MAYBE`, or `NO-GO`, with a 0–100 score, a confidence,
  and the reasons behind it
- ranks the ten best deep-sky targets for your horizon and your gear
- optionally writes a short plain-language summary of the verdict

It runs as a small container next to your MQTT broker. It recomputes on its own
schedule, so the verdict stays current even when Home Assistant restarts.

## ✨ Why

Deciding whether to set up usually means checking several weather sites, a moon
calendar, a planetarium app, and your memory of which trees block which part of
the sky. That takes long enough that good nights get missed and poor nights waste
an hour of setup. PierPressure does those checks for you and brings the answer to
you. The full product intent is in [`openspec/prd.md`](openspec/prd.md).

## 🚀 Quick start

You need an MQTT broker that Home Assistant already uses, with
[MQTT discovery](https://www.home-assistant.io/integrations/mqtt/#mqtt-discovery)
turned on (it is on by default).

1. Write a `config.yaml` (see [Configuration](#️-configuration)).
2. Pick a version from the
   [releases page](https://github.com/andrewduckett/pier-pressure/releases) and
   run that image. This example pins `2026.10.0`:

   ```bash
   docker run -d --restart unless-stopped \
     -v "$PWD/config.yaml:/app/config.yaml:ro" \
     -e PIERPRESSURE_MQTT_PASSWORD='your-broker-password' \
     ghcr.io/andrewduckett/pier-pressure:2026.10.0
   ```

   The image runs on `linux/amd64` and `linux/arm64`, such as a Raspberry Pi.
   The `latest` tag always points at the newest release, but a pinned version
   only changes when you change it.

3. In Home Assistant, open **Settings → Devices & services → MQTT**. A device
   named `PierPressure <pier>` appears for each pier.

The first line the container logs is its version, for example
`PierPressure 2026.10.0`. Include it when you report a problem.

To build the image from this repository instead:

```bash
docker build -t pierpressure .
```

Then run it as in step 2, with `pierpressure` as the image name. An image you
build yourself reports the version `0.0.0+unreleased`.

To run from source instead, install [uv](https://docs.astral.sh/uv/) and
[just](https://github.com/casey/just), then:

```bash
just install                   # create the environment
just run                       # reads ./config.yaml
uv run python -m pierpressure /path/to/config.yaml   # or name a file
```

## ⚙️ Configuration

A minimal file needs the broker, a recompute interval, and one pier:

```yaml
mqtt:
  host: 192.168.1.10
  port: 1883                                # optional (default shown)
  username: pierpressure                    # optional
  password: ${PIERPRESSURE_MQTT_PASSWORD}   # read from the environment
  discovery_prefix: homeassistant           # optional (default shown)
  base_topic: pierpressure                  # optional (default shown)
recompute:
  interval_seconds: 900
piers:
  - id: backyard
    latitude: 51.50
    longitude: -0.12
    elevation_m: 30
```

A fuller pier uses the optional settings:

```yaml
piers:
  - id: backyard
    latitude: 51.50
    longitude: -0.12
    elevation_m: 30
    go_threshold: 65          # score needed for GO (default 65)
    max_gust: 30              # km/h; a higher forecast gust means NO-GO (off by default)
    horizon:
      file: horizons/backyard.hrz   # relative to this config file
      format: nina
    rig:
      focal_length_mm: 400
      sensor_width_mm: 23.5
      sensor_height_mm: 15.7
      reducer: 1.0            # optional; below 1 is a reducer, above 1 a barlow
```

| Setting | What it does |
|---|---|
| `piers` | A list. Each pier is checked on its own: an invalid pier is logged and skipped, and the others keep running. If no pier is valid, PierPressure exits with an error. |
| `go_threshold` | The score a night needs for `GO`. |
| `max_gust` | Turns on the wind gate. Leave it out to ignore wind gusts. |
| `horizon` | Exactly one of: `points` (a list of `[azimuth, altitude]` pairs), `min_altitude` (a flat floor in degrees), or `file` + `format`. Without it the horizon is flat at 0°. The only file format supported today is `nina` (a NINA `.hrz` export). `stellarium` and `telescopius` are recognised but rejected as not yet supported. |
| `rig` | Your telescope and camera. With a rig, targets are also ranked on how well they fit the field of view. |
| `explainer` | The optional LLM summary. See [docs/llm-explainer.md](docs/llm-explainer.md). |

**Secrets.** Any `${VAR}` in a value is replaced with that environment variable
when the file loads, so passwords and API keys need not sit in the file. If the
variable is not set, the literal `${VAR}` stays in place, so a missing secret is
easy to spot.

## 🏠 Home Assistant entities

Each pier becomes one device, `PierPressure <pier>`, with these entities:

| Entity | State | Notes |
|---|---|---|
| **Verdict** (sensor) | `GO`, `MAYBE`, or `NO-GO` | The full verdict document is in its attributes. |
| **Score** (sensor) | 0–100 | Shows as unavailable on a `NO-GO` caused by a gate, rather than `0`. |
| **Top target** (sensor) | The best target's name, or its catalogue id | The full ranked list is in its attributes. Unavailable when nothing is rankable. See [docs/target-ranking.md](docs/target-ranking.md). |
| **Refresh** (button) | — | "Show me now": recomputes and republishes straight away. |
| **Narrative** (sensor) | `ready` or unavailable | Only when the explainer is on. The text is in its attributes. |

If the container stops, its last-will message marks every entity unavailable.

<details>
<summary>MQTT topics</summary>

| Purpose | Topic | Retained |
|---|---|---|
| Discovery configs | `homeassistant/<sensor\|button>/pierpressure_<pier>/<verdict\|score\|top_target\|narrative\|refresh>/config` | yes |
| Verdict state | `pierpressure/<pier>/verdict/state` | yes |
| Verdict document | `pierpressure/<pier>/verdict/attributes` | yes |
| Top target state and list | `pierpressure/<pier>/top_target/state`, `.../top_target/attributes` | yes |
| Narrative state and text | `pierpressure/<pier>/narrative/state`, `.../narrative/attributes` | yes |
| Refresh command | `pierpressure/<pier>/refresh/command` | no |
| Availability | `pierpressure/status` | yes |

</details>

### The verdict document

The Verdict sensor's attributes hold one JSON document. Every key is always
present; a value with no data is `null`, never left out. Times are UTC ISO-8601,
to the whole second, ending in `Z`.

| Field | Type | Meaning |
|---|---|---|
| `pier` | string | The pier id from the config. |
| `generated_at` | timestamp | When this document was computed. |
| `verdict` | `GO` \| `MAYBE` \| `NO-GO` | The decision. |
| `score` | 0–100 or `null` | The banded score when every gate passes; `null` when a gate fails. |
| `confidence` | object | `{ band: LOW\|MEDIUM\|HIGH, value: 0–100 }`. Rises as dusk nears and the forecast firms up. |
| `reasons` | list of strings | Each gate and score term, so the verdict explains itself. |
| `targets` | list | Up to ten ranked targets. Each has `id`, `name`, `type`, `score`, `window`, `max_altitude`, `transit_time`, `moon_separation`, `size_arcmin`, `magnitude`, and `surface_brightness`. |
| `dark_window` | object | Tonight's astronomical night: `{ start, end }`. |
| `moon` | object | The moon's illumination, phase, and behaviour during the dark window. |

**`dark_window`** is when the sun's centre is more than 18° below the horizon.
"Tonight" is the night whose dawn is the first one at or after `generated_at`, so
it is right whether you ask in the afternoon or after midnight.

- `start` and `end` are astronomical dusk and dawn.
- Both are `null` when there is no astronomical darkness, for example in a
  high-latitude summer.
- During continuous polar night, the window is not null. It is anchored to the
  local solar day.

**`moon`** always has `illumination` and `phase`. Its other fields are `null`
when there is no dark window.

- `illumination`: the lit fraction, `0`–`1`, to two decimal places.
- `phase`: `new`, `waxing crescent`, `first quarter`, `waxing gibbous`, `full`,
  `waning gibbous`, `last quarter`, or `waning crescent`.
- `up_during_dark`: whether the moon is above the horizon at any point in the
  dark window.
- `rise`, `set`: moonrise and moonset **inside** the dark window, or `null`.
  "Above the horizon" means the moon's centre is above 0° altitude, with no
  refraction correction.

The astronomy uses a version-pinned ephemeris and runs fully offline. The same
pier and instant always give the same document. See
[`docs/decisions/0004-deterministic-offline-astronomy.md`](docs/decisions/0004-deterministic-offline-astronomy.md).

### Getting a notification

PierPressure decides *what* the verdict is and *when* to recompute it. **You**
decide when to be told, with a Home Assistant automation. This one checks at 19:00
and notifies you unless the verdict is `NO-GO`:

```yaml
automation:
  - alias: "PierPressure — notify if tonight is worth it"
    trigger:
      - platform: time
        at: "19:00:00"
    condition:
      - condition: not
        conditions:
          - condition: state
            entity_id: sensor.pierpressure_backyard_verdict
            state: "NO-GO"
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "Tonight looks good 🔭"
          message: >
            Verdict: {{ states('sensor.pierpressure_backyard_verdict') }}
            (score {{ state_attr('sensor.pierpressure_backyard_verdict', 'score') }}),
            start with {{ states('sensor.pierpressure_backyard_top_target') }}
```

### Removing the entities

Home Assistant removes an entity when its discovery topic is cleared. Publish an
empty retained message to each discovery topic. For a pier called `backyard`:

```bash
for e in sensor/pierpressure_backyard/verdict sensor/pierpressure_backyard/score \
         sensor/pierpressure_backyard/top_target sensor/pierpressure_backyard/narrative \
         button/pierpressure_backyard/refresh; do
  mosquitto_pub -r -n -t "homeassistant/$e/config"
done
```

## 🏗️ How it is built

- **Pure core, simple adapter.** `pierpressure/core/` has no Home Assistant or MQTT
  imports and produces one JSON verdict document. `pierpressure/delivery/`
  publishes it. A test enforces the boundary.
- **Deterministic.** The same inputs, including a pinned evaluation time, give a
  byte-identical document.
- **Frozen contract.** Topics, entities, and the meaning of existing fields never
  change. The document only gains new fields.
- **No single weather source is required.** Providers (Open-Meteo, 7Timer!) sit
  behind one interface, with caching and fallback.
- **The LLM never touches the numbers.** It only explains a finished verdict.

The reasons behind each choice are in the decision records under
[`docs/decisions/`](docs/decisions/).

```
pierpressure/
  core/          # pure decision core: config, sky, scoring, ranking, model
  conditions/    # weather providers (Open-Meteo, 7Timer!) with caching and fallback
  delivery/      # MQTT discovery publisher and refresh-command subscriber
  explain/       # optional LLM narrative
  data/openngc/  # vendored OpenNGC catalogue (CC BY-SA 4.0)
  service.py     # the persistent loop that wires these together
tests/           # core tests need no broker; delivery tests use a fake client
docs/            # decision records and guides
openspec/        # product intent, discovery map, specs, and change history
```

## 🛠️ Development

With [Nix](https://nixos.org) and [direnv](https://direnv.net), `cd` into the repo
and run `direnv allow` once. The dev shell provides Python 3.12, uv, and just.
Without Nix, install uv and just yourself.

```bash
just install     # uv sync
just lint        # ruff check
just format      # ruff format
just typecheck   # mypy
just test        # pytest (integration tests are skipped by default)
just check       # lint + typecheck + test: the CI gate
just test-integration   # runs integration tests against a throwaway Mosquitto
```

`docker compose --profile full up` runs PierPressure against a local broker.

### Releasing

Releases are for the maintainer. Each one publishes an image to
`ghcr.io/andrewduckett/pier-pressure` and creates a GitHub release.

1. On GitHub, open **Actions → Release → Run workflow**, choose `main`, and run
   it. The workflow re-runs `just check`, builds and pushes the image for amd64
   and arm64, and then tags the commit and creates the release.
2. The version is monthly CalVer, `YYYY.M.N`: the UTC year and month, and a
   counter that starts at 0 each month. The first release in October 2026 is
   `2026.10.0`, the next is `2026.10.1`. The git tag is the only place the
   version is stored ([ADR-0013](docs/decisions/0013-calver-versions-from-git-tags.md)).
3. A commit is released at most once. Running the workflow again on a commit
   that already has a release tag fails.

After the **first** release only, make the package public: open the package on
GitHub, then **Package settings → Change visibility → Public**. Then pull the
version tag from a machine that is not logged in to GHCR, run it, and check that
the first log line shows the version.

To undo a release, delete the GitHub release, its git tag and the package version
on GHCR. If it was the newest release, `latest` is deleted with it. Point
`latest` back at the previous release, for example `2026.10.0`:

```bash
docker buildx imagetools create -t ghcr.io/andrewduckett/pier-pressure:latest \
  ghcr.io/andrewduckett/pier-pressure:2026.10.0
```

Planned work is in [GitHub issues](https://github.com/andrewduckett/pier-pressure/issues).
AI agents should start with [`AGENTS.md`](AGENTS.md).

## 📄 License

MIT. See [LICENSE](LICENSE). The OpenNGC catalogue is CC BY-SA 4.0; see
[NOTICE](NOTICE).
