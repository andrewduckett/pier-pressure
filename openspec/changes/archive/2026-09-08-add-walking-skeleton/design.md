## Context

See proposal.md - Why. This change is a walking skeleton: it must prove the full pipe (config → deterministic verdict document → MQTT-discovery entities in Home Assistant → refresh on demand) with stubbed decision values, and freeze the verdict-document and MQTT contract so M2–M6 replace stubs without reshaping either surface. The durable constraints in `openspec/config.yaml` context apply — especially the pure/deterministic core, HA never load-bearing, and the persistent container owning its own freshness.

## Goals / Non-Goals

**Goals:**
- A pure `core` package with no delivery or HA imports, so the verdict document is producible and testable in isolation.
- A concrete, frozen JSON verdict document and a concrete MQTT discovery/state/command topic scheme.
- A persistent process that publishes on startup, on a configurable interval, and on an on-demand "show me now" command, with entities that survive an HA restart and go unavailable if the process dies.
- A `Dockerfile` so the process runs as a persistent container.

**Non-Goals (design-level, on top of the proposal's):**
- No astronomy, weather, horizon, ranking, or LLM logic — the producer is a deterministic stub.
- No HAOS add-on manifest / Supervisor packaging (a plain container only).
- No async runtime; a simple threaded model is sufficient at this size.

## Decisions

### D1 — Package layout enforces the pure-core boundary
```
pierpressure/
  core/
    model.py      # verdict-document types + JSON (de)serialization
    clock.py      # Clock protocol; SystemClock, FixedClock
    config.py     # load + validate config (piers, mqtt, recompute)
    producer.py   # produce_verdict(pier, clock) -> Verdict   (STUB in M1)
  delivery/
    mqtt.py       # discovery publisher + state publisher + command subscriber
  service.py      # persistent loop wiring the two together
  __main__.py     # entrypoint: python -m pierpressure
tests/            # core tests need no broker; delivery tests use a fake client
```
`core` MUST NOT import from `delivery`. Rationale: the "testable off HA / delivery-independent" spec requirements become structurally true, not just conventions. Alternative (single module) rejected — it invites the coupling the specs forbid.

### D2 — Verdict document types via Pydantic v2
Model the document and the config with Pydantic v2. It gives declarative range validation (latitude/longitude bounds, `score` 0–100, `confidence.value` 0–100, `verdict`/`band` enums), stable JSON (de)serialization, and config validation in one dependency. Alternative (stdlib dataclasses + jsonschema) rejected as more hand-rolled for the same result.

Frozen document shape (M1 stub values shown):
```json
{
  "pier": "backyard",
  "generated_at": "2026-09-07T21:30:00Z",
  "verdict": "MAYBE",
  "score": 50,
  "confidence": { "band": "LOW", "value": 0 },
  "reasons": ["Walking skeleton: real verdict logic not yet implemented"],
  "targets": [],
  "dark_window": { "start": null, "end": null }
}
```
Serialization rules for determinism: UTC ISO-8601 `Z` timestamps, keys emitted in a fixed order, no locale-dependent formatting. `generated_at` is the only time-varying field and comes solely from the injected clock (D3). Every contract key is **always present** — a field with no value is emitted as JSON `null`, never omitted. In particular `score` is `null` on a gated NO-GO, never absent, so downstream consumers such as the score `availability_template` (D6) can rely on the key existing. A serialization test asserts `score` is present-and-`null` on a gated NO-GO.

### D3 — Injectable clock
A `Clock` protocol with `now() -> datetime` (tz-aware UTC). `producer.produce_verdict(pier, clock)` reads time only from it. `SystemClock` in production (`datetime.now(timezone.utc)`); `FixedClock(instant)` in tests. Timezone strictness is enforced end to end: the Pydantic model rejects naive datetimes and normalizes to UTC, and serialization emits ISO-8601 with a `Z` suffix, so a naive local time can never silently break the determinism rule. Rationale: satisfies the determinism spec (same inputs + pinned instant → byte-identical document) and makes golden-file tests trivial.

### D4 — Stub producer (M1 only)
`produce_verdict` returns a deterministic, honest-but-coarse document: `verdict=MAYBE`, `score=50`, `confidence={LOW,0}`, one reason naming it a skeleton, `targets=[]`, `dark_window={null,null}`. It performs config validation (rejecting bad piers) so the validation requirement is real now. M2/M3 replace the body behind this signature.

### D5 — MQTT topic scheme (per pier)
Discovery prefix default `homeassistant`; app base topic default `pierpressure`; both configurable.

| Purpose | Topic | Retain |
|---|---|---|
| Verdict discovery cfg | `homeassistant/sensor/pierpressure_<pier>/verdict/config` | yes |
| Score discovery cfg | `homeassistant/sensor/pierpressure_<pier>/score/config` | yes |
| Refresh discovery cfg | `homeassistant/button/pierpressure_<pier>/refresh/config` | yes |
| Verdict state | `pierpressure/<pier>/verdict/state` | yes |
| Document attributes (JSON) | `pierpressure/<pier>/verdict/attributes` | yes |
| Refresh command | `pierpressure/<pier>/refresh/command` | no |
| Availability (LWT) | `pierpressure/status` | yes |

Discovery config, state, and availability are all **retained** so a Home Assistant restart re-reads the last verdict, re-creates the entities, and sees current availability without waiting for a recompute (satisfies the retained-state spec scenario). Availability is driven by an MQTT Last-Will-and-Testament: on startup the process publishes a **retained** `online` to `pierpressure/status`, and the LWT is registered as a **retained** `offline`. Retaining availability is correct precisely *because* of the LWT — on any unexpected disconnect the broker overwrites the retained value with `offline`, so a late-subscribing HA always reads the container's true current availability rather than a stale `online`.

Representative verdict-sensor discovery payload:
```json
{
  "name": "Verdict",
  "unique_id": "pierpressure_backyard_verdict",
  "state_topic": "pierpressure/backyard/verdict/state",
  "json_attributes_topic": "pierpressure/backyard/verdict/attributes",
  "availability_topic": "pierpressure/status",
  "payload_available": "online",
  "payload_not_available": "offline",
  "icon": "mdi:telescope",
  "device": {
    "identifiers": ["pierpressure_backyard"],
    "name": "PierPressure backyard",
    "manufacturer": "PierPressure",
    "model": "night-verdict"
  }
}
```
All three entities share the same `device` block so they group under one Home Assistant device per pier. `unique_id`/topics derive from the pier id → stable identity, no duplicates on re-publish (satisfies the auto-discovery spec).

### D6 — Null score surfaces as unavailable via an availability template
The score sensor's *state* reads the number from the attributes JSON topic with `value_template: "{{ value_json.score }}"`. Its *availability* is driven by a two-entry `availability` list with `availability_mode: all`: (1) the shared LWT topic `pierpressure/status`, and (2) an `availability_template` over the attributes JSON — `"{{ 'online' if value_json.score is not none else 'offline' }}"`. So the score entity is available only when the container is online AND the score is non-null; a gated NO-GO (null score) makes it `unavailable` rather than showing `0` (satisfies the null-score spec scenario). Relying on the value_template alone to yield `unavailable` is not robust in Home Assistant, which is why availability is used instead. The template checks `value_json.score is not none`, which is safe precisely because `score` is always present as `null` (never omitted) per D2 — an omitted key would raise an `UndefinedError`.

### D7 — Threaded loop: paho network thread + main-thread work queue
Use `paho-mqtt`. `loop_start()` runs the network/callback thread; it subscribes to each pier's refresh command topic. The command callback does **not** publish directly — it parses the pier id from the command topic and puts it on a thread-safe `queue.Queue`. The main thread tracks an **absolute deadline** for the next periodic refresh (`deadline = time.monotonic() + interval_seconds`) and each iteration waits only the remaining time: `queue.get(timeout=max(0.0, deadline - time.monotonic()))`. A dequeued pier id is an on-demand refresh, so it recomputes and publishes **that pier** *without moving the deadline*. When `queue.Empty` is raised (or the deadline is otherwise reached) it recomputes and publishes **all** piers and sets a new deadline. Using an absolute deadline rather than a fresh `interval_seconds` timeout per call is essential: otherwise frequent on-demand refreshes would repeatedly reset the wait and starve the periodic all-pier recompute indefinitely. On startup it publishes all piers once and sets the first deadline. A refresh that arrives while a recompute is running is simply the next item on the queue and is processed on the following iteration rather than dropped. Rationale: the queue carries the pier identity that a bare `threading.Event` cannot, preserving per-pier isolation (D8); a single thread publishes (no concurrent writes); interval + on-demand collapse into one mechanism (satisfies the periodic and on-demand spec requirements). Alternative (`aiomqtt`/asyncio) rejected — unnecessary async surface for M1. Alternative (`threading.Event`) rejected — it carries no payload, so a per-pier refresh could not tell the loop which pier to recompute.

### D8 — Config is YAML, piers is a list, secrets overridable by env
```yaml
mqtt:
  host: 192.168.1.10
  port: 1883
  username: pierpressure
  password: ${PIERPRESSURE_MQTT_PASSWORD}   # env override; avoids plaintext
  discovery_prefix: homeassistant
  base_topic: pierpressure
recompute:
  interval_seconds: 900
piers:
  - id: backyard
    latitude: 51.50
    longitude: -0.12
    elevation_m: 30
```
`piers` is a list even though M1 is validated with one, because the delivery already operates per pier and a list costs nothing — it avoids a config-shape change at M4. M1 adds no cross-pier or horizon logic; each pier independently gets the single-pier treatment. Broker password is read from an env var so it need not sit in plaintext.

Per-pier validation is isolated so one bad entry cannot take down the rest: each pier in the list is validated independently at startup; an invalid pier is reported (logged at error) and skipped, while valid piers continue to produce and publish. The process exits non-zero only if **no** valid pier remains, so a single typo in one site never silently disables a working one — and never yields a silently wrong verdict for the bad one.

### D9 — Delivery failures are raised, not swallowed
Broker connect/publish failures raise and are logged at error; the process exits non-zero on an unrecoverable startup failure (e.g. broker unreachable at boot) rather than idling as if healthy. Producer errors (bad config) are distinct from delivery errors, preserving the core/delivery separation.

### D10 — Toolchain & developer workflow
- **uv** manages the environment, dependencies, and lockfile: `pyproject.toml` (`[project]` deps), `uv.lock`, `.python-version` pinned to 3.12. Commands run via `uv run`.
- **just** provides the task runner (`Justfile`), thin wrappers over uv:
  `install` (`uv sync`), `lint` (`uv run ruff check .`), `format` (`uv run ruff format .`), `typecheck` (`uv run mypy pierpressure`), `test` (`uv run pytest`), `run` (`uv run python -m pierpressure`), and `check` (lint + typecheck + test).
- **ruff** does both linting and formatting (`ruff check` + `ruff format`); black is not used, avoiding two formatters that can conflict. Configured under `[tool.ruff]` in `pyproject.toml`.
- **mypy** type-checks the `pierpressure` package (`[tool.mypy]` in `pyproject.toml`); the core is small and fully typed.
- **pytest** runs the deterministic core tests (no broker) and delivery tests against a fake MQTT client.
- **pre-commit** (`.pre-commit-config.yaml`) runs ruff check/format and mypy on commit so checks run before code lands.
- **GitHub Actions** (`.github/workflows/ci.yml`) runs `just check` on push/PR. The repository is not yet git-initialized, so the workflow sits ready and activates once the repo is pushed to GitHub.
- The **Dockerfile** builds via uv (install into a virtual env, then a slim runtime layer), consistent with local tooling. This is a plain container, not a HAOS add-on (see Non-Goals).

Rationale: uv + just + ruff is the current, fast, low-friction Python toolchain and keeps one command surface (`just`) for humans and CI alike. Alternatives (pip/poetry, make, black+flake8+isort) rejected as slower and more moving parts for the same result.

### D11 — Verification strategy: assert our output automatically, confirm HA behavior manually
A fake MQTT client can prove *what PierPressure publishes*, but cannot prove *how Home Assistant reacts*. So verification is split honestly:
- **Automated (pytest, no broker):** the delivery layer publishes to a fake/in-memory MQTT client; tests assert the exact topics, retain flags, and payloads, and validate each discovery payload against Home Assistant's MQTT-discovery JSON schema for that entity type (sensor, button). This catches malformed discovery configs — a subtle schema error fails the suite rather than only failing silently in production.
- **Manual acceptance (documented checklist):** a short M1 acceptance checklist (in the README) run once against the real HAOS + broker confirms the true end-to-end claims that no unit test can: the three entities appear under one device, the verdict/score/confidence render, the refresh button triggers a republish, a gated NO-GO shows the score as unavailable, and killing the container flips entities to unavailable.
- **Optional integration test (opt-in):** a `pytest` marker that runs against a local broker (e.g. an ephemeral Mosquitto) exercises real publish/subscribe and LWT behavior; not required for CI to pass on machines without a broker.

Rationale: the spec's HA-facing scenarios are honestly verifiable — the mechanically-assertable parts (payload/topic/retain/schema) are automated, and the parts that genuinely require Home Assistant are a named, repeatable manual check rather than an untested assertion.

## Risks / Trade-offs

- **Forgetting `retain` on discovery/state** → entities vanish on HA restart. → Mitigate: retain is specified in D5 and covered by the retained-state test scenario.
- **Retaining availability** would leave a stale `online` after a crash. → Mitigate: availability is LWT-driven and not retained (D5).
- **`value_template` null handling varies by HA version.** → Mitigate: verify against the target HA; the technique (D6) is documented so it is easy to adjust.
- **Thread interplay (callback vs main loop).** → Mitigate: all publishing is funnelled to the main thread via the Event (D7); the callback only signals.
- **Plaintext broker credentials.** → Mitigate: env-var override (D8); documented as the recommended path.
- **Unauthenticated refresh command topic.** The `refresh/command` topic is a control surface — anyone with broker access can trigger a recompute. → Mitigate: benign in M1 (a recompute is idempotent and cheap) and bounded by the broker's own ACLs/auth; documented as a trust boundary so later milestones that add heavier on-demand work reconsider it.
- **Determinism drift from serialization.** → Mitigate: fixed key order + UTC ISO-8601 + injected clock (D2/D3), asserted by a golden-document test.

## Migration Plan

Greenfield; nothing to migrate. Deploy = run the container pointed at the existing broker. To fully remove PierPressure entities from HA, publish empty retained payloads to the three discovery config topics (documented in the README). No rollback concerns beyond stopping the container.

## Open Questions

- Default `recompute.interval_seconds` (proposed 900). Safe to pick now; M3 will likely make cadence adaptive (denser near dusk), which changes the value, not the contract.
- Whether the score sensor should carry a `device_class`/`unit_of_measurement`. Cosmetic; deferable without affecting the contract.
