## Context

See proposal.md — Why. M2 made the astronomy real (`dark_window`, `moon`) but
the decision fields (`verdict`, `score`, `confidence`, `reasons`) are still
stubs. This design covers how M3 fills them from external observing conditions
without breaking the two rules that shaped M2: the core is a deterministic,
offline-testable pure function, and no single external source is load-bearing.

The tension this design resolves: astronomy is genuinely offline, but weather is
irreducibly external — a forecast cannot be computed from first principles. The
resolution is a seam, not a relaxation of the rules.

## Goals / Non-Goals

**Goals:**
- Keep `produce_verdict` a pure, deterministic function after conditions arrive.
- Confine all network access, caching, and fallback to a provider layer outside
  `pierpressure/core/`.
- Turn the frozen contract's stubbed fields into real gates, a banded score, and
  lead-time confidence, with `reasons[]` falling out of the math.
- Degrade honestly when data is missing, never crash and never publish a false GO.

**Non-Goals (design-level boundaries):**
- No new document fields unless a later decision needs one; M3 fills existing
  fields (Decision 7).
- No target ranking (M5), horizon masks (M4), or LLM prose (M6).
- No forecast-uncertainty modelling beyond lead-time, freshness, and completeness.
- No contiguity or peak-quality modelling of the night (Decision 3, accepted limit).

## Decisions

### D1 — The seam: a plain conditions snapshot passed into a pure core

`produce_verdict(pier, clock, conditions)` takes an immutable **conditions
snapshot** as an argument. The provider layer builds the snapshot (network,
cache, fallback); the core only reads it. So the core stays a pure function of
its inputs and remains byte-identical for a pinned snapshot, and the existing
boundary and offline-guard tests keep passing — the core gains no network import.

**Why a plain data snapshot, not a provider interface injected into the core:**
a data value cannot fetch anything, so I/O cannot creep back across the seam and
determinism stays a hard wall rather than "deterministic if you mock correctly."
Graceful fallback and "no load-bearing source" then become *pure logic over the
snapshot's availability flags* (Decision 6), not exception handling inside the
core.

- *Alternative — inject a provider interface into the core:* still nominally
  pure, but invites lazy fetches, retries, and timeouts to blur the seam, and
  forces determinism tests to mock an interface. Rejected.
- *Alternative — the core owns fetching behind an offline cache:* reintroduces
  the IERS/ephemeris auto-download problem ADR0004 spent effort removing, and
  breaks the boundary test. Rejected.

### D2 — Snapshot shape: one availability-stamped hourly grid over the dark window

The snapshot is an hourly series covering `dark_window.start .. end`. Each hour
carries cloud cover, wind gust, seeing, and transparency, and **each field is
stamped present-or-absent**. The snapshot also carries a per-provider **issue
time** so the core can compute freshness (Decision 5) without reading wall-clock.

The provider layer resamples 7Timer!'s coarser (3-hourly) data onto the hourly
grid, so the core sees one uniform grid and never knows a provider or a
resolution existed. When there is no dark window, no snapshot is needed — the
astronomy gate (Decision 4) short-circuits before conditions matter.

**The window is always bounded.** M2 already anchors even a *continuous* polar
night to the observer's local solar day (`sky.py` `_local_solar_day`, noon→noon),
so `dark_window` never exceeds ~24 hours and is always within a weather
forecast's reach. No session clamp is needed here: conditions are fetched and
aggregated over the actual `dark_window`, which is at most a day long even in
high-latitude winter.

### D3 — Aggregation: a per-hour clarity weight drives gate and score

Each hour gets a **clarity weight `q ∈ [0,1]`** from its cloud cover via a fixed
monotonic curve (clear → 1, overcast → 0), and a **coverage weight `w ∈ [0,1]`**
equal to the fraction of that hour that lies inside the dark window (a boundary
hour that is only partly dark contributes `w < 1`; fully-inside hours have
`w = 1`). Every sum in this decision runs over the dark window (at most ~24h,
D2). Coverage weighting keeps every quantity normalized when the window
does not fall on whole-hour boundaries — a 2.5-hour window can never let three
hourly slots push a fraction above 1. One concept then drives everything. Let
`C` be the set of hours whose **cloud** data is available, and
`W = Σ_{h∈C}(w·q)` the effective clear-hours total over those hours:

- overcast **gate** = `W ≈ 0` (no hour with cloud data is even partially usable);
- cloud **score term** = `W / Σ_{all h}(w)` ∈ [0,1] — the numerator sums only
  hours with cloud data, but the denominator is the **whole** window. Hours whose
  cloud is missing therefore contribute no usable time: they count as
  *not-known-usable*, never as clear (which would inflate the score) and never as
  overcast (which would risk a false NO-GO gate). Partial cloud coverage thus
  depresses the score honestly, confidence falls with it (D5), and a `GO` stays
  possible only when the covered portion is both substantial and clear.
- an **optional** hourly term `x` (seeing, transparency) = its clarity-weighted
  mean over the hours where *that term* is available:
  `Σ_{h∈C∩A(x)}(w·q·x) / Σ_{h∈C∩A(x)}(w·q)`, where `A(x)` is the set of hours
  carrying that term. Restricting the denominator to the term's own available
  hours keeps a partial-coverage gap from artificially depressing its mean.
- the **moon** term is not hourly snapshot data; it is derived from M2's
  `moon.rise`/`set`. Each hour gets a boolean `up_h` (is the moon above the
  horizon during that hour), and the moon's contribution is
  `illumination × Σ_{h∈C}(w·q·up_h) / W` — the clarity-weighted fraction of
  usable darkness the moon is up, scaled by its brightness. The discrete rise/set
  instants thus map onto the hourly grid as a per-hour above-horizon flag before
  entering the same clarity-weighted machinery.

Every clarity-weighted mean is defined only when its denominator is > 0. When
gates pass with cloud present, `W > 0` is guaranteed (the overcast gate would
have fired otherwise); an optional term with no available hour simply drops out
(its contribution is omitted and confidence's `K` reflects the gap, D5). The one
case where clarity is entirely undefined — cloud absent for the whole window —
never reaches this aggregation: it is short-circuited earlier (D6).

**Why not the mean cloud cover:** the mean rates "clear 4h then overcast 4h"
identical to "uniformly 50% hazy all night," yet the first is four usable hours
and the second is none. Integrated usable dark time is the metric observers
actually reason about.

*Accepted limitation:* at equal `W`, this ignores contiguity and peak quality.
Deferred; addable additively later. Hour-resolution forecasts do not support
contiguity claims reliably anyway.

### D4 — Verdict: gate-only NO-GO, one score threshold splits GO from MAYBE

Hard gates (any fail → NO-GO with a reason and null score):
1. no astronomical night (`dark_window` is null);
2. overcast all night — cloud data is available **and** `W ≈ 0` (the effective
   clear-hours total from D3). Requiring cloud to be present keeps an empty cloud
   set (`W = 0` for lack of data) from firing this gate; that case is the
   missing-cloud MAYBE (D6), not a NO-GO;
3. wind gust over `max_gust` for **any** hour of the dark window (opt-in; safety
   is window-wide, so it is not clarity-weighted; when `max_gust` is set but wind
   data is missing, the verdict is capped at MAYBE per D6). *Scope, deliberate:*
   the gate
   covers the dark window only, not the twilight setup/teardown period. Extending
   it to a wider session window is intentionally out of scope for M3 — the gate
   is off by default, and a session-window concept would add sun-event
   computation and cut against the astronomical-night clamp for marginal benefit.

When gates pass, the score (0–100) is computed and the verdict is **GO** if
`score ≥ go_threshold` **and cloud data is present**, else **MAYBE**. The
explicit "cloud present" condition — not just a low score — is what makes the
cloud-missing case (D6) a MAYBE regardless of `go_threshold`; without it a
`go_threshold` of 0 could produce a GO from no cloud evidence. NO-GO is *only*
ever a failed gate, so the invariant **NO-GO ⟺ null score** holds and the
delivery layer can rely on it.

**Why the moon is not a gate:** a bright moon never makes a night impossible,
only worse for faint targets — a fine lunar/planetary night. Gating it would
override a judgment that is the user's to make. It is a score penalty instead.

### D5 — Confidence: `max(floor, 100 × L × F) × K`

Confidence measures trust in the verdict, orthogonal to how good the night is.

- `L` **lead-time**: rises as dusk nears; saturates at 1 within a few hours of
  `dark_window.start` or once mid-session; decays toward a floor as dusk is many
  hours out (bounded, since M2 always selects the next night).
- `F` **freshness**: 1 when just issued; decays with the snapshot's age past the
  provider's refresh cadence; drops hard when stale cache is served in an outage.
- `K` **completeness**: 1 when all fields fully cover the window. Each optional
  field (seeing, transparency) is trimmed **proportionally** to the fraction of
  the dark window it is missing — a one-hour gap trims a little, a fully-absent
  field trims its whole share — so partial coverage costs partial confidence
  rather than all-or-nothing. When `max_gust` is configured, missing wind data
  also trims `K` (D6). `K` collapses toward 0 as cloud coverage of the window goes
  to 0 (and is exactly 0 when cloud is entirely absent, D6).

**When there is no dark window** (astronomy-only NO-GO), no forecast is involved:
`L`/`F`/`K` do not apply, and confidence is **HIGH with value 100** —
deterministic offline astronomy carries no forecast uncertainty, so "there is no
astronomical night" is a certainty, not a guess. This satisfies the
"confidence always present" contract on the no-conditions path.

**Why multiply, then floor:** trust is limited by the weakest link — a fresh,
complete forecast 15h out should not read HIGH, and neither should a stale,
incomplete one an hour before dusk. Multiplication enforces that; an average
would let a strong factor wrongly compensate for a weak one. The floor stops
pure multiplication from reading LOW when nothing is actually wrong. Band
thresholds ~40 / ~70.

The floor is a fixed constant applied to the `L·F` sub-product **only** — it
lifts an unfairly-low value when lead-time and freshness are merely middling.
Completeness `K` multiplies in *after* the floor, so it deliberately escapes the
lift: a heavily incomplete forecast (small `K`) still pulls the final confidence
down in proportion to how much data is missing, and the floor cannot rescue it.
When cloud data is entirely absent, `K` is 0 and `confidence.value` is
**exactly 0** (the cloud-missing path, D6), so the "conditions unavailable"
verdict always reads zero-confidence — mechanically assertable, not "near zero."

### D6 — Degradation ladder: honest, never false

Missing data is handled as pure logic over the snapshot's availability flags, in
a **fixed precedence** so the cases never contradict:

1. **No dark window** (astronomy) → NO-GO. Needs no conditions; confidence is
   HIGH/100 (offline astronomy is certain — there is no forecast to distrust,
   D5).
2. **Wind gate** — only when `max_gust` is configured. If wind data is present
   and a gust exceeds `max_gust` at any hour of the dark window → NO-GO. This is
   a safety dealbreaker evaluated before any cloud logic, so a missing cloud
   observation can never override it. If `max_gust` is configured but wind data
   is **missing**, the gate cannot be checked: the verdict is **capped at MAYBE —
   never GO** (a configured safety limit must not be silently ignored), with a
   reason that wind data is unavailable, and `K` is trimmed for the missing wind.
   When `max_gust` is not configured, missing wind data is irrelevant.
3. **Cloud entirely missing** (no cloud data anywhere in the window) → the
   verdict **is MAYBE — never GO** (no evidence the sky is clear), never NO-GO
   (absence of data is not a dealbreaker, and a null score would falsely imply a
   gate failed). The clarity aggregation (D3) is **skipped entirely** — there is
   no clarity to weight by — so the **score is 0** and **confidence is exactly 0**
   (band LOW), with a "conditions unavailable — astronomy only" reason. MAYBE is
   asserted outright here, not derived from `score ≥ go_threshold`, so no
   score/verdict contradiction can arise.
4. **Cloud present** → the overcast gate can fire (`W ≈ 0` **and** cloud data is
   available → NO-GO); otherwise the score is computed. The overcast gate is
   reachable only in this branch, so an empty cloud set (`W = 0` for lack of data)
   never masquerades as "overcast" — case 3 has already handled it.

Within the cloud-present branch, the provider-outage rungs:

- **7Timer! down** → seeing/transparency drop from the score, `K` trims
  confidence; gates and the cloud score stay fully intact.
- **Open-Meteo down, cache usable** → serve the last-good snapshot; `F` decays
  with its age. "Usable" is judged per source (a cache carrying fresh base
  cloud/wind is usable for those even if the 7Timer! portion is stale or absent),
  and means fresh enough (within max staleness) with a forecast horizon that
  actually covers the dark window — hours a snapshot does not reach count as
  missing.
- **Open-Meteo down, no usable cache** → cloud is truly missing (case 3).

The container always publishes an honest verdict.

**How this keeps "no single source load-bearing":** cloud data is *functionally*
required to reach GO, but no single *provider* is required to keep the system
running — the base provider sits behind a swappable interface, cache buffers
outages, and total absence degrades gracefully rather than failing.

### D7 — Contract stays frozen; growth is additive

M3 fills the existing stubbed fields; it does not reshape the document or the
MQTT surface. Whether to surface a conditions summary (e.g. window cloud
fraction, seeing) as **new additive fields** — which would add Home Assistant
entities — is deferred. If taken, it is additive and does not touch existing
fields' meaning.

### D8 — Two knobs only, per pier

`go_threshold` (the single tuning dial; global default with per-pier override)
and the opt-in `max_gust` (the wind gate's limit; absent → gate disabled). Every
other threshold, curve, and weight is fixed in code, so the system decides
rather than presenting sliders. Knobs are inputs, so they do not affect
determinism or the contract.

## Risks / Trade-offs

- **Cloud is functionally load-bearing for GO** → mitigated by cache + graceful
  degradation (D6) and a swappable interface; the rule's spirit (swappable,
  cached, degrades) holds even though a clear-sky GO needs cloud data.
- **7Timer! reliability / format drift** (an older free service) → it is
  secondary and optional; its absence only trims the score and confidence (D6).
- **Live forecasts break byte-identity** → the core is pinned against fixture
  snapshots; provider tests use recorded fixtures. Determinism is asserted on
  the core, not on live data (consistent with ADR0004).
- **Clarity curve and confidence curves are judgement calls** → they are fixed in
  code and covered by tests; a change to a curve is a deliberate, reviewed diff,
  not silent drift.
- **Provider-grid mismatch** (hourly vs 3-hourly) → resolved once in the provider
  layer (D2); the core never sees it.

## Resolved tuning values (task 5.1)

The deferred Open Questions are now settled. Each value is fixed in code and
locked by a test asserting representative inputs → expected outputs
(`tests/test_tuning_constants.py`), so a change is a deliberate, reviewed diff
rather than silent drift. The values remain judgement calls, not derived
constants; they are chosen to be sensible and are cheap to revisit.

- **Clarity curve `q(cloud)`** (`core/scoring`): linear ramp between a clear knee
  and an overcast knee — `q = clamp((90 − cloud) / (90 − 10), 0, 1)`. So cloud
  ≤ 10 % is fully usable sky (`q = 1`), cloud ≥ 90 % is none (`q = 0`, which lets
  the overcast gate fire on a genuinely socked-in sky), and 50 % → `q = 0.5`.
- **Score-term weights** (`core/scoring`): cloud 0.70, seeing 0.15, transparency
  0.15, normalised over whichever terms are present; the moon can cut the score
  by at most 0.50 when full and up throughout the usable darkness.
- **Lead-time `L`**: 1 within 3 h of dusk (or once mid-session), decaying
  linearly to a floor of 0.5 by 24 h out, then flat at the floor.
- **Freshness `F`**: 1 within 1 h of issue (the base refresh cadence), decaying
  linearly to a floor of 0.2 by 12 h old; a missing issue time counts as
  maximally stale (0.2).
- **Confidence floor**: 0.50, applied to the `L·F` sub-product only, so `K` still
  pulls incomplete forecasts down after the floor.
- **Band thresholds**: value ≥ 70 → HIGH, ≥ 40 → MEDIUM, else LOW.
- **Max cache staleness**: 12 h — aligned with the freshness stale point, so
  confidence has already decayed toward its floor before cache is dropped.
- **7Timer! resample**: hold — each 3-hourly value is held across its three
  hourly slots (simpler and defensible at forecast resolution; not interpolated).
- **Default `go_threshold`**: 65 (per-pier overridable).
