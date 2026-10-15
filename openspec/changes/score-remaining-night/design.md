## Context

The proposal says why; `specs/night-verdict/spec.md` says what. This design
resolves two constraints: the score must not exceed its usable-sky share, and
the verdict must narrow to the rest of the night without changing any
existing document field or the whole-second timestamp rule.

Facts that shape the approach:

- **The score already has multiplicative factors.** `assemble_score` in
  `pierpressure/core/scoring.py` takes a weighted mean of the cloud, seeing and
  transparency terms, then multiplies by a moon factor and a high-cloud factor.
  Seeing and transparency are the only terms that add rather than scale.
- **Seeing and transparency already describe the clear hours only.**
  `optional_term_mean` weights each hour by its clarity, so a term's mean says
  how good the clear sky is. It says nothing about how much clear sky there is.
- **Every condition rule takes a window argument.** The gates, the score terms,
  the moon penalty and the completeness factor each take `(start, end)` and
  tile it into clock-hour slots with a coverage weight. None of them reads the
  evaluation instant. Changing the window they receive changes all of them at
  once.
- **`evaluate` already has the instant.** It uses it for lead time and
  freshness. The lead-time factor is already 1 once the instant is past dusk.
- **The moon's rise and set are found over the whole dark window.** `moon_up_at`
  reads them from the `Moon` value, which `moon_info` computes before scoring.
  Asking whether the moon is up at an instant inside a shorter window gives the
  same answer, so the moon term needs no new astronomy.
- **The producer builds the document from the window and the decision.**
  `produce_verdict` in `pierpressure/core/producer.py` passes the whole dark
  window to `evaluate` and to `rank_targets`, then emits `dark_window`.
- **The golden tests lock the document byte for byte.** Every scored golden
  under `tests/fixtures/golden/expected/` changes with this design, and the
  suite is regenerated with `PP_WRITE_GOLDENS=1`.

## Goals / Non-Goals

**Goals:**

- A night's score never exceeds its usable-sky share. Good atmosphere refines a
  clear night; it cannot rescue a cloudy one.
- Once the night has started, the verdict answers "is the rest of tonight
  worth it", with the same math it already uses.
- The core stays a pure function of the pier, the instant and the conditions.

**Non-Goals:**

- Target ranking on the remaining night (issue #110).
- A new clarity curve, moon penalty or high-cloud penalty.
- Any change to how confidence's lead time and freshness work.

## Decisions

### D1. The scored window is the dark window clamped to start no earlier than the scoring instant

`evaluate` first floors the evaluation instant to a whole second: the
**scoring instant**, `now = instant.replace(microsecond=0)`. The document
already floors `generated_at` the same way, so the two are equal. It then
computes `scored = (min(max(now, start), end), end)` from the dark window.
`evaluate` is the only caller that needs `now`; the producer passes the raw
instant as today and `evaluate` floors it. The
inner `max` drops the hours that have passed. The outer `min` keeps the start
from passing the end. `evaluate` passes `scored` to every condition rule: the
overcast gate, the wind gate, wind coverage, cloud availability, the score and
the completeness factor. The lead-time factor keeps reading the dark window's
start, which gives 1 once the night has begun, as today.

```
dark window       |<------------- dusk .......... dawn ------------->|
now before        ^                                   scored = dark
now inside                  ^-------- scored -------------------------|
now == floored dawn                                                   ^  scored empty
```

`evaluate` returns `scored` on the `Decision`, and the producer emits it as
`scored_window`. One computation feeds both, so the emitted span and the span
the verdict judged cannot differ, and `scored_window.start` equals
`generated_at` mid-session by construction.

*Why floor the instant before clamping:* every document timestamp is floored to
a whole second at validation. Clamping with the raw instant would score from
22:00:00.400 and report 22:00:00. Flooring first keeps the document honest, and
costs at most one second of already-elapsed time.

*Why the outer `min`:* `dark_window` picks the first exact dawn crossing at
or after the raw instant, then floors both bounds to a whole second. So an
instant in the last partial second of the night, up to and including the
crossing, selects the ending night. Its floored `end` equals `now`. Without
the `min`, a raw instant later in that second would start after the end and
tile no slots, which reads as "no cloud data". The `min` folds that case into
the empty-window path (D2). An instant after the crossing selects the next
night. A test pins the boundary with an instant that carries microseconds.

*Why clamp inside `evaluate` and not in `dark_window`:* the `dark_window` field
is a frozen contract, and the moon and the targets still need the whole night.
One clamp at the one place that decides the verdict keeps every other reader
unchanged.

*Alternative, a separate "session window" concept with its own module:*
rejected. The clamp is two lines, and the rules already take a window.

### D2. An empty or short scored window cannot be GO

When `scored` starts and ends at the same instant, `evaluate` returns `MAYBE`,
score 0, with a reason that no dark time remains, before it reads any cloud
data. This can only happen when `now` equals `dark_window.end` (D1).
Confidence comes from the usual lead time and freshness, with completeness at
0 because the window covers no hour. This path sits after the no-dark-window
gate and before the wind gate.

When `scored` is narrowed and shorter than `MIN_REMAINING` (60 minutes), the
gates and the score run as usual, but a `GO` is capped at `MAYBE` with the
reason "Less than an hour of dark time remains." This is the same cap shape
as the missing-wind rule. `MIN_REMAINING` matches the ranking's minimum target
window, so the verdict and the target list agree on what a usable span is. A
whole night shorter than an hour is not narrowed and is not capped; the night
is what it is.

*Why a cap and not a gate:* a failed gate is the only cause of a `NO-GO`, and
"not much night left" is not a condition gate. The score stays honest about
the sky; the cap stops it from saying "set up now".

*Why not let an empty window fall through:* an empty window has no slots. The
cloud availability check would then read "no cloud data", and the verdict
would say "conditions unavailable", which is false. The overcast gate cannot
fire either, because it needs cloud data present.

*Why not scale the score by the remaining length:* the usable-sky term is a
share so that a short night and a long night with the same clear fraction
score the same, which the spec requires. A length factor would also change
every pre-dusk score on short summer nights.

The transition near dawn is then: `GO` while an hour or more remains, `MAYBE`
with the computed score for the last hour, `MAYBE` with score 0 in the final
second, and the next night after the crossing.

### D3. Seeing and transparency become a per-hour atmosphere weight on the usable-sky term

Each hour of the scored window gets an atmosphere quality `a_h`: the mean of
the seeing and transparency values that hour carries, or 1 when it carries
neither. The score becomes:

```
A          = sum(w_h * q_h * a_h) / sum(w_h * q_h)        over the scored window
score01    = cloud_term
           * (ATMOSPHERE_FLOOR + (1 - ATMOSPHERE_FLOOR) * A)
           * (1 - MOON_MAX_PENALTY * moon_penalty)
           * high_cloud_factor
```

`w_h` is the hour's coverage weight and `q_h` its clarity weight, as today.
`ATMOSPHERE_FLOOR` is 0.7, replacing the three weights 0.70, 0.15 and 0.15.
The spec states this formula, so a different implementation cannot satisfy the
spec with different numbers.

`A` differs from today's `optional_term_mean` in one way: an hour with cloud
data but no seeing or transparency stays in the mean, at 1, instead of
dropping out of both numerator and denominator. With that, the cloud and
atmosphere product is `sum(w_h * q_h * (0.7 + 0.3 * a_h)) / sum(w_h)`, a sum
of per-hour terms, each non-negative and increasing in that hour's clarity. So
more cloud in any hour can never raise the score. With today's restricted
denominator, clouding out the one hour that carried poor seeing would lift the
mean and could raise the score, which the spec forbids. The spec pins this
with a ten-hour scenario (97, then 90 when the poor hour is clouded out).

The night in the issue had a cloud term of 0.15 and seeing and transparency
of 0.71 in every hour, with the moon below the horizon and no high-cloud reason,
so both remaining factors were 1. It scores `0.15 × (0.7 + 0.3 × 0.71) = 0.137`,
so 14. With a bright moon up or cirrus present the number would be lower still.

*Why a factor:* the cloud term says how much sky there is; the atmosphere
terms say how good it is. "How much times how good" is the honest combination,
and it is the shape the moon and high-cloud terms already use. The old
weighted mean let the atmosphere terms stand in for sky that was not there.

*Why a floor of 0.7 rather than 0:* the worst 7Timer! seeing and transparency
still leave a usable night for bright targets. A factor of 0 would turn poor
atmosphere into a gate by another name, which ADR-0002 reserves for real
dealbreakers.

*Why 1 for a missing hour, not 0.85:* the project drops an unknown factor and
lets confidence carry the doubt (ADR-0010 for ranking, design D3 of the
conditions verdict for seeing and transparency). A middle value would score an
unknown atmosphere below a known good one and above a known poor one, which is
a guess dressed as a fact. Per hour, 1 is also the only value that keeps the
score monotone in cloud without a second rule.

*Why the high-cloud factor keeps its restricted denominator:* changing it is
out of scope (proposal), and its own design chose not to read a missing cirrus
component as clear sky. So the score is monotone in cloud only when the
high-cloud component is present for every hour or for none. The spec says so,
and issue #112 tracks the gap.

*Alternative, keep the weighted mean but weight the atmosphere terms by the
cloud term:* gives the same ordering with a less readable formula. Rejected.

### D4. Reasons name the span once the scored window is narrowed

The scored window is narrowed when `scored.start > start` (the floored dusk).
An instant in the dusk second is not narrowed, so its reasons keep the
whole-night wording, which is true for it. When narrowed, `evaluate` puts a
span line first in every reason list it returns: "Scored from HH:MM:SS to
HH:MM:SS UTC (the rest of tonight)." The times are whole seconds, so they equal
`scored_window` exactly. That covers the scored path, the overcast and wind
gates, the missing-cloud path, and the empty-window path. The whole-night
wording of the other reasons changes with it:

- "Cloud: N% of the remaining night usable."
- "No usably clear sky in the forecast for the rest of the night."
- "Wind gust over the N km/h limit during the rest of the night."

The atmosphere reasons change on every scored verdict, narrowed or not,
because D3 changes what the factor means. A new line "Atmosphere factor N%."
states the factor as computed. The seeing and transparency lines keep their
means over the hours that carry data, and add their coverage when it is
partial: "Seeing quality 0% (covers 10% of the usable sky)." A reader can then
see why a 0% seeing line sits beside a 97% factor.

*Why on every path, and why reword the gates:* a mid-session `NO-GO` for
overcast is a verdict on the rest of the night, not the whole of it. "Overcast
for the whole dark window" would be false after a clear evening, whatever line
precedes it.

*Why "in the forecast" for the overcast gate:* the gate fires when every hour
with cloud data is overcast. Remaining hours without cloud data are unknown,
not overcast. The wording claims only what the forecast shows. The pre-dusk
reason keeps today's text, which has the same gap; changing it is out of
scope.

*Why change the cloud wording rather than only add a line:* "15% of the dark
window usable" would be false mid-session, because the share is of the
remaining night. The reasons are prose, not a frozen field, so their wording
can change.

### D5. `scored_window` is an additive field with `dark_window`'s shape

`VerdictDocument` gains `scored_window: DarkWindow` after `dark_window`. The
same model class serves both, since the shape and the null rule are identical.
The README's document table describes it, and says that the targets still
judge the whole night, so a target that has set can still be listed beside a
remaining-night verdict (issue #110). No MQTT entity or attribute changes; the
field travels in the document only.

*Why add the field at all:* a score that falls during the night needs a visible
cause. Home Assistant and the narrative explainer can read the span without
parsing a reason string.

### D6. Tests lock the new shape and the goldens are regenerated once

Unit tests in `tests/test_scoring.py` cover the atmosphere factor. The score
never exceeds the cloud term. Better atmosphere never lowers the score.
Missing atmosphere gives a factor of 1. The ten-hour monotonicity case gives
97, then 90. One half-way value rounds to the even integer.

Tests in `tests/test_verdict_eval.py` cover the clamp. A clear-then-overcast
night is `NO-GO` mid-session and not before dusk. A passed gust does not gate.
A passed wind gap does not cap. An instant in the floored dawn second gives
the no-dark-time path, and so does an instant exactly on the crossing. An
instant after the crossing selects the next night. Thirty minutes before dawn
caps a `GO` at `MAYBE`; sixty minutes before dawn does not. A producer test checks `scored_window`
before dusk, mid-session and without a dark window. A new golden case runs the
recorded forecasts at a mid-session instant, so the new field, the span line
and the reworded reasons are locked byte for byte. The existing goldens are
regenerated in one commit, and the diff is reviewed for the expected score
changes only.

## Risks / Trade-offs

- **Every scored verdict changes.** Users see lower scores on partly clear
  nights, and scores that fall through the night. → The proposal, the README
  and the decision record say so. The go-threshold default stays 65.
- **A score that moves during the night can flip a Home Assistant automation.**
  A `GO` at 20:00 can become `MAYBE` at 23:00. → This is the intended honest
  answer. Notification timing stays in the user's automation, which can act
  on the first verdict of the night if it prefers.
- **Targets and the verdict judge different spans mid-session.** A target that
  has set can still lead the list under a verdict for the rest of the night.
  → Issue #110 tracks it. The target `window` fields still state the truth for
  the whole night.
- **Partly missing cirrus data can still break monotonicity.** The high-cloud
  factor keeps its restricted denominator, so clouding out the one hour that
  carried cirrus can lift the factor. → Unchanged from today, stated as a
  limit in the spec, and tracked as issue #112.
- **A sub-second gap at dawn.** The dark window is floored to whole seconds,
  and the instant may carry microseconds, so the selected night can end a
  fraction of a second before the instant. → D1's outer `min` folds that case
  into the empty-window path, and a test with a microsecond instant pins it.
