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

Stage status checked against the code on 2026-10-03.

### People who use PierPressure

**Tonight at the pier** (Andrew, the adopter):

```
 Find the  ─► Install  ─► Connect ─► Describe ─► See      ─► Get      ─► Choose  ─► Stay current
 project      & run       to HA      my site     tonight's    told in     a target    through the
 (adopter)                (MQTT)                 verdict      time                    night
    │           │           │           │           │            │           │            │
 supported   partial     supported   partial    supported    supported   partial    supported
```

1. **Find the project** (adopter) — the README explains what it does, how to set it
   up, and every config setting and entity — supported
2. **Install and run** — *off Home Assistant*: the user builds the Docker image
   from the repository, because no image is published. *On Home Assistant*: there is
   no add-on yet — partial ([#21](https://github.com/andrewduckett/pier-pressure/issues/21), [#23](https://github.com/andrewduckett/pier-pressure/issues/23), [#28](https://github.com/andrewduckett/pier-pressure/issues/28))
3. **Connect to Home Assistant** — MQTT discovery creates one device per pier with
   its entities, and a last-will message marks them unavailable if the container
   stops — supported
4. **Describe my site** — location, gates, rig, and the optional explainer are all
   configurable. A horizon can be inline points, a flat floor, or a NINA `.hrz`
   file; Stellarium and Telescopius exports are rejected as not yet supported —
   partial
5. **See tonight's verdict** — verdict, score, confidence, and reasons; a refresh
   button; an optional plain-language narrative — supported
6. **Get told in time** — the README gives a Home Assistant automation that
   notifies at a chosen time — supported
7. **Choose a target** — the Top target sensor shows the best target. The full
   ranked list is only in JSON attributes, with no dashboard card to show it —
   partial ([#24](https://github.com/andrewduckett/pier-pressure/issues/24))
8. **Stay current through the night** — the container recomputes on its interval
   and keeps the verdict fresh when Home Assistant restarts — supported

> **Implication**: running on or off Home Assistant differs only at stage 2.
> Everything after it travels over MQTT, so an add-on is a packaging job, not a
> second product.

### People who build PierPressure

**Ship a change safely** (Andrew, the maintainer):

```
 Open the ─► Pick next ─► Propose  ─► Gate the ─► Prove    ─► Keep data ─► Notice a  ─► Release
 dev shell   story        → archive    change      against     & pins      provider     & deploy
                                                   real HA     current     breaking
    │           │            │            │           │            │           │            │
 supported  supported    supported    supported    partial     partial     partial        gap
```

1. **Open the dev shell** — `flake.nix` and `.envrc` give Python, uv, and just;
   `just check` passes inside it — supported
2. **Pick the next story** — issues with `priority/*` labels, and propose rules in
   `openspec/config.yaml` — supported
3. **Propose → archive** — OpenSpec with the `spec-driven-review` schema — supported
4. **Gate the change** — `just check` and integration tests in CI, CodeQL, and a
   `main` ruleset that requires both — supported
5. **Prove against real Home Assistant** — integration tests run against a real
   Mosquitto broker, but the manual Home Assistant checklist covers only the first
   delivery surface, not the top-target or narrative entities — partial
   ([#22](https://github.com/andrewduckett/pier-pressure/issues/22))
6. **Keep data and pins current** — the ephemeris and the OpenNGC catalogue are
   pinned, but there is no documented way to update them and no automated
   dependency updates — partial ([#26](https://github.com/andrewduckett/pier-pressure/issues/26), [#27](https://github.com/andrewduckett/pier-pressure/issues/27))
7. **Notice a provider breaking** — fallback keeps the verdict going and
   failures are logged, but nothing tells the maintainer that a provider has been
   failing for days — partial ([#25](https://github.com/andrewduckett/pier-pressure/issues/25))
8. **Release and deploy** — no version tags, release notes, or published image;
   deploying means building the image on the host — gap ([#21](https://github.com/andrewduckett/pier-pressure/issues/21))

## Backlog

Stories are GitHub issues: <https://github.com/andrewduckett/pier-pressure/issues>.
