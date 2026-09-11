## Context

See `proposal.md` — Why. This change adds the horizon mask (M4) as pier site data with
no verdict consumer yet; M5 consumes it. The relevant existing state:

- `pierpressure/core/config.py` already loads YAML, validates each pier independently
  (an invalid pier is logged and skipped; zero valid piers is a hard failure), and
  expands `${ENV}` in strings. `PierConfig` today holds `id`, location, and two tuning
  knobs.
- The core is pure and offline: `test_core_boundary` forbids HA/MQTT imports in
  `core/`, and `test_offline_guard` forbids runtime network access. `produce_verdict`
  is a pure function of `(pier, clock, conditions)`.
- Azimuth/altitude already appear in the sky math (Skyfield alt/az), but target alt/az
  sampling is deferred to M5, so nothing yet queries a horizon.

## Goals / Non-Goals

**Goals:**

- One canonical horizon shape — ordered `(az, alt)` samples — that every source
  (inline, floor, absent, imported) produces, so the query and all downstream code are
  source-agnostic.
- A pure, deterministic query seam (`altitude at azimuth`; `is a point above the
  horizon`) that M5 can consume without change.
- Keep file I/O out of the core's verdict path: horizon **text** is parsed to samples at
  config-load time, never inside `produce_verdict`.

**Non-Goals:**

- Any verdict-document, topic, or entity change (locked by a spec requirement).
- Target sampling or ranking (M5), and the Stellarium/Telescopius importers (fast-follow
  once real fixtures exist).
- Combining a flat floor with terrain samples, or per-azimuth floors — a horizon has
  exactly one source.
- Surfacing the horizon in the verdict document. M4 keeps the document byte-identical,
  but this does **not** foreclose a later milestone shipping a (likely downsampled)
  horizon array additively so Home Assistant can draw the mask and explain why a target
  was rejected — that is the contract's expected additive growth, deferred until a
  consumer needs it, not a door closed here.

## Decisions

### D1 — Canonical representation: sorted `(az, alt)` samples, linear interp, cyclic

The horizon is an azimuth-sorted tuple of `(az, alt)` samples; querying an arbitrary
azimuth linearly interpolates the two bracketing samples, and the sample set is a closed
ring (the arc from the largest az back to the smallest wraps across 360/0). **Why:** it
is exactly what NINA/Stellarium/Telescopius files already are (an `az alt` list the
tools draw as a linear polygon), so imports round-trip and users' previews match.
**Alternatives:** a fixed-step altitude array (rejected earlier — a new shape nobody
exports); step/nearest interpolation (rejected — disagrees with how the tools draw the
polygon). This representation and the azimuth convention are hard to reverse once
importers and M5 bind to them, so they are pinned in an ADR.

Three sharp edges of this representation are pinned so the query is total and
deterministic:
- **Complete ring, not an overlay.** The samples define the horizon for the whole
  circle; the wrap segment (greatest az back to least) is a real interpolated segment.
  A sparse list therefore does not leave "unmentioned" directions open — it interpolates
  across them. This is correct for a full-circle export but a footgun for hand-authored
  points, so the spec documents the anchor idiom (bound a localized obstruction with 0°
  samples) rather than silently auto-filling flat 0, which would need an ill-defined
  notion of a "gap" in a ring.
- **Single sample is constant.** One sample (and the `min_altitude`/flat-0 cases, which
  are one sample) returns that altitude everywhere with no interpolation — no
  divide-by-zero on a zero azimuth span.
- **Fixed query precision.** `alt_at(az)` rounds its interpolated result to a defined
  decimal precision, mirroring `_round_fraction` in `model.py`, so an unrounded float
  cannot flip M5's `>=` classification at a grazing boundary across platforms
  (ADR-0004's determinism guarantee extends to the horizon).

### D2 — Azimuth convention normalised at the edge

Canonical azimuth is north-zero, clockwise. Each importer is responsible for normalising
its source convention (NINA and Telescopius are north-zero; Stellarium landscapes are
sometimes south-zero) **before** the samples enter the canonical form. **Why:** keeps
the core convention single and the query trivial; pushes the one place conventions
differ into the thin adapter that knows the format. This is why importers are more than
delimiter-splitting and each needs a real fixture to pin.

### D3 — One source per pier, three inputs, resolved at config load

`PierConfig` gains an optional `horizon` block that is one of: inline `points`
(`list[[az, alt]]`), a scalar `min_altitude` floor, or a file reference
(`{ file, format }`). Absent → flat 0. These are mutually exclusive; more than one is a
validation error. A `file` reference is read and parsed to canonical samples **during config load**.
`load_config` resolves the config file's own directory and passes it as Pydantic
**validation context** (`model_validate(raw_pier, context={...})`, read back via
`ValidationInfo.context`) into per-pier validation; a **relative** horizon path is then
resolved against that directory rather than the process working directory. The file
read and parse run *inside* per-pier validation, so a missing file, an unreadable file,
or a malformed one raises a `ValidationError` that the existing `validate_piers` loop
already catches — logging and skipping just that pier — rather than crashing the load or
duplicating the isolation logic (this is what keeps D3 and D5 consistent). The resolved
`PierConfig` a pier carries already holds plain samples, so `produce_verdict` never
touches the filesystem. Range normalization that belongs to file quirks — azimuth 360
folded to 0, sub-horizon altitude clamped to 0 — is applied by the importer as text
becomes samples. **Why:** matches the existing config-load-time `${ENV}` expansion,
reuses the per-pier isolation already in `validate_piers`, and keeps the core
pure/offline. **Alternative rejected:** reading files in `load_config` *before*
`validate_piers` — it would have to re-implement the per-pier log-and-skip isolation for
read/parse errors, so passing the base directory as validation context is simpler. `min_altitude` and
flat-0 are the degenerate one-sample case of the same representation, so the query has a
single code path. **Alternatives:** parsing inside the core (rejected — breaks purity
and the offline guard); a separate horizon file always required (rejected — inline and
floor cover the hand-authored and simple cases without a file to manage).

### D4 — Parsers take text, not paths; importers are a registry keyed by format

`core/horizon.py` exposes pure functions: build-from-pairs, and per-format parse-from-
text (NINA now). The config layer reads the file bytes and hands text to the parser.
Unsupported formats (Stellarium, Telescopius) are registered names that raise a clear
"not yet supported" error. **Why:** parsers stay unit-testable without the filesystem
and inside the offline guard; adding Stellarium later is a new text parser plus a fixture,
touching nothing else. **Alternatives:** parsers that open files (rejected — same purity
break as D3).

### D5 — Per-pier validation isolation reuses the existing path

An invalid horizon (bad range, duplicate azimuth, two sources, unsupported format,
malformed file) fails that pier through the existing `validate_piers` isolation: it is
logged and skipped, valid piers continue, zero valid piers stays a hard failure. **Why:**
one bad horizon should not silence a whole multi-pier install, and the behaviour already
exists — the horizon just feeds into it.

## Risks / Trade-offs

- **NINA `.hrz` syntax is assumed, not verified** (headers, comment character, exact
  delimiter) → parse against a **real** exported `.hrz` fixture committed under
  `tests/fixtures/`, not a hand-guessed one; treat any deviation the fixture reveals as
  the spec of the format.
- **Building a seam with no live consumer** (M5 is the consumer) → mitigated by a
  directly testable contract (`alt_at(az)`, above/below classification) exercised by
  unit tests, plus the byte-identical-document requirement that proves M4 changed no
  observable output.
- **Azimuth convention mismatch on import** (south-zero vs north-zero) → D2 normalises in
  the importer; the NINA fixture test asserts a known obstruction lands at the correct
  canonical azimuth, catching a convention slip.
- **Interpolation at the wrap seam is an easy off-by-one** → an explicit scenario and
  test query azimuths inside the wrap arc, not only between interior samples.
- **A sparse hand-authored horizon silently blocks the sky** — `[[170, 40], [190, 40]]`
  interpolates 40° across the whole northern sky through the wrap → the spec pins the
  complete-ring semantics, documents the 0°-anchor idiom, and carries a scenario that
  asserts az 0 reads 40 (not open), so the behaviour is defined and controllable rather
  than a surprise. Not mitigated by auto-filling flat 0 (an undefined "gap" in a ring).
- **Float interpolation leaks platform precision into M5's `>=` boundary** → `alt_at`
  rounds to a fixed precision, and the boundary is `>=`; a pinned-value test guards
  cross-platform identity as the rest of the core does.
- **A real `.hrz` closes its polygon at az 360 or dips below 0°** and would fail strict
  ranges → the importer normalizes 360→0 and clamps sub-horizon altitude to 0 rather
  than reject the file; the fixture test exercises both.
- **A very large or pathological horizon file read at config load** (e.g. a symlink to
  `/dev/zero`) → a horizon file is operator-supplied local config at the same trust level
  as `config.yaml` itself, which `load_config` already reads unbounded, so this crosses
  no new trust boundary and is not load-bearing. A sane size/line-count sanity cap MAY be
  added defensively, but it is not a gate: the operator controls their own config.
