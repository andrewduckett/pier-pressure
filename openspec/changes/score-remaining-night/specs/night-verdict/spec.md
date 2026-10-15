## ADDED Requirements

### Requirement: The verdict judges the remaining night

The verdict SHALL judge the **scored window**: the part of the dark window from the evaluation instant to astronomical dawn. Before astronomical dusk, the scored window SHALL equal the dark window. Once the night has started, the scored window SHALL start at the evaluation instant, so hours that have passed no longer count. The hard gates that read conditions (overcast, wind), the score, and the completeness part of confidence SHALL all run over the scored window. The `dark_window` field SHALL keep the whole night and SHALL NOT change meaning.

The document SHALL carry a `scored_window` object with a `start` and an `end`, in the same shape as `dark_window`. Both SHALL be null when there is no dark window. Otherwise `scored_window.end` SHALL equal `dark_window.end`, and `scored_window.start` SHALL be the later of `dark_window.start` and the evaluation instant.

When the evaluation instant falls on astronomical dawn, the scored window SHALL be empty. The verdict SHALL then treat the night as having no usable time left: it SHALL NOT fail the overcast gate, SHALL NOT be `GO`, SHALL be `MAYBE` with a `score` of 0, and SHALL carry a reason that no dark time remains. It SHALL NOT report that conditions are unavailable.

#### Scenario: Before dusk, the scored window is the whole night

- **WHEN** a verdict is produced at an evaluation instant before astronomical dusk
- **THEN** `scored_window.start` equals `dark_window.start`
- **AND** `scored_window.end` equals `dark_window.end`

#### Scenario: Mid-session, the scored window starts now

- **WHEN** a verdict is produced at an evaluation instant inside the dark window
- **THEN** `scored_window.start` equals the evaluation instant
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

#### Scenario: A verdict at dawn has no usable time left

- **WHEN** a verdict is produced at an evaluation instant equal to astronomical dawn, with cloud data available
- **THEN** the `verdict` is `MAYBE`
- **AND** the `score` is 0
- **AND** a reason states that no dark time remains
- **AND** no reason states that conditions are unavailable

### Requirement: Reasons name the scored span

Once the night has started, the reasons SHALL say which span the verdict judged. The cloud reason SHALL state the usable share of the remaining night, and a reason SHALL state the scored span's start and end. Before dusk, the cloud reason SHALL state the usable share of the dark window, as it does today, and no span reason is needed.

#### Scenario: A mid-session verdict names the span it judged

- **WHEN** a scored verdict is produced at an evaluation instant inside the dark window
- **THEN** a reason states the usable share of the remaining night
- **AND** a reason states the start and end of the scored window

#### Scenario: A verdict before dusk keeps the whole-night wording

- **WHEN** a scored verdict is produced at an evaluation instant before astronomical dusk
- **THEN** the cloud reason states the usable share of the dark window
- **AND** no reason states a scored span

## MODIFIED Requirements

### Requirement: Hard gates decide a NO-GO

The verdict SHALL be `NO-GO` when any hard gate fails, and a failed gate SHALL be the only cause of a `NO-GO`. The hard gates are: the selected night has no dark window; cloud data is available for the scored window and that window is overcast for its entire covered length (no part with cloud data is usably clear); and — only when a wind-gust limit is configured for the pier — the forecast gust exceeds that limit at any hour of the scored window. The overcast gate SHALL require cloud data to be available: when cloud data is entirely absent, the overcast gate SHALL NOT fire (that case is the missing-data path, not a NO-GO). The overcast gate SHALL NOT fire on an empty scored window (the evaluation instant at dawn); that case is the no-dark-time-left path. When a gate fails, the `score` SHALL be null and the reasons SHALL name the failing gate.

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

When every hard gate passes, the system SHALL compute an integer score from 0 to 100 from the observing conditions across the scored window. The score SHALL be the usable-sky term (the share of the scored window that is usably clear, the dominant term) multiplied by an atmosphere factor, a moon factor, and a high-cloud factor. The atmosphere factor SHALL combine seeing and transparency, each weighted toward the usably clear hours, and SHALL range from a fixed floor for the worst atmosphere to 1 for the best, so good seeing and transparency SHALL never lift a night above its usable-sky term. When seeing and transparency are both unavailable, the atmosphere factor SHALL be 1 and the missing data SHALL lower confidence instead. The moon factor SHALL weight the moon's brightness by how much of the usably clear scored window it is above the horizon. The product SHALL be rounded to the nearest integer, so the same inputs yield the same integer score deterministically. The verdict SHALL be `GO` when the score is at or above the pier's go-threshold **and cloud data for the scored window is available**, and `MAYBE` otherwise. Requiring cloud data for a `GO` — not merely a high score — SHALL hold even when the go-threshold is 0, so a `GO` is never issued without evidence the sky is clear. A brighter or more clouded night SHALL not score higher than an otherwise identical darker or clearer one.

#### Scenario: A score at or above the go-threshold with cloud data is GO

- **WHEN** every gate passes, cloud data is available, and the computed score is at or above the pier's go-threshold
- **THEN** the `verdict` is `GO`

#### Scenario: A score below the go-threshold is MAYBE

- **WHEN** every gate passes and the computed score is below the pier's go-threshold
- **THEN** the `verdict` is `MAYBE`

#### Scenario: A bright moon up during darkness lowers the score

- **WHEN** two otherwise identical nights differ only in that the moon is bright and above the horizon during the scored window in one and absent in the other
- **THEN** the night with the bright moon up during darkness has the lower score

#### Scenario: Good seeing and transparency cannot lift a mostly cloudy night

- **WHEN** every gate passes and only a small share of the scored window is usably clear, however good the seeing and transparency are in that share
- **THEN** the score is at most the usable-sky share expressed as a percentage

#### Scenario: Better seeing and transparency raise the score of a clear night

- **WHEN** two nights are identical in cloud and moon, and one has better seeing and transparency in its usably clear hours
- **THEN** the night with the better seeing and transparency has the higher score

#### Scenario: Missing seeing and transparency leave the score at the usable-sky term

- **WHEN** two nights are identical in cloud and moon, and one has no seeing or transparency data at all
- **THEN** the night without seeing and transparency scores the same as the usable-sky term alone, cut only by the moon and high-cloud factors
- **AND** its confidence is lower

### Requirement: Conditions are evaluated across the whole dark window

The verdict SHALL judge the night by how much usable dark time the scored window offers, not by a single hour or a flat average. A scored window with some usably clear hours SHALL NOT be gated as overcast, and its score SHALL reflect the extent and quality of the usable portion. Terms other than cloud SHALL be weighted toward the hours that are usably clear, so a term's value during a clouded-out hour does not distort the verdict. The measure of usable dark time SHALL be normalized to the actual duration of the scored window, so a window whose start and end do not fall on whole-hour boundaries still yields a score within 0 to 100. Hours of the scored window for which cloud data is unavailable SHALL count as neither clear nor overcast: they SHALL NOT trigger the overcast gate and SHALL NOT add usable dark time to the score, so partial cloud coverage lowers the score rather than inflating it or gating the night.

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
- **AND** the score reflects the usable clear portion

#### Scenario: More usable clear darkness scores higher

- **WHEN** two nights are identical except that one has more of its scored window usably clear
- **THEN** the night with more usable clear darkness has the higher score
