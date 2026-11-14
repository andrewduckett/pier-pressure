## ADDED Requirements

### Requirement: Confidence falls when the observed cloud is above this hour's forecast

When the pier has a usable observation and the filled cloud forecast gives low
and mid cloud for the clock hour that holds the evaluation instant, confidence
SHALL multiply by an observation factor. The gap is the observed cloud minus
that hour's forecast low and mid cloud, in points. The factor SHALL be 1 for a
gap under 15, about 0.9 from 15 to 35, and about 0.67 above 35: tuning
constants fixed in code with their justification.

#### Scenario: A large gap lowers confidence by about a third

- **WHEN** a verdict that would have a confidence of `30` without the observation is produced with a usable observation whose observed cloud is `62`, and the forecast gives `20` low and mid cloud for the hour
- **THEN** `confidence.value` is `20`

#### Scenario: A middling gap lowers confidence by about a tenth

- **WHEN** a verdict that would have a confidence of `100` without the observation is produced with a usable observation whose observed cloud is `62`, and the forecast gives `40` low and mid cloud for the hour
- **THEN** `confidence.value` is `90`

#### Scenario: A gap under 15 changes nothing

- **WHEN** two verdicts are produced for the same pier, instant and snapshot, one with a usable observation whose observed cloud is `37` while the forecast gives `25` low and mid cloud for the hour, and one with no observation
- **THEN** their `confidence` objects are identical

#### Scenario: Only the hour that holds the evaluation instant is compared

- **WHEN** a verdict is produced at `2026-11-14T21:30:00Z` from an observation measured at `2026-11-14T20:54:00Z` whose observed cloud is `62`, and the forecast gives `90` low cloud for the hour from `20:00` and `20` low and `0` mid cloud for the hour from `21:00`
- **THEN** the gap is `42`, read from the hour from `21:00`

### Requirement: The observed cloud is the most cloud a report's layers prove up to 12,000 ft

The observed cloud SHALL be the largest cover of any counted layer, in points:
`FEW` 12, `SCT` 37, `BKN` 62 and `OVC` 100, the least each code allows, for a
layer whose base is known and at most 12,000 ft. An `OVX` or `VV` layer SHALL
count as 100 whatever its base. Any other layer SHALL count for nothing. A
report with no counted layer SHALL have an observed cloud of 0.

#### Scenario: The largest layer counts

- **WHEN** an observation has layers `FEW` at 3000 ft and `BKN` at 4200 ft
- **THEN** its observed cloud is `62`

#### Scenario: A layer above 12,000 ft does not count

- **WHEN** an observation has layers `FEW` at 3000 ft and `OVC` at 25000 ft
- **THEN** its observed cloud is `12`

#### Scenario: A layer with no base does not count

- **WHEN** an observation has one layer `BKN` whose `base_ft` is null
- **THEN** its observed cloud is `0`

#### Scenario: An obscured sky counts as full cover

- **WHEN** an observation has one layer `VV` at 200 ft
- **THEN** its observed cloud is `100`

#### Scenario: An obscured sky with no base counts as full cover

- **WHEN** an observation has one layer `VV` whose `base_ft` is null
- **THEN** its observed cloud is `100`

### Requirement: The forecast's low and mid cloud combine as independent layers

That hour's forecast low and mid cloud SHALL be `low + mid − low × mid / 100`,
rounded to a whole point as the agreement spread is. High cloud SHALL never
count.

#### Scenario: Two thin layers combine

- **WHEN** the filled forecast gives `10` low and `10` mid cloud for the hour
- **THEN** the forecast low and mid cloud is `19`

#### Scenario: High cloud is ignored

- **WHEN** two verdicts are produced from snapshots that differ only in that hour's high cloud, `0` in one and `100` in the other, each with the same usable observation
- **THEN** their `confidence` objects are identical

### Requirement: A report that shows less cloud than the forecast never changes confidence

The observation factor SHALL be 1 whenever the observed cloud is at or below
the forecast low and mid cloud for the hour, so a clear report, a `CAVOK`
report or a report of less cloud never raises or lowers confidence.

#### Scenario: A clear report under a cloudy forecast

- **WHEN** two verdicts are produced for the same pier, instant and snapshot, whose forecast gives `80` low cloud for the hour, one with a usable `CLR` observation with no layers and one with no observation
- **THEN** their `confidence` objects are identical

#### Scenario: A CAVOK report under a cloudy forecast

- **WHEN** two verdicts are produced for the same pier, instant and snapshot, whose forecast gives `80` low cloud for the hour, one with a usable `CAVOK` observation with no layers and one with no observation
- **THEN** their `confidence` objects are identical

### Requirement: The observation factor needs a usable observation and this hour's low and mid cloud

The observation factor SHALL be 1 when the pier has no usable observation. It
SHALL also be 1 when the filled cloud forecast lacks a low or a mid value for
the clock hour that holds the evaluation instant.

#### Scenario: No mid cloud for the hour

- **WHEN** two verdicts are produced for the same pier and instant from a snapshot with low cloud but no mid cloud for the hour, one with a usable observation whose observed cloud is `100` and one with no observation
- **THEN** their `confidence` objects are identical

#### Scenario: A stale report

- **WHEN** a verdict is produced at `2026-11-14T22:25:00Z` from an observation measured at `2026-11-14T20:54:00Z` whose observed cloud is `100`, and the forecast gives `0` low and mid cloud for the hour
- **THEN** its `confidence` is the same as with no observation

### Requirement: The observation and agreement together never take confidence below MEDIUM

The observation factor SHALL multiply with the agreement factor. When the value
before both is at or above the `MEDIUM` threshold, the value after them SHALL be
at least that threshold.

#### Scenario: Disagreement and a contradicting report stay MEDIUM

- **WHEN** a verdict a day before dusk, with a fresh and complete forecast, would have a confidence of `50` without alternates or the observation, and is produced with an alternate that makes the agreement band `DISAGREE` and a usable observation whose gap is over 35
- **THEN** `confidence.value` is `40` and `confidence.band` is `MEDIUM`
- **AND** no reason line begins with `Observed cloud`, because the value is the same as without the observation

### Requirement: The observation factor applies only where confidence comes from the forecast

The observation factor SHALL apply to every verdict whose confidence comes
from the forecast, a gated `NO-GO` included. It SHALL NOT change the fixed
confidence of a verdict with no dark window, no dark time left or no cloud
data.

#### Scenario: A gated NO-GO is lowered too

- **WHEN** a verdict is `NO-GO` because a gust is over the limit, and it would have a confidence of `100` without the observation, with a usable observation whose observed cloud is `62` while the forecast gives `0` low and mid cloud for the hour
- **THEN** `confidence.value` is `67`

#### Scenario: No dark window keeps full confidence

- **WHEN** the verdict is `NO-GO` because the selected night has no dark window, with a usable observation whose observed cloud is `100` and a forecast of `0` low and mid cloud for the hour
- **THEN** `confidence.band` is `HIGH` and `confidence.value` is `100`

### Requirement: A lowered confidence adds one observed-cloud line

When the observation makes `confidence.value` lower than it would be without
the observation, `reasons` SHALL carry exactly one line
`Observed cloud above this hour's forecast: <station> reported at least <obs>%,
the forecast gave <fc>% low and mid cloud, a gap of <gap> points. Confidence
lowered.`, with `<obs>` the observed cloud, `<fc>` the forecast low and mid
cloud and `<gap>` the gap. Otherwise no such line SHALL appear.

#### Scenario: A contradicting report is named

- **WHEN** a verdict is produced with a usable observation from `KBOS` whose observed cloud is `62`, and the forecast gives `20` low and `0` mid cloud for the hour
- **THEN** `reasons` contains `Observed cloud above this hour's forecast: KBOS reported at least 62%, the forecast gave 20% low and mid cloud, a gap of 42 points. Confidence lowered.`

#### Scenario: A small gap adds no line

- **WHEN** a verdict is produced with a usable observation whose observed cloud is `12`, and the forecast gives `0` low and mid cloud for the hour
- **THEN** no reason line begins with `Observed cloud`

#### Scenario: A fixed confidence adds no line

- **WHEN** a verdict is produced from a snapshot with no cloud cover series, with a usable observation whose observed cloud is `100`
- **THEN** no reason line begins with `Observed cloud`

### Requirement: The observed-cloud line follows the observation line

The observed-cloud line SHALL come straight after the observation line, on a
gated `NO-GO` as well as a scored verdict, and before the equipment notes about
the top pick.

#### Scenario: The line follows the observation line

- **WHEN** a verdict is `MAYBE` with a usable observation that lowers confidence, for a pier with no equipment
- **THEN** the last two reasons are the observation line and the `Observed cloud` line, in that order

#### Scenario: The line comes before the equipment notes

- **WHEN** a verdict is `GO` with a usable observation that lowers confidence, for a pier with equipment and a top pick
- **THEN** the `Observed cloud` line comes before every equipment note

### Requirement: The observation changes no gate, score, agreement or timeline

The observation SHALL NOT change the verdict, the score, the agreement or the
timeline.

#### Scenario: Two verdicts differ only in the observation

- **WHEN** two verdicts are produced for the same pier, instant and snapshot, one with a usable observation whose observed cloud is `100` and one with none, and the forecast gives `0` low and mid cloud for the hour
- **THEN** their `verdict`, `score`, `agreement` and `timeline` are identical
- **AND** their `reasons` differ only by the observation line and the `Observed cloud` line

## MODIFIED Requirements

### Requirement: Confidence is always present with a band and a value from 0 to 100

The `confidence` field SHALL always be present and SHALL contain a `band` that
is exactly one of `LOW`, `MEDIUM`, or `HIGH`, and a `value` that is an integer
from 0 to 100 inclusive. Confidence expresses how much to trust the verdict
given how far ahead the forecast reaches, how complete the underlying data is,
how well the providers' cloud forecasts agree when there is more than one, and
whether the pier's airport reports more cloud than this hour's forecast.

#### Scenario: Confidence carries a band and a bounded value

- **WHEN** a verdict is produced for a valid pier configuration
- **THEN** the `confidence.band` field equals `LOW`, `MEDIUM`, or `HIGH`
- **AND** the `confidence.value` field is an integer between 0 and 100 inclusive

### Requirement: The dew line is last and changes nothing else

The dew or frost line SHALL come after every other line the core emits for the verdict, including any cap line and the agreement line, so every existing line keeps its position. Only the observation line and the observed-cloud line come after it. On a gated `NO-GO` no such line SHALL appear. The line SHALL NOT change the verdict, the score or the confidence.

#### Scenario: The line follows the agreement line and is last

- **WHEN** a verdict is `GO` with `agreement.cloud_cover` present, a scored hour under the margin and no usable observation
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

### Requirement: The observation line follows the core's other lines on every verdict

The observation line SHALL appear on every verdict with a usable observation,
a gated `NO-GO` and a night with no dark window included. It SHALL come after
every other line the core emits for the verdict, the dew line included, except
the observed-cloud line, and before the equipment notes about the top pick.

#### Scenario: The line follows the dew line

- **WHEN** a verdict is `GO` with a `Dew likely from` line and a usable observation that does not lower confidence, for a pier with no equipment
- **THEN** the last two reasons are the `Dew likely from` line and the observation line, in that order

#### Scenario: The line comes before the equipment notes

- **WHEN** a verdict is `GO` with a usable observation, for a pier with equipment and a top pick
- **THEN** the observation line comes before every equipment note

#### Scenario: A gated NO-GO keeps the line

- **WHEN** a verdict is `NO-GO` for an overcast dark window, with a usable observation that does not lower confidence
- **THEN** `reasons` names the overcast gate first
- **AND** its last line is the observation line

## REMOVED Requirements

### Requirement: The observation changes no gate, score or confidence

**Reason**: The observation now lowers confidence when it reports more cloud
than this hour's forecast.

**Migration**: "The observation changes no gate, score, agreement or timeline"
keeps the rest of the guarantee. Readers of `confidence` see lower values only
for piers that name a station.
