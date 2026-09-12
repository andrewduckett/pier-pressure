## Context

See proposal.md — Why. This design covers *how* the two suitability terms enter
the ranking without breaking the frozen contract or the deterministic core.

Current state the design builds on:

- `core/ranking.py` scores each gated target from **four** sub-scores — altitude,
  window, moon, transit — with fixed module-constant weights that **sum to 1.0**,
  scaled to an integer 0–100. Rankings are cached per night on a key of pier
  geometry plus the dark window.
- `core/catalog.py` filters candidates to observable types with recorded
  magnitude at or brighter than `MAGNITUDE_LIMIT = 13.0` (unknown magnitude kept).
  It parses `MajAx` into `size_arcmin` — already stored, "for future
  field-of-view work, not emitted now" — and `V-Mag`/`B-Mag`. The pinned OpenNGC
  data *also* carries `SurfBr` (surface brightness, mag/arcsec²), `MinAx`, and
  `PosAng`, which the parser does not yet read.
- `core/config.py` `PierConfig` has no equipment fields.
- `Target` (`core/model.py`, contracted in `night-verdict`) emits geometry only:
  `id, name, type, score, window, max_altitude, transit_time, moon_separation`.

## Goals / Non-Goals

**Goals:**

- Add a field-of-view-fit term and a brightness term to the ranking score.
- Keep the score a deterministic, banded 0–100 for the same `(pier, instant)`.
- Degrade gracefully: rank sensibly with no rig configured, and with objects that
  lack a size or a magnitude — without substituting guessed values.
- Grow the verdict document additively; break no existing field or delivery
  surface.

**Non-Goals (design-level boundaries beyond the proposal's scope):**

- Multiple rigs per pier and per-target best-rig selection.
- Rotation-aware framing (`MinAx` + `PosAng` ellipse fit); this milestone treats
  the object as a `MajAx` circle.
- A pixel-scale / sampling / seeing-match term (a later equipment refinement).
- Brightness as a *gate*; it is a score term only. The `MAGNITUDE_LIMIT` candidate
  filter keeps its current role and value.
- Feeding equipment or brightness into any LLM layer.

## Decisions

### D1 — Equipment is raw optics, not a pre-computed field of view

Add an optional `rig` to `PierConfig`: `focal_length_mm`, `sensor_width_mm`,
`sensor_height_mm`, and `reducer` (default `1.0`). The core derives the field of
view; the config never carries a pre-chewed FOV.

*Why:* it matches how imagers describe gear, the derivation is trivial and pure,
and it leaves room for later equipment-driven terms (pixel scale, sampling) with
no config break. *Alternative — a direct `fov_width_deg`/`fov_height_deg`:*
rejected; it pushes arithmetic onto the user and closes the door to those later
terms. *Alternative — a list of rigs:* rejected for this milestone; it forces
per-target best-rig selection and balloons scope.

### D2 — Field of view derived from the effective focal length

Effective focal length `f_eff = focal_length_mm * reducer` (a 0.8 reducer widens
the field; a 2.0 barlow narrows it). Per axis,
`FOV_axis = 2 * atan(sensor_axis / (2 * f_eff))`, in degrees. Both axes are
computed; the **short edge** is the fit reference (see D3).

Focal length, both sensor dimensions, and the reducer are validated as **strictly
positive** at config load (a `Field(gt=0.0)` constraint, mirroring the existing
`max_gust` precedent). A non-positive value is a pier configuration error, not a
runtime crash — so `f_eff` and `fov_short` are never zero and D3's
`r = size / fov_short` never divides by zero.

### D3 — FOV fit is a framing curve on the short edge, object as a circle

Define `r = size_arcmin / fov_short_arcmin` (FOV in arcmin = degrees × 60). The
fit sub-score is a curve on `r`:

```
  fit(r)
   1.0 |         ___________
       |        /           \
       |       /             \
       |    __/               \__
   lo  |  _/                     \____
   0.0 +--+-------+-------+-------+-------+--> r
         speck  ~0.1    ~0.6    1.0    >1.5
        (tiny)   |<- sweet band ->|  (won't fit)
```

- A **speck** (`r` near 0) scores a low floor, not zero — a tiny object is still
  imageable, just not ideal.
- The **sweet band** (a comfortable fraction of the frame) scores ~1.0.
- Past `r = 1` the object no longer fits; the score decays rather than cliffs, so
  a slightly-too-big (mosaic-able) object beats a hugely-too-big one.

Both new sub-scores (fit and brightness) are clamped to `[0, 1]` like the four
existing ones, so the renormalised weighted sum stays in `[0, 100]`.

*Why the short edge:* it is the true "does it fit" constraint — an object wider
than the short edge is cropped at any rotation. *Alternative — diagonal:* rejected;
it can call an object a fit that the frame cannot actually contain. *Why a
MajAx circle:* the major axis is the conservative fit test and needs no frame
rotation. *Alternative — `MinAx`+`PosAng` ellipse:* deferred (a Non-Goal).

### D4 — Brightness prefers surface brightness, then magnitude

The brightness input is `SurfBr` where the catalog records it, else `V-Mag`, else
`B-Mag`, else unknown. The sub-score is monotonic — brighter (numerically smaller
magnitude) scores higher — clamped to `[0, 1]`. Surface brightness
(mag/arcsec², roughly 18–25) and integrated magnitude (roughly 0–13) are
**different physical scales**, so each is mapped through its **own** anchors, never
a single shared curve — otherwise an object judged by surface brightness would
score as far "fainter" than one judged by integrated magnitude purely because its
numbers are larger. D6 tunes the anchor values on the validation night; the
two-scale structure is fixed here.

*Why surface brightness first:* for extended deep-sky objects it predicts
detectability far better than integrated magnitude — a mag-9 galaxy smeared over
half a degree is much harder than a compact mag-9 planetary — and `SurfBr` ships
in the pinned data, so nothing is derived. *Keep the `MAGNITUDE_LIMIT` candidate
filter:* it is partly a performance cap (it reduces the ~14k-row catalog to a few
thousand the coarse grid scan can afford). Its role simply splits cleanly — the
filter is the candidate cap, brightness ranks *within* the survivors.

### D5 — Unknown terms drop and the weights renormalise (the crux)

The four fixed weights become **six** base weights. For each `(pier, target)`,
form the **live** subset of terms and renormalise their weights to sum to 1
before the weighted sum:

```
  term        live when
  ---------   ------------------------------------------
  altitude    always (geometry)
  window      always (geometry)
  moon        always (geometry)
  transit     always (geometry)
  brightness  a brightness value is known for the object
  fov_fit     a rig is configured AND the object has a size
```

So a rig-less pier ranks on five terms; an object with unknown size drops only
`fov_fit`; an object with unknown magnitude drops only `brightness`. The score is
always the honest combination of what is actually known.

*Why drop-and-renormalise over a neutral fixed value:* it never guesses. A neutral
mid-value would let an object with unknown size *and* magnitude ride on a
fabricated middle; dropping the terms scores it purely on placement, which is all
we know — the same philosophy as M5's "unknown magnitude is kept, not scored."
One mechanism covers both the no-rig case and missing per-object data. Determinism
is unaffected: the live set and the renormalised weights are a pure function of
the inputs.

### D6 — Weights and curve constants are set on a validation night

The six base weights, the framing-curve shape (`speck` floor, sweet-band edges,
over-size decay), and the brightness-curve anchors are fixed **module constants**,
their values chosen and retained on a real validation night — the method M5 used
in its task 8.2. The *structure* is decided here; the *numbers* are tuned there
and documented inline with the night they were validated against.

### D7 — The rig joins the ranking cache key

Rankings now depend on the configured rig, so the rig's fields join
`ranking.py`'s per-night `_cache_key`. Design D5 of the M5 ranking already
anticipated config-driven parameters entering the key. A test asserts that
changing the rig changes the ranking for an affected night.

### D8 — Additive document growth: raw facts, not a derived blend

Each `Target` additionally carries `size_arcmin`, `magnitude`, and
`surface_brightness` (each present always, `null` when the catalog records no
value — matching the frozen contract's emit-every-key rule). The document emits the
**raw catalog facts**, not the internal choice the brightness factor makes, so
downstream consumers (and the M7 LLM explainer) see the real numbers. The emitted
`magnitude` is the catalog's existing M5 visual-then-blue value (the same one used
as the candidate filter); it is deliberately distinct from the brightness factor's
internal input, which is `surface_brightness`-else-`magnitude`.
`reasons[]` gains equipment-aware, additive entries (for example "well framed for
your rig", "bright target"). No existing field changes meaning.

### D9 — Fixed-precision rounding hardens cross-platform score stability

The derived field of view and the pre-scaled renormalised score are rounded to a
fixed decimal precision *before* the final integer scaling, mirroring the
document's existing emitted-field precision (`max_altitude` and `moon_separation`
round to 3 decimals) and the horizon-mask precision posture.

*Why:* the M5 score already runs float trig (`sin`) and float division into
`round(100.0 * weighted)`, reconciled by pinned-value CI tests *within* a platform
(ADR-0004; night-verdict "stable precision") rather than an absolute
cross-architecture bit guarantee. The new `atan` (FOV) and the renormalisation
division are the same class of operation, so they inherit that posture rather than
break it — but rounding the FOV and the pre-scaled weighted float shrinks the
epsilon surface around integer `.5` boundaries, so a score is far less likely to
flip across architectures. The rule applies uniformly to the existing and new
sub-scores' combination. Within-platform determinism is unchanged, and the
pinned-value tests extend to the two new (`atan`- and renormalisation-based) terms.

## Risks / Trade-offs

- **Golden target lists shift** — brightness and renormalisation change scores on
  every night, and even a rig-less pier now gets the brightness term. → Re-baseline
  the golden outputs on the validation night; the determinism and pure-core
  boundary tests are unaffected and still assert byte-identical output.
- **Scores across objects use different weight vectors** when their known-term
  sets differ. → Accepted; it is the honest reading and mirrors M5's
  unknown-magnitude rule. Documented so a reader is not surprised that an
  unknown-size object was scored on five terms and its neighbour on six.
- **Framing and brightness curves are judgement calls.** → Keep them as named,
  documented constants tuned on a real night; start conservative so no term
  dominates the four geometry terms.
- **Reducer/barlow sign confusion.** → Define `f_eff = focal * reducer`
  explicitly and validate derived FOV against a known rig in a test.
- **`SurfBr` is sparse for some types.** → Fall back to integrated magnitude, then
  to dropping the term; never fabricate a value.

## Migration Plan

Additive and stateless — no data migration. The `rig` config is optional, so
existing configurations load unchanged; a pier with no rig simply ranks without
the `fov_fit` term. Deploying does change rankings for every pier (the brightness
term and renormalisation apply with or without a rig — that is the milestone's
intent), so the change lands together with re-baselined golden outputs. Rollback
is a plain revert; there is no persisted state to unwind.

## Open Questions

- The exact base-weight values and curve constants (D6) are resolved during
  implementation on the validation night. They change none of the specs, the
  approach, or the task breakdown — only the tuned numbers behind fixed
  constants — so they are safe to settle then rather than now.
