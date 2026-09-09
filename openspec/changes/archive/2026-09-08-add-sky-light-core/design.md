## Context

See proposal.md — Why. M1 froze the verdict-document contract and the MQTT pipe
with stubbed decision values. This change replaces the `produce_verdict` body
with real sun/moon astronomy behind that same signature, filling `dark_window`
and adding a `moon` object (see `specs/night-verdict/spec.md`). The durable
constraints in `openspec/config.yaml` apply — especially the pure/deterministic
core, "no load-bearing external source", and "HA never load-bearing for
correctness". The central engineering problem is not the trigonometry; it is
making the astronomy **deterministic and fully offline** so those constraints
hold once a scientific library enters the codebase. This design is the M2 analog
of M1's "retire the plumbing risk first".

## Goals / Non-Goals

**Goals:**
- Real astronomical-night window (sun < −18°) and a `moon` object, computed from
  the pier location and the injected clock instant only.
- Deterministic, byte-identical output across platforms and library patch
  versions, with zero runtime network access.
- Establish reusable, tested sky machinery (twilight crossings, moon
  rise/set/illumination) that M3–M5 build on.

**Non-Goals (design-level boundaries beyond the proposal):**
- No `targets` output and **no target alt/az engine**. The night-grid alt/az
  sampler is deferred entirely to M5, where the catalog and ranking define what a
  target needs; it has no consumer in M2, so building it here would be dead code
  at risk of a rewrite. `targets` stays `[]`.
- No horizon mask (M4), no weather/conditions (M3), no scoring changes — the
  verdict/score/confidence values stay as M1 stubs; only `dark_window` and
  `moon` become real.
- No catalog data of any kind (that is an M5 data concern, not an ephemeris one).

## Decisions

### D1 — Skyfield only; drop Astroplan/Astropy

Use Skyfield alone for all M2 math. Skyfield's `almanac.find_discrete` finds the
sun's −18° twilight crossings (dark window) and the moon's rise/set; Skyfield
gives moon phase/illumination and topocentric alt/az directly. The roadmap's
"Skyfield / Astroplan / Astropy" is treated as the *candidate set*, not a
mandate.

- **Why not Astroplan/Astropy too:** Astroplan sits on Astropy, and Astropy
  auto-downloads IERS earth-orientation data (`finals2000A`) at runtime for
  precise transforms. That single behaviour breaks *both* determinism (the data
  changes over time) and the offline constraint. Adopting it means fighting to
  disable the download; not adopting it removes the problem at the root, for a
  smaller image and less surface.
- **Precision note:** Skyfield on its built-in timescale is accurate to well
  within our needs (twilight to the second, alt/az to two decimals). We do not
  need Astropy's sub-arcsecond IERS precision.

### D1a — Which night: instant-relative selection, not calendar date

"Tonight" must be well-defined whether the core runs at 14:00 or at 01:00
mid-session, so the night is selected **relative to the evaluation instant**, not
by mapping the instant to a calendar date (which would compute the wrong night
after midnight). The rule: the selected night is the one whose astronomical dawn
is the **first dawn at or after the evaluation instant**. Concretely, search a
bounded horizon (~48 h) starting shortly before the instant for the sun's −18°
crossings; `end` = the first dawn (sun ascending through −18°) at or after the
instant; `start` = the dusk immediately preceding that dawn. If the instant is
already within darkness, this yields the current night; otherwise the next one.
Alternative (map instant → calendar date → that evening's dusk) rejected — it
silently evaluates a night ~17 h away when consulted after midnight.

**Extreme-latitude boundary cases.** `find_discrete` reports *zero* crossings for
both continuous night and continuous day, so they must be told apart by sampling
the sun's altitude at the instant (or across the span):
- sun continuously **below** −18° (polar winter — the best observing): the whole
  span is dark → `dark_window` is non-null. The window MUST be anchored to a
  **stable boundary** so it does not slide on every recompute. Anchor to the
  observer's **local solar day** — the 24 h from one local solar noon to the next
  (equivalently, centred on local solar midnight), computed from the sun's
  transit. A sliding "24 h from the instant" window is rejected: it would shift by
  the polling interval on every recompute, churning the Home Assistant recorder. A
  UTC-calendar-day anchor is *also* rejected: at longitudes near 0° (UK, West
  Africa) UTC midnight coincides with local solar midnight — the middle of the
  observing night — so the window would snap to the next block mid-session. The
  local-solar-day anchor envelops the local night without a mid-night jump, and
  local solar noon is well-defined at high latitude even when the sun never
  clears −18°. One singular exception: at the exact geographic poles
  (`abs(latitude) == 90`, which `PierConfig` currently permits) the sun does not
  transit a meridian, so the anchor MUST fall back to the UTC calendar day there
  — a pier exactly at a pole is degenerate, but the code must not raise.
- sun continuously **above** −18° (polar summer): genuinely no astronomical
  night → `dark_window` is `{null, null}`.
Conflating the two (treating "no crossings" as "no night") would blank out polar
winter, exactly when the site is most usable, so it is a first-class spec case
with its own tests.

### D2 — Deterministic, offline data: pinned ephemeris + built-in timescale

Two data inputs are needed and both are pinned with **no runtime download**:

- **Ephemeris** (sun/moon/earth positions, e.g. `de421`, ~17 MB, valid
  ~1900–2050). Preferred delivery: ship it as a **version-locked dependency**
  so `uv.lock` pins it exactly like every other dependency and Skyfield loads it
  from the installed path — no git-bloat, no bespoke build step, no runtime
  fetch. Fallback if the packaged route is awkward to hand to Skyfield: download
  once via a **shared `just fetch-ephemeris` task** that asserts a **SHA-256
  checksum**, invoked by *both* the Docker build and local developer setup — not
  hidden in the Dockerfile alone, or `just check` would run `pytest` against a
  missing ephemeris locally (Skyfield would then crash or try to fetch at runtime,
  tripping the offline-guard test). Either route keeps the file pinned and the
  local and container environments identical.
- **Timescale**: `load.timescale(builtin=True)` — leap-second/∆T data baked into
  the pinned Skyfield version. Fully offline; frozen by the library version that
  `uv.lock` already pins.

With a pinned ephemeris + built-in timescale + pinned Skyfield, verdict
production is a **pure function of (pier, clock)** and the determinism guarantee
rests entirely on the lockfile.

- **Alternatives rejected:** (a) Skyfield's default `load('de421.bsp')` — fetches
  on first use → non-deterministic and network-dependent at runtime; the
  anti-pattern. (b) A mounted cache volume populated on first boot — same
  problem, deferred one boot. (c) `finals2000A.all` for high precision —
  re-introduces a download to buy accuracy we do not need.

### D3 — Rounding is part of the contract

Full-precision floats can differ in their last bits across platforms and library
patch versions, threatening "byte-identical". The verdict document therefore
normalizes astronomical numbers to a **fixed decimal precision**. Crucially this
is applied at **validation/instantiation** (a pydantic `field_validator` /
`AfterValidator`), *not* only at serialization: if precision were dropped only in
the `@field_serializer`, the in-memory model would keep full precision while the
JSON dropped it, so `doc != model_validate(doc.to_json())` — breaking M1's
"serialize and read back with the same field values" round-trip requirement. The
existing `_require_aware_utc` field-validator is the natural home to also
`.replace(microsecond=0)`, and an `AfterValidator` rounds the illuminated
fraction; the serializer then merely formats an already-normalized value, so
in-memory and JSON agree and round-trip holds. Precision:
- angular values (alt/az, when later surfaced): 2 decimal places (degrees);
- illuminated fraction: 2 decimal places;
- timestamps: whole seconds, applied to **every** document timestamp uniformly
  (`generated_at` — `SystemClock.now()` carries microseconds too — as well as
  `dark_window.start`/`end` and `moon.rise`/`set`). Normalize in the shared
  datetime field-validator (`.replace(microsecond=0)`) so the stored value is
  already whole-seconds; the serializer additionally uses
  `isoformat(timespec="seconds")` as belt-and-braces. Doing it in the validator
  (not only the serializer) is what keeps the round-trip intact per the note
  above.

This is a spec requirement ("Astronomical fields are computed offline with
stable precision") realized as a serialization rule, mirroring M1's existing
fixed-key-order/`Z`-suffix determinism rules in `model.py`.

### D4 — Moon model shape ("shape B": behaviour across the window)

Add a `Moon` pydantic model, emitted as the document's `moon` field:
- `illumination: float` (0–1, 2 dp) — roughly constant across a night;
- `phase: MoonPhase` — a `StrEnum` of the eight standard phases, derived from the
  sun–moon elongation (phase angle 0–360°, measured as the moon's ecliptic
  longitude minus the sun's). The continuous angle maps to the discrete phases by
  **45°-wide octants centred on the cardinal points**: new = [337.5°, 22.5°),
  waxing crescent = [22.5°, 67.5°), first quarter = [67.5°, 112.5°), waxing
  gibbous = [112.5°, 157.5°), full = [157.5°, 202.5°), waning gibbous = [202.5°,
  247.5°), last quarter = [247.5°, 292.5°), waning crescent = [292.5°, 337.5°).
  The new-moon octant wraps the 0°/360° seam, so it is a modular/OR test
  (`angle >= 337.5 or angle < 22.5`), not a literal `337.5 <= angle < 22.5`
  (which is always false). Defining the boundaries makes the mapping
  deterministic and testable. An enum
  (not a freeform string) matches the existing `Verdict`/`Band` `StrEnum`s in
  `model.py` and gives downstream UI a stable set to match on;
- `up_during_dark: bool | None` — is the moon above the horizon at any point in
  the dark window; null when there is no dark window;
- `rise: datetime | None`, `set: datetime | None` — moon rise/set instants that
  fall **within** the dark window, else null.

The moon "horizon" is pinned to the **geometric centre at 0° altitude** (no
refraction, no lunar-radius correction), matching the spec — this removes the
determinism hole where a library's refraction default (~−0.83°) would shift
rise/set. Phase angle is `(moon ecliptic longitude − sun ecliptic longitude)
mod 360` — the modulo is required, since bare subtraction can go negative and
miss the octant checks. The `Moon` model's `rise`/`set` fields MUST carry the
same `@field_validator(...)` → `_require_aware_utc` (with the `microsecond=0`
normalization from D3) that `DarkWindow` uses, or sub-second precision leaks past
the truncation rule.

The across-window fields are null when `dark_window` is null (no astronomical
night). Rationale: a bright moon *above the horizon during darkness* is the moon
fact that changes a verdict, and it is computed with the same `find_discrete`
machinery as the twilight window — cheap to produce while we are already there.
Alternative (a bare instantaneous altitude snapshot at `generated_at`) rejected:
it misses moonrise/set inside the night, which is exactly what M3 scoring needs.

### D5 — Internal sky module

Add a pure core module (no HA/MQTT imports, consistent with the M1 boundary
test) — e.g. `pierpressure/core/sky.py` — exposing:
- `dark_window(pier, instant) -> (start, end) | (None, None)`;
- `moon_info(pier, dark_window, instant) -> Moon`.

The target alt/az night-grid sampler is **not** part of M2 (deferred to M5, per
the Non-Goals) — nothing in M2 would call it. `produce_verdict` orchestrates:
build the timescale + observer once, compute the window, compute the moon,
assemble the (still-stubbed verdict/score/confidence) document. Keeping the
engine in its own module keeps `producer.py` a thin orchestration seam and gives
M5 a clean place to add the sampler when it has a consumer. Alternative (inline
the math in `producer.py`) rejected — it would bury reusable machinery M3–M5 need
behind the producer.

### D6 — Determinism and offline enforced by tests

Mirror M1's "core must not import delivery" boundary test with:
- **Offline-guard test**: patch socket creation and assert `produce_verdict`
  makes no network access — so a future stray `load('…')` that reaches for the
  network fails CI rather than silently phoning home.
- **Pinned-instant determinism tests**: known site/date pairs (a mid-latitude
  site with a normal night; a high-latitude summer date with *no* astronomical
  night → null window) asserting exact expected `dark_window`/`moon` values, and
  that two runs are byte-identical.

## Risks / Trade-offs

- **Ephemeris-as-a-dependency may not hand cleanly to Skyfield.** → Fall back to
  D2's build-time download + checksum; both routes yield a pinned, offline file.
- **Skyfield/ephemeris version bump changes low-order digits and breaks
  byte-identity.** → The rounding rule (D3) absorbs small changes; determinism
  tests pin expected values, so a bump that shifts a rounded value is caught in
  CI and reviewed deliberately, not silently.
- **A value landing exactly on a rounding boundary (`x.xx5`) can flip across CPU
  architectures.** "Byte-identical across platforms" is therefore a strong claim
  with a caveat: `round()` on a value at the half-way point can differ by an ULP
  between, say, amd64 and arm64. → In practice mitigated because (a) astronomical
  values almost never sit exactly on a 2-dp boundary, and (b) the pinned-value
  determinism tests run in CI catch any drift; the honest framing (reflected in
  the spec) is "deterministic for a given platform and pinned library set, with
  CI guarding cross-platform drift", not an absolute cross-architecture identity
  guarantee. If a real boundary case ever bites, add a tiny stable epsilon before
  rounding to force a consistent direction.
- **`find_discrete` reports zero crossings for both continuous night and
  continuous day.** → Disambiguate by sampling the sun's altitude (D1a):
  continuous darkness → non-null window covering the dark span; continuous
  daylight → null. Both are first-class spec scenarios with dedicated tests, so
  polar winter is never blanked out as "no night" and neither case raises.
- **Image size grows by the ephemeris (~tens of MB).** → Accepted; it is the
  price of offline determinism and is bounded by choosing a compact ephemeris
  (`de421`), not a full-range one.
- **First heavy scientific dependency enters the image.** → Contained to the
  pure core module; the core/delivery boundary and offline-guard tests keep the
  blast radius visible.

## Open Questions

- Exact ephemeris artifact (`de421` vs a smaller trimmed range) and whether the
  locked-dependency route or the build-time-checksum route is used — a packaging
  detail that does not change the specs, the approach, or the task breakdown, so
  it is settled during implementation against whichever loads cleanly with the
  pinned Skyfield.
