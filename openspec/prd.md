# PRD: PierPressure

## 1. Background and problem

An amateur astronomer with a permanent pier (or a favourite spot in the garden)
asks the same two questions every clear-looking evening:

- **Is tonight worth setting up for?**
- **If it is, what should I point at from this pier?**

Answering them today means checking several weather sites, a moon calendar, a
planetarium app, and your own memory of which trees block which part of the sky.
That takes long enough that good nights get missed and poor nights waste an hour
of setup.

PierPressure answers both questions automatically and puts the answer where the
household already looks: Home Assistant dashboards and notifications.

## 2. Goals

- Give each pier a single, trustworthy **verdict** for tonight: `GO`, `MAYBE`, or
  `NO-GO`, with a 0–100 score, a confidence, and the reasons behind it.
- Recommend a short, ranked list of **targets** that are actually visible from
  that pier, during real darkness, with the observer's equipment.
- Keep the verdict **fresh on its own**, without depending on Home Assistant to
  schedule or trigger it.
- Make every verdict **explainable** from its itemised reasons, so the user can
  see why the answer is what it is.
- Keep the answer **correct and repeatable**: the same inputs at the same instant
  always give the same verdict.

## 3. Non-goals

- Controlling the mount or running the imaging session. PierPressure recommends;
  it does not operate equipment.
- Cloud hosting, multiple users, or accounts.
- Live all-sky-camera cloud detection. It may become a conditions source later.
- Choosing which host box runs the container. The core does not depend on the
  host.

## 4. Users and context

- **Primary user:** an amateur astronomer or astrophotographer who runs Home
  Assistant at home and observes from one or more fixed piers.
- **Where they see it:** a Home Assistant dashboard card and an automation-driven
  notification. Notification timing is a Home Assistant automation, not part of
  PierPressure.
- **How it runs:** a persistent container on the home network, next to an MQTT
  broker. The container may run inside Home Assistant itself.

## 5. Product overview

For each configured pier, PierPressure:

1. Works out tonight's **astronomical darkness** and the **moon's** behaviour.
2. Fetches **weather conditions** (cloud by layer, wind, seeing, transparency)
   from providers that can fail over to one another.
3. Applies hard **gates**, then a banded **score**, and reports a **confidence**
   that rises as dusk nears and the forecast firms up.
4. Ranks deep-sky **targets** from a vendored catalogue against the pier's
   horizon mask, the moon, the dark window, and the observer's equipment.
5. Publishes one **verdict document** per pier to Home Assistant through MQTT
   discovery, and optionally a plain-language **narrative** of it.

It recomputes on startup, on a configurable interval, and on demand when the user
presses the "show me now" refresh button.

## 6. Functional requirements

### 6.1 Verdict model

- Hard **gates** run first. Any failed gate gives `NO-GO`, a reason, and a null
  score. Gates include: no astronomical darkness tonight; overcast across the dark
  window; and an optional wind-gust limit.
- When every gate passes, a banded **0–100 score** follows. Cloud is split into
  low, mid, and high layers; thin high cloud is scored on its own term because it
  ruins transparency.
- `reasons[]` lists every gate and score term, so the verdict explains itself.
- `confidence {band: LOW|MEDIUM|HIGH, value: 0–100}` reflects forecast lead time
  and freshness.

### 6.2 Sky and light

- The **dark window** is astronomical night: the sun more than 18° below the
  horizon. Polar continuous night and nights with no darkness are handled as
  distinct cases.
- Every target window is **hard-clamped** to astronomical night, whatever view
  window the user asks for. This is a rule, not a preference.
- The **moon** object reports phase, illumination, and when it is above the
  horizon during the dark window.

### 6.3 Piers and horizon masks

- Several piers can be configured, each with its own location and horizon mask.
- The canonical horizon is a sampled list of `(azimuth, altitude)` points. A
  horizon can be given inline, as a flat minimum altitude, or as an exported file.
  The NINA `.hrz` importer is built; Stellarium and Telescopius are recognised
  but not yet supported.
- A target counts only when it clears the mask in its direction.

### 6.4 Targets

- Candidates come from the full OpenNGC catalogue, vendored as pinned in-repo data.
- Ranking factors: time visible in the dark window, altitude above the horizon
  mask, separation from the moon, transit time, brightness, and — when a rig is
  configured — how well the object fits the field of view.
- The top ten fill the structured `targets` list. A top-target sensor is also
  published.
- Ranking is explained in [`docs/target-ranking.md`](../docs/target-ranking.md).

### 6.5 Delivery to Home Assistant

- Entities are created through **MQTT discovery**: per-pier verdict, score, and
  top-target sensors, and a refresh button. REST is an acceptable fallback adapter.
- The verdict document and the MQTT entity mapping are a **frozen contract**. See
  section 8.

### 6.6 Optional narrative

- An optional LLM layer writes a short plain-language narrative of a finished
  verdict and its top targets.
- The narrative is a **separate** Home Assistant sensor, never a field of the
  verdict document or part of `reasons[]`.
- It is off by default, cached on the verdict terms, and the system works fully
  without it. See [`docs/llm-explainer.md`](../docs/llm-explainer.md).

## 7. Configuration

- One YAML file lists the MQTT broker, the recompute interval, and the piers.
- Each pier has a location, a horizon mask, and optionally an equipment rig
  (telescope and camera) and gate limits.
- Any `${VAR}` in a value is replaced from the environment at load time, so the
  broker password need not sit in the file.

## 8. Architecture rules

These rules hold for every change. The hard-to-reverse ones are recorded as
decision records in [`docs/decisions/`](../docs/decisions/).

- **Pure, deterministic core.** The decision core is Python 3.12+ with no Home
  Assistant or MQTT imports. The same inputs, including a pinned evaluation
  instant, give the same verdict document.
- **One contract.** The core emits a single JSON verdict document. That document
  and the MQTT entity mapping are the stable contract. The delivery surface
  (topics, entities, entity mapping) and the meaning of existing fields never
  change. The document may grow **additively**. Reserve a stubbed field only
  when its shape is already known.
- **Home Assistant is never load-bearing.** The container owns its own freshness.
  If Home Assistant restarts, the verdict stays current.
- **No load-bearing data source.** Conditions providers sit behind an interface
  with graceful fallback.
- **The LLM never feeds the math.** Astronomy and ephemeris results never come
  from the LLM.
- **Offline astronomy.** Ephemeris data is version-pinned and computed offline,
  with no network access at runtime.

## 9. Tech stack and deployment

- **Language:** Python 3.12.
- **Astronomy:** Skyfield, Astroplan, Astropy.
- **Conditions:** Open-Meteo as the base provider, with 7Timer! for seeing and
  transparency.
- **Toolchain:** uv, just, ruff (lint and format), mypy, pytest, pre-commit.
  GitHub Actions CI runs `just check`.
- **Deployment:** a Docker container, with a Compose file that includes a local
  Mosquitto broker for development. Home Assistant OS cannot run arbitrary
  containers, so a Home Assistant add-on wraps the same image for those users.
  The add-on is packaging only: it adds no behaviour of its own.

## 10. Success criteria

- On a clear, dark night, the dashboard says `GO` early enough to set up, and the
  top target is one the user would have chosen themselves.
- On a cloudy or moonlit night, the verdict says `NO-GO` or `MAYBE`, and its
  reasons say why.
- Restarting Home Assistant never leaves a stale verdict on the dashboard.
- Losing one weather provider lowers confidence but does not stop the verdict.

## 11. Open questions and future work

- **Target suggestions** in the narrative ("start with M31, it transits at
  01:20"). Deferred so the LLM does not look load-bearing.
- **More conditions sources**, such as a local all-sky camera.
