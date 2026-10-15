## ADDED Requirements

### Requirement: The verdict judges the remaining night

The verdict SHALL judge the **scored window**: the part of the dark window from the evaluation instant to astronomical dawn.

- The **scoring instant** is the evaluation instant with its sub-second part removed, the same whole second as `generated_at`.
- Before astronomical dusk, the scored window SHALL equal the dark window.
- Once the night has started, the scored window SHALL start at the scoring instant, so hours that have passed no longer count.
- The scored window's start SHALL never be later than its end. When the scoring instant equals `dark_window.end`, the scored window is empty.

These rules SHALL all run over the scored window:

- the overcast gate and the wind gate;
- the wind-coverage check and the cloud-availability check;
- the score and each of its terms;
- the completeness part of confidence.

The `dark_window` field SHALL keep the whole night and SHALL NOT change meaning.

The document SHALL carry a `scored_window` object with a `start` and an `end`, in the same shape as `dark_window`.

- Both SHALL be null when there is no dark window.
- `scored_window.end` SHALL equal `dark_window.end`.
- `scored_window.start` SHALL be the later of `dark_window.start` and `generated_at`, and never later than `scored_window.end`.

`generated_at` is the scoring instant, so the emitted span is the span the verdict judged.

An empty scored window can only arise in the last partial second of the night. Three facts combine:

- `dark_window.end` is the exact dawn crossing, floored to a whole second.
- The selected night is the one whose exact dawn is at or after the evaluation instant.
- The scoring instant is the evaluation instant floored to a whole second.

So the scoring instant equals `dark_window.end` only when the evaluation instant lies in that floored second, up to and including the exact crossing. An instant after the crossing selects the next night.

When the scored window is empty, the verdict SHALL be `MAYBE` with a `score` of 0 and a reason that no dark time remains. It SHALL NOT fail the overcast gate, SHALL NOT be `GO`, and SHALL NOT report that conditions are unavailable.

A short remaining span is not worth setting up for, however clear it is. When the scored window is narrowed and shorter than 60 minutes, the verdict SHALL NOT be `GO`. The gates and the score still run as usual. A verdict that would otherwise be `GO` SHALL be `MAYBE`, with a reason that less than an hour of dark time remains. A whole night shorter than 60 minutes is not narrowed and is not capped by this rule.

#### Scenario: Before dusk, the scored window is the whole night

- **WHEN** a verdict is produced at an evaluation instant before astronomical dusk
- **THEN** `scored_window.start` equals `dark_window.start`
- **AND** `scored_window.end` equals `dark_window.end`

#### Scenario: Mid-session, the scored window starts at the generation second

- **WHEN** a verdict is produced at an evaluation instant inside the dark window, with a fractional second
- **THEN** `scored_window.start` equals `generated_at`
- **AND** `scored_window.end` equals `dark_window.end`

#### Scenario: Clear hours that have passed no longer lift the score

- **WHEN** the dark window is clear for its first hours and overcast for the rest, and a verdict is produced after the clear hours have passed
- **THEN** the overcast gate fails and the `verdict` is `NO-GO`
- **AND** a verdict produced before dusk for the same night is not `NO-GO`

#### Scenario: A gust that has already passed does not gate the night

- **WHEN** a pier has a configured wind-gust limit, the forecast exceeds it only in an hour that has passed, and a verdict is produced after that hour
- **THEN** the `verdict` is not `NO-GO`

#### Scenario: Missing wind data in a passed hour does not cap the verdict

- **WHEN** a pier has a configured wind-gust limit, wind data is absent only for an hour that has passed, and every remaining hour has wind data under the limit
- **THEN** the `verdict` is not capped at `MAYBE` on account of wind data

#### Scenario: The scored window is null without a dark window

- **WHEN** a verdict is produced for a selected night that has no dark window
- **THEN** `scored_window.start` and `scored_window.end` are both null

#### Scenario: A verdict in the last partial second of the night has no usable time left

- **WHEN** a verdict is produced at an evaluation instant in the whole second that `dark_window.end` names, up to and including the exact dawn crossing, with cloud data available
- **THEN** `scored_window.start` equals `scored_window.end`
- **AND** the `verdict` is `MAYBE`
- **AND** the `score` is 0
- **AND** a reason states that no dark time remains
- **AND** no reason states that conditions are unavailable

#### Scenario: Less than an hour left caps the verdict at MAYBE

- **WHEN** a verdict is produced at an evaluation instant 30 minutes before `dark_window.end`, the remaining sky is clear, and the score is at or above the go-threshold
- **THEN** the `verdict` is `MAYBE`
- **AND** the `score` is the computed score, not 0
- **AND** a reason states that less than an hour of dark time remains

#### Scenario: An hour or more left can still be GO

- **WHEN** a verdict is produced at an evaluation instant 60 minutes before `dark_window.end`, the remaining sky is clear, and the score is at or above the go-threshold
- **THEN** the `verdict` is `GO`

#### Scenario: A verdict after the exact dawn crossing judges the next night

- **WHEN** a verdict is produced at an evaluation instant after the exact astronomical dawn crossing
- **THEN** `dark_window` is the next night's window
- **AND** `scored_window` equals `dark_window`

### Requirement: Reasons name the scored span

The scored window is **narrowed** when `scored_window.start` is later than `dark_window.start`. That is the test for every rule in this requirement. An evaluation instant in the same whole second as dusk is not narrowed: its scored window is the whole night, so the whole-night wording is true.

When the scored window is narrowed, every verdict with a dark window SHALL carry, as its first reason, a line that states the scored window's start and end to the second, in UTC. This holds for a scored verdict, a gated `NO-GO`, a missing-cloud `MAYBE`, and an empty scored window.

When the scored window is narrowed, no reason SHALL make a claim about the whole night, and no reason SHALL claim more than the forecast covers. On a scored verdict, the cloud reason SHALL state the usable share of the remaining night. A failed overcast gate SHALL say that the forecast shows no usably clear sky for the rest of the night. A failed wind gate SHALL say the gust falls in the rest of the night.

When the scored window is not narrowed, no span line is present, and the reasons keep their whole-night wording.

#### Scenario: A mid-session scored verdict names the span it judged

- **WHEN** a scored verdict is produced at an evaluation instant at least one second after `dark_window.start` and inside the dark window
- **THEN** the first reason states the start and end of the scored window, each equal to the second to `scored_window.start` and `scored_window.end`
- **AND** a reason states the usable share of the remaining night

#### Scenario: A mid-session gated verdict names the span it judged

- **WHEN** a `NO-GO` verdict is produced at an evaluation instant at least one second after `dark_window.start` and inside the dark window, because the overcast gate or the wind gate failed
- **THEN** the first reason states the start and end of the scored window
- **AND** a later reason names the failing gate and refers to the rest of the night, not the whole dark window
- **AND** when the gate is overcast and some remaining hours lack cloud data, the reason claims no more than that the forecast shows no usably clear sky

#### Scenario: A mid-session missing-cloud verdict names the span it judged

- **WHEN** a verdict is produced at an evaluation instant at least one second after `dark_window.start` and inside the dark window, with no cloud data for the scored window
- **THEN** the first reason states the start and end of the scored window
- **AND** a later reason states that conditions are unavailable

#### Scenario: A verdict before dusk keeps the whole-night wording

- **WHEN** a scored verdict is produced at an evaluation instant before astronomical dusk
- **THEN** the cloud reason states the usable share of the dark window
- **AND** no reason states a scored span

#### Scenario: A verdict in the dusk second keeps the whole-night wording

- **WHEN** a scored verdict is produced at an evaluation instant in the same whole second as `dark_window.start`
- **THEN** `scored_window.start` equals `dark_window.start`
- **AND** no reason states a scored span

## RENAMED Requirements

- FROM: `### Requirement: Conditions are evaluated across the whole dark window`
- TO: `### Requirement: Conditions are evaluated across the whole scored window`

## MODIFIED Requirements

### Requirement: Hard gates decide a NO-GO

The verdict SHALL be `NO-GO` when any hard gate fails, and a failed gate SHALL be the only cause of a `NO-GO`. The hard gates are:

- the selected night has no dark window;
- cloud data is available for the scored window, and every part of that window with cloud data is overcast (no part is usably clear);
- only when a wind-gust limit is configured for the pier: the forecast gust exceeds that limit at any hour of the scored window.

The overcast gate SHALL require cloud data to be available. When cloud data is entirely absent, the overcast gate SHALL NOT fire; that case is the missing-data path, not a NO-GO. The overcast gate SHALL NOT fire on an empty scored window; that case is the no-dark-time-left path. When a gate fails, the `score` SHALL be null and the reasons SHALL name the failing gate.

#### Scenario: No dark window gates to NO-GO

- **WHEN** a verdict is produced for a selected night that has no dark window
- **THEN** the `verdict` is `NO-GO`
- **AND** the `score` is null

#### Scenario: An all-night overcast dark window gates to NO-GO

- **WHEN** every hour of the scored window is overcast, with no usably clear portion
- **THEN** the `verdict` is `NO-GO`
- **AND** the `score` is null

#### Scenario: Configured wind-gust limit gates to NO-GO

- **WHEN** a pier has a configured wind-gust limit and the forecast gust exceeds it at any hour of the scored window
- **THEN** the `verdict` is `NO-GO`
- **AND** the `score` is null

#### Scenario: An unusable night is never NO-GO without a failed gate

- **WHEN** every hard gate passes
- **THEN** the `verdict` is not `NO-GO`
- **AND** the `score` is a non-null integer between 0 and 100

### Requirement: A banded score decides GO versus MAYBE

When every hard gate passes, the system SHALL compute an integer score from 0 to 100 from the observing conditions across the scored window.

The score SHALL be the product of four factors, each from 0 to 1, scaled to 100 and rounded to the nearest integer. A value exactly half-way between two integers SHALL round to the even one, so 12.5 gives 12 and 13.5 gives 14. The factors are:

- the **usable-sky term**: the share of the scored window that is usably clear. This is the dominant term;
- the **atmosphere factor**: `0.7 + 0.3 × A`. Each hour has an atmosphere quality `a`. It is the mean of the seeing and transparency values that hour carries. An hour that carries neither has `a` of 1. `A` is the mean of `a` over the scored window, weighted by each hour's usably clear share. When no hour carries seeing or transparency, the factor is 1. The missing data SHALL lower confidence instead;
- the **moon factor**: the moon's brightness weighted by how much of the usably clear scored window it is above the horizon, as today;
- the **high-cloud factor**, as today.

Because every factor is at most 1, the score SHALL never exceed the usable-sky term scaled to 100 and rounded. Good seeing and transparency refine a clear night; they cannot lift a cloudy one. The same inputs SHALL yield the same integer score.

The verdict SHALL be `GO` when the score is at or above the pier's go-threshold, **cloud data for the scored window is available**, and no cap applies. It SHALL be `MAYBE` otherwise. Two caps exist: wind data that does not cover the scored window when a wind limit is configured, and a narrowed scored window shorter than 60 minutes. Requiring cloud data for a `GO` SHALL hold even when the go-threshold is 0, so a `GO` is never issued without evidence the sky is clear.

A brighter night SHALL NOT score higher than an otherwise identical darker one. More cloud SHALL NOT raise the product of the usable-sky term and the atmosphere factor, for any pattern of missing seeing and transparency, because an hour without data counts as 1. The moon and high-cloud factors keep today's rules. Each is a ratio over the usably clear hours, so clouding out the one hour that carried the moon or the cirrus can still raise the score. The spec does not promise monotonicity in cloud through those two factors. Issue #112 covers that gap.

The reasons SHALL explain the atmosphere factor as computed. A scored verdict SHALL carry a reason that states the atmosphere factor as a percentage. Each seeing or transparency reason SHALL state the share of the usable sky its data covers, when that share is below 100%.

#### Scenario: A score at or above the go-threshold with cloud data is GO

- **WHEN** every gate passes, cloud data is available, no cap applies, and the computed score is at or above the pier's go-threshold
- **THEN** the `verdict` is `GO`

#### Scenario: A score below the go-threshold is MAYBE

- **WHEN** every gate passes and the computed score is below the pier's go-threshold
- **THEN** the `verdict` is `MAYBE`

#### Scenario: A bright moon up during darkness lowers the score

- **WHEN** two otherwise identical nights differ only in that the moon is bright and above the horizon during the scored window in one and absent in the other
- **THEN** the night with the bright moon up during darkness has the lower score

#### Scenario: Good seeing and transparency cannot lift a mostly cloudy night

- **WHEN** every gate passes, the usable-sky term is 0.15, seeing and transparency are both 0.71 in the usably clear hours, the moon is below the horizon throughout, and no high-cloud component is available
- **THEN** the `score` is 14

#### Scenario: Better seeing and transparency never lower the score

- **WHEN** two nights are identical in cloud, high cloud and moon, and one has better seeing and transparency in its usably clear hours
- **THEN** the night with the better seeing and transparency has a score no lower than the other
- **AND** when the usable-sky term is 1, the moon is down, no high cloud is present, and seeing and transparency move from 0 to 1, the `score` moves from 70 to 100

#### Scenario: The reasons explain an atmosphere factor built on partial data

- **WHEN** a scored window has nine clear hours with no seeing or transparency and one clear hour with both at 0
- **THEN** a reason states an atmosphere factor of 97%
- **AND** the seeing and transparency reasons each state a quality of 0% covering 10% of the usable sky

#### Scenario: Clouding out a poor-atmosphere hour never raises the score

- **WHEN** a scored window has ten clear hours, eight with no seeing or transparency, one with both at 1, and one with both at 0, the moon is down throughout, and no high-cloud component is present
- **THEN** the `score` is 97
- **AND** when the hour with both at 0 is made overcast instead, the `score` is 90

#### Scenario: Missing seeing and transparency leave the score at the usable-sky term

- **WHEN** two nights are identical in cloud, high cloud and moon, and one has no seeing or transparency data at all
- **THEN** the night without seeing and transparency scores the usable-sky term cut only by the moon and high-cloud factors, scaled to 100 and rounded
- **AND** its confidence is lower

### Requirement: Conditions are evaluated across the whole scored window

The verdict SHALL judge the night by how much usable dark time the scored window offers, not by a single hour or a flat average.

- A scored window with some usably clear hours SHALL NOT be gated as overcast. Its score SHALL reflect the extent and quality of the usable portion.
- Terms other than cloud SHALL be weighted toward the hours that are usably clear, so a term's value during a clouded-out hour does not distort the verdict.
- The measure of usable dark time SHALL be normalized to the actual duration of the scored window. A window whose start and end do not fall on whole-hour boundaries still yields a score within 0 to 100.
- Hours of the scored window for which cloud data is unavailable SHALL count as neither clear nor overcast. They SHALL NOT trigger the overcast gate and SHALL NOT add usable dark time to the score, so partial cloud coverage lowers the score rather than inflating it or gating the night.

#### Scenario: Hours without cloud data lower the score without gating

- **WHEN** two nights are identical and clear wherever cloud data exists, but one has cloud data covering the whole scored window and the other only covering half of it
- **THEN** neither night fails the overcast gate
- **AND** the night with cloud data for only half the window has the lower score

#### Scenario: A window that does not align to whole hours still yields a bounded score

- **WHEN** a verdict is produced for a scored window whose start and end do not fall on whole-hour boundaries
- **THEN** the `score` is an integer between 0 and 100 inclusive

#### Scenario: A partly clear night is not gated as overcast

- **WHEN** part of the scored window is usably clear and the rest is overcast
- **THEN** the overcast gate does not fail
- **AND** the `score` is above 0
- **AND** the `score` is at most the usably clear share of the scored window, scaled to 100 and rounded

#### Scenario: More usable clear darkness scores higher

- **WHEN** two nights are identical except that one has more of its scored window usably clear, by enough to change the rounded score
- **THEN** the night with more usable clear darkness has the higher score

### Requirement: The verdict degrades honestly when conditions are unavailable

When conditions data is missing, the verdict SHALL degrade rather than fail or mislead. A verdict SHALL always be produced. The rules, in the order they apply:

- **Missing optional data.** Missing seeing or transparency SHALL drop only its own contribution and lower confidence.
- **Gates first.** The hard gates SHALL be evaluated before the missing-cloud rule applies. A failed hard gate that does not depend on cloud data (no dark window, or a configured wind gust over its limit) SHALL still yield `NO-GO` even when cloud data is missing, so a safety-critical gate is never overridden by a missing observation.
- **Empty scored window.** The missing-cloud rule SHALL NOT apply to an empty scored window; that case is the no-dark-time-left path.
- **Wind limit set but wind not fully covered.** When a wind-gust limit is configured but wind data does not cover every hour of the scored window, the limit cannot be confirmed, so it SHALL be treated as unavailable. This holds whether wind data is absent for the whole scored window or only for some of its hours. When the limit is treated as unavailable this way, and no hour with wind data has already failed the gate, the verdict SHALL NOT be `GO` and SHALL be capped at `MAYBE`, with a reason that wind data is unavailable and lowered confidence.
- **Cloud entirely missing.** Only when every hard gate passes does the missing-cloud rule apply. When cloud data for the scored window is entirely unavailable, the verdict SHALL NOT be `GO` (there is no evidence the sky is clear) and SHALL NOT be `NO-GO` on account of the missing data itself (absence of data is not a dealbreaker). It SHALL be `MAYBE` with a `score` of 0, a `confidence.value` of 0 in the `LOW` band, and a reason stating that conditions are unavailable.

#### Scenario: Missing cloud data caps the verdict at MAYBE when gates pass

- **WHEN** a verdict is produced for a pier with a dark window, every hard gate passes, and there is no available cloud data
- **THEN** the `verdict` is `MAYBE`
- **AND** the `verdict` is neither `GO` nor `NO-GO`
- **AND** the `score` is 0
- **AND** the `confidence.value` is 0
- **AND** the `confidence.band` is `LOW`
- **AND** a reason states that conditions are unavailable

#### Scenario: A failed wind gate yields NO-GO even when cloud data is missing

- **WHEN** cloud data is unavailable but wind-gust data is available and exceeds the pier's configured wind-gust limit during the scored window
- **THEN** the `verdict` is `NO-GO`
- **AND** the `score` is null

#### Scenario: Missing wind data caps the verdict at MAYBE when a limit is configured

- **WHEN** a pier has a configured wind-gust limit, every gate that can be evaluated passes, and wind-gust data is unavailable for the scored window
- **THEN** the `verdict` is not `GO`
- **AND** the `verdict` is `MAYBE`
- **AND** a reason states that wind data is unavailable

#### Scenario: Partial wind coverage caps the verdict at MAYBE when a limit is configured

- **WHEN** a pier has a configured wind-gust limit, no hour with wind data exceeds it, but at least one hour of the scored window has no wind data
- **THEN** the `verdict` is not `GO`
- **AND** the `verdict` is `MAYBE`
- **AND** a reason states that wind data is unavailable

#### Scenario: A verdict is always produced despite missing conditions

- **WHEN** conditions cannot be obtained at all for a pier with a dark window
- **THEN** a verdict document is still produced

### Requirement: High, thin cloud is a distinct score penalty

When every hard gate passes and cloud data is available, the banded score SHALL
apply a penalty for high-layer (thin cirrus) cloud across the scored window that is
distinct from the total-cloud term of the score. High cirrus can leave a low
total cloud reading yet wreck transparency for deep-sky work, so the night is
scored honestly rather than as clear. The high-cloud penalty SHALL be reported as
its own itemized `reasons[]` line, separate from the total-cloud reason, so the
explanation names it as a distinct term. Holding every other input fixed —
including the total cloud cover — more high-layer cloud usably up during the scored
window SHALL NOT raise the score: it lowers it or leaves it unchanged.

The high-cloud penalty SHALL only shape the banded score; it SHALL NOT introduce
a new hard gate and SHALL NOT on its own cause a `NO-GO`. It SHALL be weighted
toward the usably clear hours in the same way as the other non-cloud terms, so a
high-cirrus reading during a clouded-out hour does not distort the verdict. When
the high-layer cloud component is unavailable for the scored window, the high-cloud
term SHALL drop its own contribution — no penalty and no reason line — rather than
fail or guess, exactly as the other optional terms degrade when their data is
missing. This term is additive: it does not change the meaning of the existing
total-cloud term, the gates, the bands, or the confidence.

#### Scenario: High cirrus lowers the score with its own reason

- **WHEN** two nights are identical, each with cloud data available and every hard gate passing, except that one has high, thin cloud usably up during the scored window and the other has none
- **THEN** the night with the high cirrus has the lower score
- **AND** its `reasons` list carries a high/thin-cloud line distinct from the total-cloud line

#### Scenario: The high-cloud penalty never gates the night

- **WHEN** a night has high, thin cloud during the scored window while every hard gate passes
- **THEN** the `verdict` is not `NO-GO` on account of the high cloud
- **AND** the `score` is a non-null integer between 0 and 100 inclusive

#### Scenario: Missing high-cloud component drops the term without penalty

- **WHEN** two nights are identical and every hard gate passes, except that one has its high-layer cloud component available and clear and the other has that component unavailable while total cloud cover is available
- **THEN** neither night is penalized for high cloud
- **AND** neither `reasons` list carries a high/thin-cloud line
