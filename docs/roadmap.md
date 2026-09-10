# PierPressure Roadmap

This is the living roadmap. It lists the milestones and their status, and records
the cross-cutting rules that hold across all of them. Each milestone becomes an
OpenSpec change (under `openspec/changes/`) **when we start it** — not all at once,
so specs never drift ahead of the work. Pull a milestone's scope from here when
you open its change.

## Cross-cutting rules (hold across every milestone)

These are the durable constraints. The genuinely hard-to-reverse ones become ADRs
(`docs/adr/`) during a change's `adr` step; all of them live in
`openspec/config.yaml` `context` so every generated artifact respects them.

- **Pure core.** The decision core is Python 3.12+ with zero Home Assistant
  imports. It is deterministic and testable off Home Assistant: the same inputs
  (including a pinned evaluation instant) yield the same verdict document.
- **One contract.** The core emits a single JSON verdict document. That document
  plus the MQTT entity mapping are the stable contract every milestone builds
  against. Frozen: the delivery surface (topics, entities, entity mapping) and the
  meaning of existing fields — never reshaped. Additive growth (new fields/objects)
  as a milestone's science arrives is allowed and expected; reserve a field early
  (stubbed) when its shape is already known, rather than inventing one before the
  milestone that defines it.
- **MQTT-discovery delivery.** Entities reach Home Assistant via MQTT discovery
  (auto-created, no hand YAML). REST is an acceptable fallback adapter.
- **HA is never load-bearing.** The core runs as a persistent container that owns
  its own freshness (recompute on startup, on interval, and on demand via a
  "show me now" MQTT command). If Home Assistant restarts, the verdict stays
  current. Notification *timing* lives in a Home Assistant automation.
- **Gates then banded score.** Verdict = hard GATES (any fail → NO-GO with a
  reason, null score) then a 0–100 SCORE only when gates pass. `reasons[]` are the
  itemized scoring/gate terms — explainability falls out of the math.
- **Astronomical-night hard clamp.** Target observability windows are always
  clamped to astronomical night (sun below −18°), regardless of any user-requested
  view window. This is a rule, not a preference.
- **Confidence reflects lead-time.** `confidence {band: LOW|MEDIUM|HIGH,
  value: 0–100}` expresses how much to trust the verdict given forecast
  lead-time/freshness; it rises as dusk nears.
- **No load-bearing data source.** Weather/conditions providers sit behind an
  interface with caching and graceful fallback; no single provider is required.
- **LLM never feeds the math.** Astronomy/ephemeris truth never comes from the
  LLM. The optional LLM layer only explains an already-computed verdict, and the
  system degrades gracefully without it.
- **Astronomy stack.** Skyfield / Astroplan / Astropy.
- **Toolchain.** uv (env/deps/lockfile), just (task runner), ruff (lint and
  format — no black), mypy (types), pytest, pre-commit, GitHub Actions CI
  running `just check`. Python 3.12.

## Milestones

### M1 — Walking skeleton  ·  status: in progress
Change: `add-walking-skeleton`

Thinnest end-to-end pipe with a **stubbed** verdict, to freeze the contract and
retire the integration risk before any science is written.
- Pure core emits the full verdict document (verdict/score/confidence/reasons/
  targets/dark_window + metadata) with stubbed decision values.
- MQTT-discovery delivery: per-pier verdict sensor, score sensor, refresh button.
- Persistent container: publish on startup + interval + on-demand "show me now".
- Minimal config: one pier + broker + recompute interval. Deterministic tests.

### M2 — Sky & light core  ·  status: in progress
Change: `add-sky-light-core`

Real ephemeris math behind the frozen contract.
- Astronomical twilight windows → fills `dark_window` (instant-relative night
  selection; polar continuous-night/no-night handled distinctly); enforces the
  astro-night clamp. Moon phase / illumination + above-horizon behaviour across
  the dark window (new `moon` object). Deterministic and fully offline (Skyfield,
  pinned ephemeris). Still no weather. (Target alt/az sampling moved to M5, where
  it has a consumer.)

### M3 — Conditions → real go/no-go  ·  status: done
Change: `add-conditions-verdict` (archived)

Turn stubs into a real verdict.
- Provider interface (lean: Open-Meteo base + 7Timer! for seeing/transparency)
  with caching + fallback. Real hard gates (no dark window; overcast across the
  dark window; optional wind-gust limit) and the banded score. Real `confidence`
  from forecast lead-time. Periodic recompute cadence becomes meaningful
  (aligned to forecast refresh, denser near dusk).

### M4 — Pier sites + horizon mask  ·  status: planned
Multiple sites, each with a horizon mask.
- Manage multiple piers. Canonical internal horizon representation (sampled
  `(az, alt)`), with importers for Stellarium / NINA `.hrz` / Telescopius. A
  target counts only if it clears the mask in its direction.

### M5 — Target catalog + ranking  ·  status: planned
Fill the `targets` list.
- Catalog source (Messier / OpenNGC). Target alt/az sampled over the night grid
  (time-sampled dusk→dawn; deferred here from M2 so it is built with its ranking
  consumer). Rank on visibility window, altitude above the horizon mask, moon
  separation, transit time, and equipment FOV-fit. Clamped to astronomical night
  per the cross-cutting rule.

### M6 — LLM explainer + suggestions  ·  status: planned
Optional prose layer.
- Consumes the finished verdict document and rewrites `reasons[]` into prose;
  never touches the numbers. System fully functional without it.

## Deferred / out of scope (for now)
- Controlling the mount or running the imaging session (this recommends, it does
  not operate).
- Cloud hosting, multi-user, accounts.
- Live all-sky camera cloud detection (may inform a future conditions source).
- HAOS add-on packaging and the choice of which host box the container runs on
  (the core is host-agnostic; revisit once M1–M3 are stable).
