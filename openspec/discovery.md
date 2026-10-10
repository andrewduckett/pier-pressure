# Discovery: PierPressure

> The living map behind the backlog: who the product serves and the journeys it supports.
> Product intent (scope, goals, non-goals) lives in `openspec/prd.md`.
> Stories are GitHub issues; each discovery run's scope and decisions live in its parent issue.

## Personas

### People who use PierPressure

#### Andrew — the home-pier astrophotographer

- **Who**: an amateur astrophotographer who runs long imaging sessions from a fixed
  pier at home, and whose house already runs on Home Assistant.
- **Goal**: know early in the evening whether tonight is worth a full imaging setup,
  and what to point at from this pier with this rig.
- **Pain today**: answering means checking several weather sites, a moon calendar, a
  planetarium app, and his own memory of which trees block which part of the sky.
  Good nights get missed, and poor nights waste an hour of setup.
- **Success looks like**: one glance at the dashboard, or one notification, answers
  both questions, and he trusts the answer enough to act on it.

#### A fellow Home Assistant astronomer — the adopter

- **Who**: another amateur astronomer, imaging or observing, who already runs Home
  Assistant and an MQTT broker and uses one or more fixed sites.
- **Goal**: get the same go/no-go answer and target list for their own site and gear,
  without reading the source.
- **Pain today**: the same scattered checking Andrew does. Every existing tool also
  expects them to open an app, instead of bringing the answer to them.
- **Success looks like**: they install it, describe their site, horizon, and rig in
  one file, and see a verdict in Home Assistant the same evening.

> **Implication**: Andrew and the adopter walk one journey. The adopter has extra
> stages at the start (find the project, get it running without cloning the repo).
> Build one setup path that works for a stranger. Don't split it into an author path
> and a user path.

### People who build PierPressure

#### Andrew — the maintainer

- **Who**: the same person, maintaining the code.
- **Goal**: add science and fix problems without breaking the frozen verdict contract
  or the deterministic core, and keep pinned data (ephemeris, star catalogue) and
  weather providers current.
- **Pain today**: astronomy code goes wrong quietly. A wrong twilight time or a
  changed weather API can look plausible for weeks.
- **Success looks like**: every change ships as a small, tested PR. A provider outage
  or a data update shows up as a failing check or a lower confidence, never as a
  confidently wrong verdict.

## Journey Map

Stage status checked against the code on 2026-10-10.

### People who use PierPressure

**Tonight at the pier** (Andrew, the adopter):

```
 Find the  ─► Install  ─► Connect ─► Describe ─► See      ─► Get      ─► Choose  ─► Stay current
 project      & run       to HA      my site     tonight's    told in     a target    through the
 (adopter)                (MQTT)                 verdict      time                    night
    │           │           │           │           │            │           │            │
 supported   supported   supported   partial    supported    supported   supported  supported
```

1. **Find the project** (adopter) — the README explains what it does, how to set it
   up, and every config setting and entity — supported
2. **Install and run** — *off Home Assistant*: pull a versioned multi-arch image from
   GHCR. *On Home Assistant OS*: install the add-on from this repository; it runs the
   same image and finds the Mosquitto add-on's broker through the Supervisor —
   supported
3. **Connect to Home Assistant** — MQTT discovery creates one device per pier with
   its entities. The entities go unavailable when PierPressure stops or loses the
   broker, and come back after a reconnect — supported
4. **Describe my site** — location, gates, rig, and the optional explainer are all
   configurable in one file. A horizon can be inline points, a flat floor, or a NINA
   `.hrz` file; Stellarium and Telescopius exports are rejected as not yet
   supported. On Home Assistant OS, writing the file needs a second add-on (Samba
   share or Studio Code Server), because the add-on has no Configuration tab —
   partial ([#69](https://github.com/andrewduckett/pier-pressure/issues/69), [#70](https://github.com/andrewduckett/pier-pressure/issues/70), [#71](https://github.com/andrewduckett/pier-pressure/issues/71), [#72](https://github.com/andrewduckett/pier-pressure/issues/72), [#73](https://github.com/andrewduckett/pier-pressure/issues/73))
5. **See tonight's verdict** — verdict, score, confidence, and reasons; a refresh
   button; an optional plain-language narrative — supported
6. **Get told in time** — the README gives a Home Assistant automation that
   notifies at a chosen time — supported
7. **Choose a target** — the Top target sensor and one sensor per rank, Target 1
   to Target 10, so any dashboard card can list the ranking — supported
8. **Stay current through the night** — the container recomputes on its interval
   and keeps the verdict fresh when Home Assistant restarts — supported

> **Implication**: running on or off Home Assistant differs only at stages 2 and 4.
> Everything after them travels over MQTT, so the add-on is a packaging job, not a
> second product.

### People who build PierPressure

**Ship a change safely** (Andrew, the maintainer):

```
 Open the ─► Pick next ─► Propose  ─► Gate the ─► Prove    ─► Keep data ─► Notice a  ─► Release
 dev shell   story        → archive    change      against     & pins      provider     & deploy
                                                   real HA     current     breaking
    │           │            │            │           │            │           │            │
 supported  supported    supported    supported    partial     supported   supported    partial
```

1. **Open the dev shell** — `flake.nix` and `.envrc` give Python, uv, and just;
   `just check` passes inside it — supported
2. **Pick the next story** — issues with `priority/*` labels, and propose rules in
   `openspec/config.yaml` — supported
3. **Propose → archive** — OpenSpec with the `spec-driven-review` schema — supported
4. **Gate the change** — `just check` and integration tests in CI, CodeQL, and a
   `main` ruleset that requires both — supported
5. **Prove against real Home Assistant** — integration tests run against a real
   Mosquitto broker, but nothing checks a change in a real Home Assistant. The
   manual acceptance checklist was removed because it was too long to run on every
   change, and no lighter way has replaced it — partial
6. **Keep data and pins current** — `docs/data-updates.md` explains how to update
   the pinned ephemeris and catalogue, and Dependabot opens grouped weekly updates
   for uv, Actions, and Docker — supported
7. **Notice a provider breaking** — a diagnostic health sensor per weather
   provider shows when it last succeeded, so a Home Assistant automation can alert
   on a long failure — supported
8. **Release and deploy** — a manual release workflow tags a CalVer version,
   publishes the image and release notes, and opens a pull request that moves the
   add-on to the new version. That pull request can fail after a workflow file
   changes — partial ([#34](https://github.com/andrewduckett/pier-pressure/issues/34))

## Backlog

Stories are GitHub issues: <https://github.com/andrewduckett/pier-pressure/issues>.
