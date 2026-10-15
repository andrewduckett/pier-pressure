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
computes `scored = (min(max(now, start), end), end)` from the dark window. The
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

*Why the outer `min`:* `dark_window` picks the first dawn at or after the
instant using the exact crossing, then floors both bounds to a whole second.
An instant inside the last partial second of the night, such as 03:25:52.400
with the crossing at 03:25:52.700, selects a night whose floored `end` is
03:25:52, which equals `now`. Without the `min`, a later raw instant could
start after the end and tile no slots, which reads as "no cloud data". The
`min` folds that case into the empty-window path (D2). An instant at or after
the exact crossing selects the next night, so the empty window is confined to
that one partial second. A test pins it with an instant that carries
microseconds.

*Why clamp inside `evaluate` and not in `dark_window`:* the `dark_window` field
is a frozen contract, and the moon and the targets still need the whole night.
One clamp at the one place that decides the verdict keeps every other reader
unchanged.

*Alternative, a separate "session window" concept with its own module:*
rejected. The clamp is two lines, and the rules already take a window.

### D2. An empty scored window is its own path, before the cloud rules

When `scored` starts and ends at the same instant, `evaluate` returns `MAYBE`,
score 0, with a reason that no dark time remains, before it reads any cloud
data. This can only happen when `now` equals `dark_window.end` (D1).
Confidence comes from the usual lead time and freshness, with completeness at
0 because the window covers no hour. This path sits after the no-dark-window
gate and before the wind gate.

*Why not let it fall through:* an empty window has no slots. The cloud
availability check would then read "no cloud data", and the verdict would say
"conditions unavailable", which is false. The overcast gate cannot fire either,
because it needs cloud data present.

*Why `MAYBE` and not `NO-GO`:* a failed gate is the only cause of a `NO-GO`,
and "the night is over" is not a condition gate. The next refresh, a second
later, selects the next night.

### D3. Seeing and transparency become one atmosphere factor on the usable-sky term

The score becomes:

```
atmosphere = mean of the present terms among seeing and transparency
score01    = cloud_term
           * (ATMOSPHERE_FLOOR + (1 - ATMOSPHERE_FLOOR) * atmosphere)
           * (1 - MOON_MAX_PENALTY * moon_penalty)
           * high_cloud_factor
```

`ATMOSPHERE_FLOOR` is 0.7, replacing the three weights 0.70, 0.15 and 0.15.
When neither term is present, the factor is 1 and the completeness factor
already trims confidence. The spec states this formula, so a different
implementation cannot satisfy the spec with different numbers.

The night in the issue had a cloud term of 0.15 and seeing and transparency
of 0.71, with the moon below the horizon and no high-cloud reason, so both
remaining factors were 1. It scores `0.15 × (0.7 + 0.3 × 0.71) = 0.137`, so 14.
With a bright moon up or cirrus present the number would be lower still.

*Why a factor:* the cloud term says how much sky there is; the atmosphere
terms say how good it is. "How much times how good" is the honest combination,
and it is the shape the moon and high-cloud terms already use. The old
weighted mean let the atmosphere terms stand in for sky that was not there.

*Why a floor of 0.7 rather than 0:* the worst 7Timer! seeing and transparency
still leave a usable night for bright targets. A factor of 0 would turn poor
atmosphere into a gate by another name, which ADR-0002 reserves for real
dealbreakers.

*Why 1 for missing data, not 0.85:* the project drops an unknown factor and
lets confidence carry the doubt (ADR-0010 for ranking, design D3 of the
conditions verdict for seeing and transparency). Inventing a middle value
would score an unknown atmosphere below a known good one and above a known
poor one, which is a guess dressed as a fact.

*Alternative, keep the weighted mean but weight the atmosphere terms by the
cloud term:* gives the same ordering with a less readable formula. Rejected.

### D4. Reasons name the span once the night has started

Once `scored` starts after dusk, `evaluate` puts a span line first in every
reason list it returns: "Scored from HH:MM to HH:MM UTC (the rest of tonight)."
That covers the scored path, the overcast and wind gates, the missing-cloud
path, and the empty-window path. On the scored path the cloud reason reads
"Cloud: N% of the remaining night usable." instead of "of the dark window".
Before dusk the reasons keep today's wording and no span line is added. The
times use the same UTC formatting as the document's timestamps.

*Why on every path:* a mid-session `NO-GO` for overcast is a verdict on the
rest of the night, not the whole of it. Without the span line, "Overcast for
the whole dark window" would read as a claim about hours that were clear.

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

Unit tests in `tests/test_scoring.py` cover the atmosphere factor: the score
never exceeds the cloud term, better atmosphere scores higher, and missing
atmosphere gives a factor of 1. Tests in `tests/test_verdict_eval.py` cover
the clamp: a clear-then-overcast night is `NO-GO` mid-session and not before
dusk, a passed gust does not gate, a passed wind gap does not cap, an instant
in the floored dawn second gives the no-dark-time path, and an instant at the
exact crossing selects the next night. A rounding test pins one half-way
value to the even integer. A producer test checks `scored_window`
before dusk, mid-session and without a dark window. The goldens are regenerated
in one commit, and the diff is reviewed for the expected score changes only.

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
- **A sub-second gap at dawn.** The dark window is floored to whole seconds,
  and the instant may carry microseconds, so the selected night can end a
  fraction of a second before the instant. → D1's outer `min` folds that case
  into the empty-window path, and a test with a microsecond instant pins it.
