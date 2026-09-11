## Context

See `proposal.md` — Why for the motivation. The shipped verdict scores cloud from
a single `BaseHour.cloud_cover` percentage, which cannot tell a low deck that
blocks the view apart from high, thin cirrus that reads near-clear on the total
yet wrecks transparency.

The pieces this change touches already exist and constrain the approach:

- **The conditions model** (`pierpressure/core/conditions.py`) carries cloud on
  `BaseHour`, a frozen dataclass whose fields are each independently optional
  (`None` = unavailable). The per-source group model (`BaseGroup`/`Conditions`)
  landed in M3.5. Note the model uses `BaseHour`/`BaseGroup`, not the
  `CloudHour`/`CloudGroup` names the proposal wrote from memory.
- **The provider seam** (`pierpressure/conditions/provider.py`) parses each source
  into `SourceReading`/`SourceForecast`, then `assemble_snapshot` promotes those
  into the core groups. `open_meteo.py` is the base source.
- **The scoring core** (`pierpressure/core/scoring.py`) rests on one idea (design
  D3): a per-hour clarity weight `q` and coverage weight `w`. The banded score is
  a weighted mean of quality terms (cloud dominant, seeing, transparency), cut by
  a **moon penalty** — a multiplicative factor that lowers the score but never
  gates. The high/thin-cloud term is the same shape as that moon penalty.

The durable constraints that bind this change: the verdict document is a frozen
contract that may only grow additively; gates, bands, and confidence stay as they
are; the core stays pure and deterministic, so any score movement is covered by
re-based pinned tests.

## Goals / Non-Goals

**Goals:**

- Carry the low/mid/high cloud component split through the model and provider
  layer as independently-optional fields, alongside the unchanged total.
- Add one distinct, itemized high/thin-cloud penalty to the banded score,
  separate from the total-cloud term, that never gates and degrades to nothing
  when the high component is missing.

**Non-Goals:**

- No new document field. The term surfaces only as a `reasons[]` line; the
  delivery surface and existing field meanings are untouched.
- No new gate and no change to confidence. High cirrus lowers the score, never
  the go/no-go gates, and the completeness factor `K` is left exactly as it is.
- No score term for the low or mid components this milestone. They are carried in
  the model for honesty and future use, but only the high component feeds math
  now.

## Decisions

### D1: Carry all three components as flat optional fields on `BaseHour`

Add `cloud_low`, `cloud_mid`, `cloud_high` (each `float | None`, percent, default
`None`) to `BaseHour`, mirroring the existing `cloud_cover`/`wind_gust` idiom.
Thread the same three fields through `SourceReading` and `assemble_snapshot`.

- **Why flat fields over a nested cloud object?** The existing per-field
  availability rule and the `at()`/`_by_time` lookup work on flat optional
  attributes. A nested object would need its own absence handling and would read
  unlike every neighbouring field. Flat fields keep total-only sources valid with
  no special case: the components simply default to `None`.
- **Why carry all three when only `high` is scored?** Open-Meteo returns the split
  as a set, and the `conditions` capability describes the whole low/mid/high
  split. Carrying all three now means later milestones (a low-deck term, say)
  need no further model change — additive once, not twice.

### D2: Score high cloud as a multiplicative penalty, like the moon

Introduce a `high_cloud_penalty(window, conditions)` computed like
`optional_term_mean` — **not** like `moon_penalty` — so missing high-cloud data
never dilutes the penalty. It is the clarity-weighted mean of `cloud_high / 100`
over exactly the hours that carry **both** `cloud_cover` and `cloud_high`:

```
numerator   = Σ_{h: cloud_cover(h) and cloud_high(h) present}  w·q · (cloud_high(h)/100)
denominator = Σ_{h: cloud_cover(h) and cloud_high(h) present}  w·q
penalty     = numerator / denominator            # None when denominator == 0
```

The denominator is restricted to the same both-present hours as the numerator, so
an hour missing `cloud_high` is excluded from both rather than adding `w·q` to the
denominator alone (which would spread the penalty thin and read missing cirrus as
clear sky). This mirrors `optional_term_mean` (`scoring.py`), which restricts its
denominator the same way and returns `None` when no hour qualifies. `moon_penalty`
can safely divide by all clear hours because moon-up is defined for every hour;
`cloud_high` is optional, so it cannot. Fold the resulting penalty (a value in
`[0, 1]`, or `None`) into `assemble_score` as an independent factor:

```
score01 = quality * (1 - _MOON_MAX_PENALTY * moon_penalty)
                  * (1 - _HIGH_CLOUD_MAX_PENALTY * high_cloud_penalty)
# high_cloud_penalty is None → its factor is 1 (the term drops out entirely)
```

The two penalties are independent multiplicative factors, so a full moon and heavy
cirrus stack (for example `(1 - 0.50)·(1 - 0.30) = 0.35`). This is monotonic and
safe; `_HIGH_CLOUD_MAX_PENALTY` is tuned in the awareness that it compounds with
the moon penalty rather than adding to it.

- **Why a penalty, not a fourth weighted quality term?** A weighted term would
  blend into the normalised weighted mean and read as a "quality %" line, not a
  penalty; it would also interact with the missing-term weight renormalisation.
  The multiplicative-cut shape matches the moon precedent (the mean itself is
  computed like `optional_term_mean`, per above), is trivially monotonic
  (`1 - k·penalty` only ever lowers the score), can never gate, and produces its
  own distinct reason — every property the spec asks for.
- **Why clarity-weight it (`w·q`)?** Weighting by `q` means an hour that is
  already fully overcast (`q = 0`) contributes nothing to the high-cloud penalty,
  because it is already penalised by the total-cloud term. The high-cloud penalty
  therefore bites precisely where it should: on hours that read otherwise clear
  but carry cirrus aloft. This also satisfies the spec's "weighted toward the
  usably clear hours" requirement.
- **Missing data:** when no window hour carries `cloud_high`, the helper returns
  `None`; `assemble_score` treats the factor as 1 and `_score_reasons` emits no
  high-cloud line — the same drop-out the optional terms already use.
- **Constant:** `_HIGH_CLOUD_MAX_PENALTY` joins the fixed tuning block at the top
  of `scoring.py`. A starting magnitude below the moon's `0.50` (around `0.30`)
  keeps thin cirrus a meaningful but non-catastrophic hit; the exact value is a
  reviewed constant, not configuration.

### D3: Emit a distinct reason line only when the penalty bites

In `_score_reasons`, after the existing `Cloud:` line and alongside the moon line,
append a high-cloud line (for example, `High cloud penalty N% (thin cirrus
aloft).`) only when the penalty is present **and its rounded percentage is greater
than zero** — that is, `penalty is not None and round(penalty * 100) > 0`. Guarding
on the rounded value (not the raw `> 0.0` the moon line uses) avoids emitting a
confusing `High cloud penalty 0%` line for a sub-half-percent penalty. This keeps
the term separate and itemized and keeps the reasons list unchanged for nights
with no cirrus or no high-cloud data.

### D4: Extend the Open-Meteo fetch to actually request the components

The proposal says the base provider "already fetches the components"; it does not.
`open_meteo.py` requests `hourly=cloud_cover,wind_gusts_10m`. This change adds
`cloud_cover_low,cloud_cover_mid,cloud_cover_high` to that request and parses each
into `SourceReading`, leaving an absent/`null` value as `None`. A recorded fixture
carrying the component arrays covers the parser with no network.

## Risks / Trade-offs

- **Double-counting on partly-cloudy hours** → thick high cloud raises both the
  total `cloud_cover` (lowering the total-cloud term) and the high-cloud penalty.
  Mitigation: the clarity weighting means fully-overcast hours add no penalty, so
  the overlap is confined to partly-clear hours where treating cirrus as extra
  bad is the intended, conservative behaviour — not a bug.
- **Golden verdict output shifts** → scored nights with high cirrus now score
  lower, so the M3.5 golden fixture changes. Mitigation: re-base that one golden
  once, deliberately, in this change's PR (the proposal calls this out), and keep
  the pinned-value tests as the determinism guard.
- **Backward compatibility of the model** → every new field defaults to `None`, so
  existing fixtures, total-only sources, and the `Conditions(None, None)` empty
  value stay valid without change. The boundary and offline tests still hold
  because no import or I/O is added to the core.
- **Confidence drift** → deliberately avoided. High-cloud coverage is *not* folded
  into `completeness_factor`, so a source that returns a total but no components
  does not lower confidence. Confidence stays a function of the same fields as
  before.
