## MODIFIED Requirements

### Requirement: Confidence is present and banded

The `confidence` field SHALL always be present and SHALL contain a `band` that is exactly one of `LOW`, `MEDIUM`, or `HIGH`, and a `value` that is an integer from 0 to 100 inclusive. Confidence expresses how much to trust the verdict given how far ahead the forecast reaches and how complete the underlying data is. Confidence SHALL rise as the evaluation instant approaches the dark window and SHALL fall when the forecast is stale or when conditions data is missing. Confidence is orthogonal to the score: a low-confidence GO and a high-confidence NO-GO are both permitted. When the verdict is a `NO-GO` because there is no dark window, no forecast is involved and the confidence SHALL be `HIGH` with a value of 100, because it rests on deterministic offline astronomy rather than on a forecast.

#### Scenario: Confidence carries a band and a bounded value

- **WHEN** a verdict is produced for a valid pier configuration
- **THEN** the `confidence.band` field equals `LOW`, `MEDIUM`, or `HIGH`
- **AND** the `confidence.value` field is an integer between 0 and 100 inclusive

#### Scenario: Astronomy-only NO-GO is fully confident

- **WHEN** the verdict is `NO-GO` because the selected night has no dark window
- **THEN** the `confidence.band` is `HIGH`
- **AND** the `confidence.value` is 100

#### Scenario: Confidence rises as the dark window nears

- **WHEN** two verdicts are produced for the same pier, one long before the dark window begins and one shortly before it begins, each using a forecast freshly issued at its evaluation instant so freshness and data completeness are equal for both
- **THEN** the confidence produced shortly before the dark window is at least as high as the confidence produced long before it

#### Scenario: Missing optional data lowers confidence

- **WHEN** a verdict is produced from conditions in which optional fields (seeing or transparency) are unavailable
- **THEN** the confidence is lower than it would be for the same conditions with those fields available
- **AND** the missing optional data does not fail a gate and does not null the score

### Requirement: Reasons explain the verdict

The `reasons` field SHALL be a non-empty list of human-readable strings that itemize the terms behind the verdict, so the explanation follows from the decision itself. When the verdict is a gated NO-GO, the reasons SHALL name the failing gate. When gates pass, the reasons SHALL itemize the terms that shaped the score.

#### Scenario: Every verdict carries at least one reason

- **WHEN** a verdict is produced for a valid pier configuration
- **THEN** the `reasons` list contains at least one non-empty human-readable string

#### Scenario: A gated no-go names the failing gate

- **WHEN** a verdict is `NO-GO` because a hard gate failed
- **THEN** the `reasons` list names the gate that failed

## ADDED Requirements

### Requirement: Hard gates decide a NO-GO

The verdict SHALL be `NO-GO` when any hard gate fails, and a failed gate SHALL be the only cause of a `NO-GO`. The hard gates are: the selected night has no dark window; cloud data is available for the dark window and that window is overcast for its entire covered length (no part with cloud data is usably clear); and — only when a wind-gust limit is configured for the pier — the forecast gust exceeds that limit at any hour of the dark window. The overcast gate SHALL require cloud data to be available: when cloud data is entirely absent, the overcast gate SHALL NOT fire (that case is the missing-data path, not a NO-GO). When a gate fails, the `score` SHALL be null and the reasons SHALL name the failing gate.

#### Scenario: No dark window gates to NO-GO

- **WHEN** a verdict is produced for a selected night that has no dark window
- **THEN** the `verdict` is `NO-GO`
- **AND** the `score` is null

#### Scenario: An all-night overcast dark window gates to NO-GO

- **WHEN** every hour of the dark window is overcast, with no usably clear portion
- **THEN** the `verdict` is `NO-GO`
- **AND** the `score` is null

#### Scenario: Configured wind-gust limit gates to NO-GO

- **WHEN** a pier has a configured wind-gust limit and the forecast gust exceeds it at any hour of the dark window
- **THEN** the `verdict` is `NO-GO`
- **AND** the `score` is null

#### Scenario: An unusable night is never NO-GO without a failed gate

- **WHEN** every hard gate passes
- **THEN** the `verdict` is not `NO-GO`
- **AND** the `score` is a non-null integer between 0 and 100

### Requirement: A banded score decides GO versus MAYBE

When every hard gate passes, the system SHALL compute an integer score from 0 to 100 that combines the observing conditions across the dark window — cloud (the dominant term), the moon's brightness weighted by how much of the dark window it is above the horizon, transparency, and seeing. The weighted combination SHALL be rounded to the nearest integer, so the same inputs yield the same integer score deterministically. The verdict SHALL be `GO` when the score is at or above the pier's go-threshold **and cloud data for the dark window is available**, and `MAYBE` otherwise. Requiring cloud data for a `GO` — not merely a high score — SHALL hold even when the go-threshold is 0, so a `GO` is never issued without evidence the sky is clear. A brighter or more clouded night SHALL not score higher than an otherwise identical darker or clearer one.

#### Scenario: A score at or above the go-threshold with cloud data is GO

- **WHEN** every gate passes, cloud data is available, and the computed score is at or above the pier's go-threshold
- **THEN** the `verdict` is `GO`

#### Scenario: A score below the go-threshold is MAYBE

- **WHEN** every gate passes and the computed score is below the pier's go-threshold
- **THEN** the `verdict` is `MAYBE`

#### Scenario: A bright moon up during darkness lowers the score

- **WHEN** two otherwise identical nights differ only in that the moon is bright and above the horizon during the dark window in one and absent in the other
- **THEN** the night with the bright moon up during darkness has the lower score

### Requirement: Conditions are evaluated across the whole dark window

The verdict SHALL judge the night by how much usable dark time it offers, not by a single hour or a flat average. A dark window with some usably clear hours SHALL NOT be gated as overcast, and its score SHALL reflect the extent and quality of the usable portion. Terms other than cloud SHALL be weighted toward the hours that are usably clear, so a term's value during a clouded-out hour does not distort the verdict. The measure of usable dark time SHALL be normalized to the actual duration of the dark window, so a window whose start and end do not fall on whole-hour boundaries still yields a score within 0 to 100. Hours of the dark window for which cloud data is unavailable SHALL count as neither clear nor overcast: they SHALL NOT trigger the overcast gate and SHALL NOT add usable dark time to the score, so partial cloud coverage lowers the score rather than inflating it or gating the night.

#### Scenario: Hours without cloud data lower the score without gating

- **WHEN** two nights are identical and clear wherever cloud data exists, but one has cloud data covering the whole dark window and the other only covering half of it
- **THEN** neither night fails the overcast gate
- **AND** the night with cloud data for only half the window has the lower score

#### Scenario: A window that does not align to whole hours still yields a bounded score

- **WHEN** a verdict is produced for a dark window whose start and end do not fall on whole-hour boundaries
- **THEN** the `score` is an integer between 0 and 100 inclusive

#### Scenario: A partly clear night is not gated as overcast

- **WHEN** part of the dark window is usably clear and the rest is overcast
- **THEN** the overcast gate does not fail
- **AND** the score reflects the usable clear portion

#### Scenario: More usable clear darkness scores higher

- **WHEN** two nights are identical except that one has more of its dark window usably clear
- **THEN** the night with more usable clear darkness has the higher score

### Requirement: The verdict degrades honestly when conditions are unavailable

When conditions data is missing, the verdict SHALL degrade rather than fail or mislead. Missing optional data (seeing or transparency) SHALL drop only its own contribution and lower confidence. When a wind-gust limit is configured for the pier but wind data is unavailable, the safety limit cannot be checked: the verdict SHALL NOT be `GO` and SHALL be capped at `MAYBE`, so a configured safety limit is never silently ignored, with a reason that wind data is unavailable and lowered confidence. The hard gates SHALL be evaluated before the missing-cloud rule applies: a failed hard gate that does not depend on cloud data — no dark window, or a configured wind gust over its limit — SHALL still yield `NO-GO` even when cloud data is missing, so a safety-critical gate is never overridden by a missing observation. Only when every hard gate passes does the missing-cloud rule apply: when cloud data for the dark window is entirely unavailable, the verdict SHALL NOT be `GO` (there is no evidence the sky is clear) and SHALL NOT be `NO-GO` on account of the missing data itself (absence of data is not a dealbreaker); it SHALL be `MAYBE` with a `score` of 0 (no evidence the night is usable), a `confidence.value` of 0 in the `LOW` band, and a reason stating that conditions are unavailable. A verdict SHALL always be produced.

#### Scenario: Missing cloud data caps the verdict at MAYBE when gates pass

- **WHEN** a verdict is produced for a pier with a dark window, every hard gate passes, and there is no available cloud data
- **THEN** the `verdict` is `MAYBE`
- **AND** the `verdict` is neither `GO` nor `NO-GO`
- **AND** the `score` is 0
- **AND** the `confidence.value` is 0
- **AND** the `confidence.band` is `LOW`
- **AND** a reason states that conditions are unavailable

#### Scenario: A failed wind gate yields NO-GO even when cloud data is missing

- **WHEN** cloud data is unavailable but wind-gust data is available and exceeds the pier's configured wind-gust limit during the dark window
- **THEN** the `verdict` is `NO-GO`
- **AND** the `score` is null

#### Scenario: Missing wind data caps the verdict at MAYBE when a limit is configured

- **WHEN** a pier has a configured wind-gust limit, every gate that can be evaluated passes, and wind-gust data is unavailable for the dark window
- **THEN** the `verdict` is not `GO`
- **AND** the `verdict` is `MAYBE`
- **AND** a reason states that wind data is unavailable

#### Scenario: A verdict is always produced despite missing conditions

- **WHEN** conditions cannot be obtained at all for a pier with a dark window
- **THEN** a verdict document is still produced

### Requirement: Optional pier tuning configuration

A pier configuration MAY set a go-threshold (an integer from 0 to 100 that sets the score at or above which a gate-passing night is `GO` rather than `MAYBE`) and MAY set a wind-gust limit that enables the wind gate. When the go-threshold is omitted, a system default SHALL apply. When the wind-gust limit is omitted, the wind gate SHALL be disabled and gusts SHALL NOT be able to cause a `NO-GO`. These are the only tuning knobs; all other thresholds and weights are fixed by the system.

#### Scenario: Omitted go-threshold uses the default

- **WHEN** a pier configuration omits the go-threshold
- **THEN** the system default go-threshold is applied

#### Scenario: Omitted wind-gust limit disables the wind gate

- **WHEN** a pier configuration omits the wind-gust limit
- **THEN** no forecast gust can cause a `NO-GO` for that pier
