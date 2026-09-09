## Why

PierPressure's hardest risks are not the astronomy — they are whether a computed verdict can reliably reach a Home Assistant dashboard and refresh on demand, and whether the verdict document has a stable shape the later science can pour into. This change builds the thinnest end-to-end slice (a "walking skeleton") that proves the whole pipe with a stubbed verdict, so every later milestone replaces a stub with real math behind a frozen contract instead of rewiring Home Assistant late.

## What Changes

- Introduce a **pure Python core** (no Home Assistant imports) that emits **one deterministic JSON verdict document** for a single configured pier. In this change the verdict, score, and confidence are **stubbed** — the document *contract* is real and tested; the scoring and conditions math arrive in later milestones.
- Define the **verdict document contract**: `verdict` (GO | MAYBE | NO-GO), `score` (0–100, or null when NO-GO by gate), `confidence` (`{band: LOW|MEDIUM|HIGH, value: 0–100}`), `reasons` (string list), `targets` (list, empty until the ranking milestone), `dark_window` (`{start, end}` astronomical dusk→dawn, null until the sky-math milestone), plus identifying metadata (pier id, generation timestamp). `confidence` and `dark_window` are stubbed in this change; their shape is frozen now so later milestones fill them without reshaping the document.
- Deliver the verdict into Home Assistant via an **MQTT discovery publisher** adapter that auto-creates per-pier entities (a verdict sensor and a score sensor, with confidence, reasons, night window, and metadata as attributes) plus a **"show me now" refresh button** — no hand-written HA YAML required.
- Run as a **persistent container** that owns its own freshness: it computes and publishes on startup, recomputes on a configurable interval, and recomputes immediately on demand when the refresh button publishes to a **"show me now" MQTT command topic** the container subscribes to. Home Assistant is never load-bearing for freshness or correctness — if HA restarts, the verdict stays current.
- Keep notification *timing* in Home Assistant: a user-authored automation watches the verdict entity and sends a push notification when the verdict is not NO-GO, at whatever time the user chooses. The core owns *what* the verdict is and *when it is recomputed*, not *when the user is told*.
- Establish **minimal configuration**: one pier (id, latitude, longitude, elevation), MQTT broker connection details, and a recompute interval. Multi-pier, horizon masks, weather providers, target catalog, and the LLM explainer are explicitly out of scope for this change.
- Establish the **deterministic test harness**: the same inputs (including a pinned evaluation instant) yield the same verdict document, verified off Home Assistant.

Non-goals for this change: real sky/light math, weather/conditions data, horizon masking, target ranking, the optional LLM layer, HAOS add-on packaging, and choosing which host box the container runs on. The core stays host-agnostic; it publishes to the existing broker either way.

## Capabilities

### New Capabilities
- `night-verdict`: Produces a deterministic per-pier night verdict document (verdict, banded score, confidence, reasons, targets, night window, metadata) from configuration, with a stable contract that later milestones fill with real astronomy, conditions, and ranking. This change establishes the contract and deterministic emission with stubbed decision values.
- `ha-delivery`: Publishes a verdict document to Home Assistant via MQTT discovery, auto-creating per-pier entities plus a refresh control, keeping them current from a persistent process (startup + interval + on-demand), so the verdict can be placed on a dashboard and used as an automation trigger for push notifications.

### Modified Capabilities
<!-- None. This is the first change; no existing capabilities. -->

## Impact

- **New code**: a Python 3.12+ package containing the deterministic core (verdict document model + stubbed producer), an MQTT discovery publisher and command subscriber, a long-running service loop (startup + interval + on-demand recompute), and configuration loading.
- **New dependencies**: an MQTT client library (e.g. paho-mqtt) and a config/validation library; no astronomy or weather dependencies yet.
- **External systems**: publishes to and subscribes on the existing Mosquitto/MQTT broker on the user's HAOS install; creates entities via MQTT discovery. Requires broker credentials in configuration.
- **Home Assistant**: new auto-discovered entities per pier (verdict sensor, score sensor, refresh button); a user-authored automation consumes the verdict sensor to trigger notifications (documented, not shipped as a blueprint in this change).
- **Contract surface**: the verdict document JSON and the MQTT entity mapping become the stable interface that milestones M2–M6 build against.
- **Dev tooling**: repository scaffolding using uv (env/deps), just (task runner), ruff (lint + format), mypy (types), pytest, pre-commit, and a GitHub Actions CI workflow running `just check`; plus a uv-based `Dockerfile` for the persistent container.
