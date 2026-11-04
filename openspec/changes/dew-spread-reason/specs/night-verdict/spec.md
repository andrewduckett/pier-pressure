## ADDED Requirements

### Requirement: Reasons name the first dew or frost hour

When every hard gate passes and the pier's dew margin is above zero, the `reasons` list SHALL carry at most one dew or frost line. The line names the first hour of the scored window whose spread is strictly less than the margin. An hour's spread is its temperature minus its dew point, in °C. The line SHALL read `Frost likely from <time>.` when that hour's temperature is at or below 0 °C, and `Dew likely from <time>.` otherwise. `<time>` is the start of that hour, as the same UTC date and time string the document emits for its timestamps. When no hour qualifies, no such line SHALL appear.

#### Scenario: Dew is named from the first hour under the margin

- **WHEN** a pier with the default dew margin of 4 °C has a scored window from 20:30 to 03:25 UTC, every gate passes, the air stays above freezing, and the spread is 6 °C at 20:00, 5 °C at 21:00, 3.5 °C at 22:00 and 2 °C at 23:00
- **THEN** `reasons` contains `Dew likely from 2026-09-08T22:00:00Z.`
- **AND** no other reason line begins with `Dew` or `Frost`

#### Scenario: Frost is named when the first hour under the margin is freezing

- **WHEN** the first scored hour whose spread falls under the margin has a temperature of 0 °C or lower
- **THEN** `reasons` contains `Frost likely from <time>.` for that hour
- **AND** no reason line begins with `Dew`

#### Scenario: Dew first and frost later gives one dew line

- **WHEN** the first scored hour under the margin is at 2 °C and a later scored hour under the margin is at −1 °C
- **THEN** `reasons` contains one `Dew likely from` line naming the first hour
- **AND** no reason line begins with `Frost`

#### Scenario: A spread equal to the margin is not under it

- **WHEN** every scored hour's spread is exactly 4 °C and the dew margin is 4 °C
- **THEN** no reason line begins with `Dew` or `Frost`

#### Scenario: A zero margin turns the line off

- **WHEN** a pier sets a dew margin of 0 and every scored hour's spread is 1 °C
- **THEN** no reason line begins with `Dew` or `Frost`

#### Scenario: Missing cloud still gets the line

- **WHEN** cloud data is entirely unavailable for the scored window, every hard gate passes, and a scored hour's spread is 1 °C
- **THEN** the verdict is `MAYBE` with a reason that conditions are unavailable
- **AND** `reasons` also contains a `Dew likely from` line

### Requirement: The dew walk reads the scored window's hours in order

The dew walk SHALL read the scored window's hour slots in order from its start, as the score does. An hour that lacks temperature or dew point SHALL be skipped. Cloud SHALL neither exclude nor weight an hour.

#### Scenario: A passed hour is not named, and a boundary hour names its start

- **WHEN** a verdict is produced at 23:30 UTC inside a dark window that opened at 20:30 UTC, and the spread is under the margin at 22:00 and at 23:00
- **THEN** `reasons` contains `Dew likely from 2026-09-08T23:00:00Z.`
- **AND** no reason line names 22:00

#### Scenario: An hour without both values is skipped

- **WHEN** the first scored hour has a temperature but no dew point, and the next hour has a spread of 1 °C
- **THEN** the `Dew likely from` line names the second hour

#### Scenario: No temperature or dew point gives no line

- **WHEN** no scored hour carries both a temperature and a dew point
- **THEN** no reason line begins with `Dew` or `Frost`

### Requirement: The dew line is last and changes nothing else

The dew or frost line SHALL come after every other line the core emits for the verdict, including any cap line and the agreement line, so every existing line keeps its position. On a gated `NO-GO` no such line SHALL appear. The line SHALL NOT change the verdict, the score or the confidence.

#### Scenario: The line follows the agreement line and is last

- **WHEN** a verdict is `GO` with `agreement.cloud_cover` present and a scored hour under the margin
- **THEN** the core's last three reasons are the `Score N/100.` line, the `Cloud agreement` line and the `Dew likely from` line, in that order

#### Scenario: The line follows a cap line and the agreement line

- **WHEN** a verdict is `MAYBE` because wind data does not cover the scored window, `agreement.cloud_cover` is present, and a scored hour is under the margin
- **THEN** the `Dew likely from` line comes after both the wind-unavailable line and the `Cloud agreement` line

#### Scenario: A gated NO-GO carries no dew line

- **WHEN** a verdict is `NO-GO` for an overcast dark window and every scored hour's spread is 1 °C
- **THEN** no reason line begins with `Dew` or `Frost`

#### Scenario: The line changes nothing else

- **WHEN** two verdicts are produced for the same pier and instant from snapshots that differ only in temperature and dew point
- **THEN** their `verdict`, `score` and `confidence` are identical
- **AND** their `reasons` differ at most by one `Dew likely from` or `Frost likely from` line

## MODIFIED Requirements

### Requirement: Optional pier tuning configuration

A pier configuration MAY set three tuning knobs:

- a go-threshold: an integer from 0 to 100. A gate-passing night with a score at or above it is `GO` rather than `MAYBE`;
- a wind-gust limit, which enables the wind gate;
- a dew margin in °C: a finite number of 0 or more. A spread between temperature and dew point under it makes dew or frost likely.

When the go-threshold is omitted, a system default SHALL apply. When the wind-gust limit is omitted, the wind gate SHALL be disabled and gusts SHALL NOT be able to cause a `NO-GO`. When the dew margin is omitted, it SHALL be 4 °C. A dew margin of 0 SHALL turn the dew line off. A negative or non-finite dew margin SHALL be rejected as a configuration error. These are the only tuning knobs; all other thresholds and weights are fixed by the system.

#### Scenario: Omitted go-threshold uses the default

- **WHEN** a pier configuration omits the go-threshold
- **THEN** the system default go-threshold is applied

#### Scenario: Omitted wind-gust limit disables the wind gate

- **WHEN** a pier configuration omits the wind-gust limit
- **THEN** no forecast gust can cause a `NO-GO` for that pier

#### Scenario: Omitted dew margin is 4 °C

- **WHEN** a pier configuration omits the dew margin
- **THEN** the pier's dew margin is 4 °C

#### Scenario: A negative or infinite dew margin is rejected

- **WHEN** a pier configuration sets a dew margin of −1, or of `.inf`
- **THEN** loading the configuration fails with an error that names the dew margin
