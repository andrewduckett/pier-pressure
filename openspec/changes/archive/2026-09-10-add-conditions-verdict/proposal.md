## Why

The verdict is still a stub. Astronomy is real (M2 fills `dark_window` and
`moon`), but `verdict`, `score`, `confidence`, and `reasons` are hard-coded
placeholders — every night returns "MAYBE, 50". PierPressure cannot yet answer
its one question: is tonight worth setting up for? This change turns those stubs
into a real go/no-go by adding observing conditions (cloud, wind, seeing,
transparency) and computing the gates, the banded score, and the confidence the
contract has always reserved space for.

## What Changes

- **A conditions provider layer, outside the pure core.** Weather and seeing
  come from external forecasts (Open-Meteo for cloud and wind; 7Timer! for
  seeing and transparency). All network access, caching, and fallback live in
  this layer. It produces a plain, immutable **conditions snapshot** — an hourly
  series covering the dark window, with each field stamped for availability and
  freshness.
- **The core stays pure and gains an input.** `produce_verdict(pier, clock,
  conditions)` takes the snapshot as an argument. The core does no I/O; it
  remains a deterministic function of its inputs, so the same snapshot yields a
  byte-identical document. This keeps the offline-astronomy and
  no-load-bearing-source rules intact: the network lives only at the provider
  edge.
- **Real hard gates (any fail → NO-GO, null score):**
  - no astronomical night (`dark_window` is null);
  - overcast all night (every hour of the dark window is at or above a fixed
    cloud threshold — the true "no usable sky" dealbreaker);
  - wind gust over a configured limit (**opt-in, off by default**).
- **Real banded score (0–100 when gates pass)** from cloud (dominant), the moon
  (illumination weighted by how much of the dark window it is up, finally
  consuming M2's moon fields), transparency, and seeing. `reasons[]` itemize
  these terms, so the explanation falls out of the math.
- **Real confidence from forecast lead-time and data completeness.** Confidence
  rises as dusk nears and falls when optional data (seeing, transparency) is
  missing. Missing optional data lowers confidence and drops its score term; it
  never fails a gate or zeroes the score.
- **Two knobs, per pier.** `go_threshold` (the single tuning dial — the score at
  or above which a passing night is GO rather than MAYBE; sensible default) and
  the opt-in `max_gust` (the wind gate's limit). Every other threshold and
  weight is fixed in code, so the system decides rather than presenting sliders.
- **Recompute cadence becomes meaningful:** aligned to forecast refresh and
  denser as dusk approaches. (Cadence detail is settled in design.)

The verdict document is **not reshaped**: this change fills existing stubbed
fields. Whether to surface a conditions summary as new additive fields (for new
Home Assistant entities) is a design decision, taken additively if at all.

## Capabilities

### New Capabilities
- `conditions`: The observing-conditions provider layer. Fetches cloud and wind
  (Open-Meteo) and seeing and transparency (7Timer!) from external forecasts,
  behind one interface with caching and graceful fallback. Emits an immutable,
  availability-stamped conditions snapshot covering the dark window. No single
  provider is load-bearing; the layer degrades to a partial snapshot rather than
  failing.

### Modified Capabilities
- `night-verdict`: The verdict's decision fields become real. The stubbed
  `verdict`, `score`, `confidence`, and `reasons` are replaced by hard gates, a
  banded score, and lead-time confidence computed from the pier, the clock, and
  the conditions snapshot. NO-GO remains gate-only with a null score; a passing
  night is GO or MAYBE split at `go_threshold`.

## Impact

- **New code:** a `conditions` provider package outside `pierpressure/core/`
  (fetch, cache, fallback, snapshot); the snapshot type; gate and score logic
  inside the core.
- **Changed signature:** `produce_verdict` gains a `conditions` argument; the
  service fetches the snapshot before calling it and passes it in.
- **Config:** `PierConfig` gains `go_threshold` (with a global default) and an
  optional `max_gust`.
- **Dependencies:** an HTTP client (added via `uv`), scoped to the provider
  layer; the core adds none.
- **Tests:** provider tests use recorded forecast fixtures; core determinism
  tests pin a fixture snapshot so output stays byte-identical while live
  forecasts drift. The core boundary and offline-guard tests must still pass —
  the core gains no network or Home Assistant imports.
- **Delivery:** the MQTT contract (topics, entities, entity mapping) is
  unchanged. Any new entities would follow only from additive document fields,
  decided in design.
- **Out of scope:** target ranking and the `targets` list (M5); the LLM prose
  layer (M6); horizon masks and multiple sites (M4).
