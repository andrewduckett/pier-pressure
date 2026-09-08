# 🔭 PierPressure

## 🧐 What is this thing?

PierPressure decides **"is tonight worth setting up for, and what should I point
at from this pier?"** and delivers that verdict into Home Assistant. A pure
Python core computes a single deterministic **verdict document** per pier; an
MQTT-discovery adapter turns it into Home Assistant entities you can put on a
dashboard and trigger notifications from.

This is the **M1 walking skeleton**: the full pipe (config → verdict document →
MQTT entities → refresh on demand) works end to end, but the decision values are
**stubbed** (`verdict: MAYBE`, `score: 50`). The document contract and the MQTT
entity mapping are real and frozen; later milestones fill in the astronomy,
conditions, and target ranking behind the same contract.

## 🧩 The Problem

Home Assistant should not be load-bearing for a verdict's freshness or
correctness, and the hard risk in a project like this is the *plumbing*, not the
math. PierPressure retires that risk first: the core runs as a persistent
container that owns its own freshness (recompute on startup, on an interval, and
on demand), so if Home Assistant restarts the verdict stays current.

## ✨ Why is this worth solving

Freezing the contract now means every later milestone replaces a stub with real
math instead of rewiring Home Assistant late. See `docs/roadmap.md` for the
milestone plan.

## 📦 Install

Requires [uv](https://docs.astral.sh/uv/) and [just](https://github.com/casey/just).

```bash
just install     # uv sync: environment, dependencies, lockfile
```

## ⚙️ Usage

Write a `config.yaml` (see below), then run:

```bash
export PIERPRESSURE_MQTT_PASSWORD='your-broker-password'
just run                       # uv run python -m pierpressure
# or point at a specific file:
uv run python -m pierpressure /path/to/config.yaml
```

Or as a container:

```bash
docker build -t pierpressure .
docker run --rm \
  -v "$PWD/config.yaml:/app/config.yaml" \
  -e PIERPRESSURE_MQTT_PASSWORD='your-broker-password' \
  pierpressure
```

### Configuration

```yaml
mqtt:
  host: 192.168.1.10
  port: 1883
  username: pierpressure
  password: ${PIERPRESSURE_MQTT_PASSWORD}   # env override; avoids plaintext
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

**The `${ENV}` password override.** Any `${VAR}` in a config value is replaced
with that environment variable at load time, so the broker password need not sit
in plaintext in the file. Set it in the environment (e.g.
`export PIERPRESSURE_MQTT_PASSWORD=...` or `-e` on `docker run`). If the variable
is unset, the literal `${VAR}` is left in place rather than silently blanked, so a
missing secret is visible.

`piers` is a list even though M1 runs with one. Each pier is validated
independently: an invalid pier is logged and skipped while valid piers keep
running; a config with **no** valid pier exits non-zero.

### MQTT entities

Publishing a pier `<pier>` creates one Home Assistant **device**
(`PierPressure <pier>`) grouping three entities, and uses these topics:

| Entity / purpose | Topic | Retain |
|---|---|---|
| Verdict sensor (discovery) | `homeassistant/sensor/pierpressure_<pier>/verdict/config` | yes |
| Score sensor (discovery) | `homeassistant/sensor/pierpressure_<pier>/score/config` | yes |
| Refresh button (discovery) | `homeassistant/button/pierpressure_<pier>/refresh/config` | yes |
| Verdict state (`GO`/`MAYBE`/`NO-GO`) | `pierpressure/<pier>/verdict/state` | yes |
| Document attributes (JSON) | `pierpressure/<pier>/verdict/attributes` | yes |
| Refresh command | `pierpressure/<pier>/refresh/command` | no |
| Availability (LWT) | `pierpressure/status` | yes |

- **Verdict** (sensor): state is `GO`, `MAYBE`, or `NO-GO`; the reasons, score,
  confidence, night window, pier id, and generation timestamp are JSON attributes.
- **Score** (sensor): the numeric 0–100 score. On a gated `NO-GO` the score is
  `null` and the entity renders **unavailable** rather than `0`.
- **Refresh** (button): a "show me now" control that triggers an immediate
  recompute and republish for that pier.

### Notifying at a chosen time (Home Assistant automation)

The core owns *what* the verdict is and *when it is recomputed*; **you** own
*when you are told*. This automation checks the verdict at 19:00 and pushes a
notification when tonight is worth setting up (verdict is not `NO-GO`):

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
            (score {{ state_attr('sensor.pierpressure_backyard_verdict', 'score') }})
```

Because state is republished on startup, on interval, and on demand, the
automation reads the current verdict whenever it fires.

### Removing PierPressure entities from Home Assistant

Entities are created via retained discovery messages, so to remove them cleanly
publish an **empty retained payload** to each discovery config topic. For a pier
`backyard`:

```bash
mosquitto_pub -r -t 'homeassistant/sensor/pierpressure_backyard/verdict/config' -n
mosquitto_pub -r -t 'homeassistant/sensor/pierpressure_backyard/score/config'   -n
mosquitto_pub -r -t 'homeassistant/button/pierpressure_backyard/refresh/config' -n
```

(`-r` retained, `-n` empty message.) Home Assistant removes an entity when its
discovery topic is cleared.

## 🏗️ Design Notes

- **Pure core, dumb adapter.** `pierpressure/core/` has no Home Assistant or MQTT
  imports and emits one JSON verdict document. `pierpressure/delivery/` publishes
  it. The boundary is enforced by a test.
- **Deterministic.** Same inputs (including a pinned evaluation instant via an
  injectable clock) yield a byte-identical document.
- **Freshness is the container's job.** Startup + interval + on-demand recompute;
  a Last-Will marks entities unavailable if the process dies.

The full rationale lives in `openspec/changes/add-walking-skeleton/design.md` and
the repository ADRs under `docs/adr/`.

## 📁 Project Layout

```
pierpressure/
  core/        # pure decision core: model, clock, config, producer (no delivery)
  delivery/    # MQTT discovery publisher + command subscriber
  service.py   # persistent loop wiring the two together
  __main__.py  # entrypoint: python -m pierpressure
tests/         # core tests need no broker; delivery tests use a fake client
docs/          # roadmap, ADRs, and the M1 acceptance checklist
```

## 🛠️ Development

```bash
just lint        # ruff check
just format      # ruff format
just typecheck   # mypy
just test        # pytest (integration tests deselected by default)
just check       # lint + typecheck + test — the CI gate
```

Optional integration tests exercise a real local broker and are deselected by
default; run them against a local Mosquitto with `uv run pytest -m integration`.

The **M1 manual acceptance checklist** — the end-to-end proof against real Home
Assistant — is in [`docs/acceptance/m1-ha-acceptance.md`](docs/acceptance/m1-ha-acceptance.md).

## 🤖 For AI Agents

This project uses OpenSpec. Planning artifacts for in-flight work live under
`openspec/changes/`; durable cross-cutting rules are in `docs/roadmap.md` and
`docs/adr/`. The core must stay pure (no HA/MQTT imports) and deterministic, and
the verdict document plus MQTT entity mapping are a **frozen contract** — reserve
new fields stubbed rather than reshaping either surface.
