## ADDED Requirements

### Requirement: The document carries cloud agreement

The verdict document SHALL carry an `agreement` object, always present, keyed by variable. Its `cloud_cover` entry SHALL be present exactly when at least one hour of the scored window has a cloud-cover value from two or more providers, counting the filled `cloud_cover` series and its alternates. Otherwise `agreement` SHALL be the empty object. The entry SHALL hold three fields. `band` is exactly one of `AGREE`, `MIXED` or `DISAGREE`. `spread` is the night's mean cloud gap in percentage points, rounded to a whole number. `providers` lists the keys of every provider that gives a value for at least one counted hour, the filled series' provider first when it is among them, then the alternates in configured order.

#### Scenario: Two providers that nearly agree

- **WHEN** a verdict is produced before dusk, the filled `cloud_cover` series and one alternate each cover the whole dark window, and their values differ by 8 points in every hour
- **THEN** `agreement.cloud_cover.band` is `AGREE`
- **AND** `agreement.cloud_cover.spread` is `8`
- **AND** `agreement.cloud_cover.providers` lists the filled series' provider key first and the alternate's second

#### Scenario: One provider yields no agreement

- **WHEN** a verdict is produced from a snapshot whose `cloud_cover` series has no alternate
- **THEN** `agreement` is the empty object `{}`

#### Scenario: An alternate that covers no scored hour does not count

- **WHEN** a verdict is produced mid-session and the only `cloud_cover` alternate covers hours that have already passed
- **THEN** `agreement` is the empty object `{}`

#### Scenario: Providers that never share an hour yield no agreement

- **WHEN** the filled series covers only the first two hours of the scored window and the only alternate covers only its last two hours
- **THEN** `agreement` is the empty object `{}`

#### Scenario: A provider that shares no counted hour is not listed

- **WHEN** three providers return cloud cover, two cover the whole scored window and the third covers only hours after it
- **THEN** `agreement.cloud_cover.providers` lists the two providers only

#### Scenario: No dark window means no agreement

- **WHEN** a verdict is `NO-GO` because the selected night has no dark window, and the snapshot carries a `cloud_cover` alternate
- **THEN** `agreement` is the empty object `{}`

### Requirement: Cloud agreement is the clarity-weighted mean gap over the scored window

The gap for an hour SHALL be the highest cloud cover any participating provider gives for that hour minus the lowest, counted only for an hour two or more of them cover. The night's mean gap SHALL weight each counted hour by its coverage of the scored window times the clarity weight of that hour's lowest cloud cover, on the same clarity curve the score uses. When every weight is zero, the mean SHALL be 0. `band` SHALL be decided on the rounded `spread`: `AGREE` below 15 points, `MIXED` from 15 to 35 inclusive, and `DISAGREE` above 35, so the band and the spread a reader sees never disagree.

#### Scenario: A mixed and a disagreeing night

- **WHEN** two verdicts are produced from snapshots where the filled series and one alternate differ by 25 points in every hour, and by 45 points in every hour
- **THEN** the first document's `agreement.cloud_cover.band` is `MIXED` with `spread` `25`
- **AND** the second's is `DISAGREE` with `spread` `45`

#### Scenario: An hour one provider covers is left out of the mean

- **WHEN** the filled series covers the whole dark window and the alternate covers only its first half, differing by 40 points there
- **THEN** `agreement.cloud_cover.spread` is `40`

#### Scenario: Disagreement in an hour the filled series calls overcast still counts

- **WHEN** the filled series gives `95` for every hour of the dark window and the alternate gives `20`
- **THEN** `agreement.cloud_cover.band` is `DISAGREE`
- **AND** `agreement.cloud_cover.spread` is `75`

#### Scenario: Clear hours weigh more than cloudy ones

- **WHEN** the filled series and the alternate differ by 50 points in hours where the lowest value is `5`, and by 5 points in hours where the lowest value is `85`
- **THEN** `agreement.cloud_cover.spread` is closer to `50` than to `5`

#### Scenario: The band follows the rounded spread

- **WHEN** the unrounded mean gap is 14.6 points
- **THEN** `agreement.cloud_cover.spread` is `15` and `agreement.cloud_cover.band` is `MIXED`

#### Scenario: Unanimous overcast is agreement

- **WHEN** the filled series and the alternate each give `95` or more for every hour of the dark window
- **THEN** `agreement.cloud_cover.band` is `AGREE`
- **AND** `agreement.cloud_cover.spread` is `0`

### Requirement: Confidence falls with low agreement

Confidence SHALL multiply by an agreement factor: 1 when `agreement.cloud_cover` is absent or `AGREE`, about 0.9 when `MIXED`, and about 0.67 when `DISAGREE`. The factor SHALL be a tuning constant fixed in code with its justification. The factor SHALL never take a confidence that is `MEDIUM` or `HIGH` without it below `MEDIUM`: when the value before the factor is at or above the `MEDIUM` threshold, the value after it SHALL be at least that threshold. Agreement SHALL change no gate, no score and no verdict value. An alternate's issue time SHALL NOT change confidence.

#### Scenario: Mixed agreement lowers confidence

- **WHEN** two verdicts are produced for the same pier and instant from snapshots that differ only in the alternate's values, so one is `AGREE` and the other `MIXED`
- **THEN** the `MIXED` document's `confidence.value` is lower than the `AGREE` document's
- **AND** the two documents have the same `verdict` and `score`

#### Scenario: Disagreement lowers confidence further

- **WHEN** two verdicts are produced from snapshots that differ only in the alternate's values, so one is `MIXED` and the other `DISAGREE`
- **THEN** the `DISAGREE` document's `confidence.value` is lower than the `MIXED` document's

#### Scenario: Disagreement alone never reaches LOW

- **WHEN** a verdict that would have a confidence of `100` without alternates is produced with an alternate that makes the band `DISAGREE`
- **THEN** `confidence.band` is `MEDIUM`

#### Scenario: Disagreement at a long lead time stays MEDIUM

- **WHEN** a verdict a day before dusk, with a fresh and complete forecast, would have a confidence of `50` without alternates, and an alternate makes the band `DISAGREE`
- **THEN** `confidence.value` is `40` and `confidence.band` is `MEDIUM`

#### Scenario: An already LOW confidence still falls

- **WHEN** a verdict that would have a confidence of `30` without alternates is produced with an alternate that makes the band `DISAGREE`
- **THEN** `confidence.value` is `20`

#### Scenario: A stale alternate does not lower confidence

- **WHEN** two verdicts are produced for the same pier and instant from snapshots that differ only in the issue time of a `cloud_cover` alternate
- **THEN** the two documents are byte-identical

### Requirement: Reasons name the agreement

When `agreement.cloud_cover` is present, the `reasons` list SHALL carry exactly one line `Cloud agreement <agree|mixed|disagree>: <n> providers, spread <spread> points.`. `<n>` is the number of providers listed and `<spread>` the document's spread. When the band is `MIXED` or `DISAGREE`, the line SHALL end with ` Confidence lowered.`. The line SHALL come after the lines that name the gate or itemize the score, on a gated `NO-GO` as well as a scored verdict, so every earlier line keeps its position. When `agreement` is empty, no such line SHALL appear.

#### Scenario: A scored verdict names the agreement

- **WHEN** a verdict is `GO` with `agreement.cloud_cover` of band `AGREE`, spread `8` and two providers
- **THEN** `reasons` contains `Cloud agreement agree: 2 providers, spread 8 points.`
- **AND** it follows the `Score N/100.` line

#### Scenario: A gated verdict names the agreement

- **WHEN** a verdict is `NO-GO` for an overcast dark window and `agreement.cloud_cover` is `DISAGREE` with spread `60` across two providers
- **THEN** `reasons` names the overcast gate first
- **AND** then contains `Cloud agreement disagree: 2 providers, spread 60 points. Confidence lowered.`

#### Scenario: One provider adds no line

- **WHEN** a verdict is produced from a snapshot whose `cloud_cover` series has no alternate
- **THEN** no reason line begins with `Cloud agreement`

### Requirement: Entry cloud band carries the lowest and highest cloud any provider gave

Each timeline entry's `cloud_cover_min` and `cloud_cover_max` SHALL be the lowest and highest `cloud_cover` any provider, the filled series or an alternate, gives for that hour, in percent exactly as the series hold them. Both SHALL be null when fewer than two providers give a value for the hour.

#### Scenario: Two providers draw the band

- **WHEN** the filled `cloud_cover` series holds `40.0` and the one alternate `70.0` for an hour
- **THEN** that entry's `cloud_cover` is `40.0`, `cloud_cover_min` is `40.0` and `cloud_cover_max` is `70.0`

#### Scenario: One provider leaves the band null

- **WHEN** the filled `cloud_cover` series holds `40.0` for an hour and no alternate covers that hour
- **THEN** that entry's `cloud_cover` is `40.0` and its `cloud_cover_min` and `cloud_cover_max` are null

#### Scenario: Two alternates without the filled series still draw the band

- **WHEN** the filled series lacks an hour that two alternates cover with `10.0` and `30.0`
- **THEN** that entry's `cloud_cover` is null, `cloud_cover_min` is `10.0` and `cloud_cover_max` is `30.0`

## MODIFIED Requirements

### Requirement: A timeline entry has a fixed flat shape

Each timeline entry SHALL carry exactly these keys, always present and in this order: `time`, `sun_altitude`, `moon_altitude`, `cloud_cover`, `cloud_low`, `cloud_mid`, `cloud_high`, `wind_gust`, `seeing`, `transparency`, `temperature`, `dew_point`, `humidity`, `wind_speed`, `wind_direction`, `precipitation_probability`, `cloud_cover_min`, `cloud_cover_max`. `time` SHALL be the top of the hour, emitted like every other document timestamp. The two cloud band keys come last, after the six weather keys, so every key that preceded them keeps its position.

#### Scenario: A read-back entry equals the emitted one

- **WHEN** a document with a timeline is serialized to JSON and read back
- **THEN** every entry's keys, order and values are unchanged

#### Scenario: The keys before the weather keys keep their positions

- **WHEN** a document with a timeline is serialized to JSON
- **THEN** each entry's first ten keys are `time`, `sun_altitude`, `moon_altitude`, `cloud_cover`, `cloud_low`, `cloud_mid`, `cloud_high`, `wind_gust`, `seeing`, `transparency`, in that order
- **AND** the six weather keys follow them in the order `temperature`, `dew_point`, `humidity`, `wind_speed`, `wind_direction`, `precipitation_probability`

#### Scenario: The cloud band keys come last

- **WHEN** a document with a timeline is serialized to JSON
- **THEN** each entry's last two keys are `cloud_cover_min` then `cloud_cover_max`

### Requirement: The document carries an hourly timeline

The verdict document SHALL carry a `timeline` list: the hourly series of sky and weather for the pier. The list SHALL hold one entry per clock hour across the union of the hours every filled series in the conditions covers, including hours already past. Hours only an alternate covers SHALL NOT add an entry. It SHALL be sorted by hour ascending, with no hour repeated. The list SHALL be empty, never absent, when no provider returned rows.

#### Scenario: The timeline spans the union of both providers' hours

- **WHEN** a verdict is produced with a cloud-cover series covering 00:00 to 23:00 on one day and a seeing series covering 12:00 on that day to 11:00 two days later
- **THEN** the `timeline` holds one entry for every hour from the first day's 00:00 to the third day's 11:00, in ascending order, with no hour repeated

#### Scenario: No provider rows yield an empty timeline

- **WHEN** a verdict is produced with the empty conditions value
- **THEN** the document's `timeline` is an empty list
- **AND** the verdict is produced without error

#### Scenario: Past hours stay in the timeline

- **WHEN** a verdict is produced inside the dark window, with the evaluation instant later than some hours a provider returned
- **THEN** the entries for those earlier hours are present and unchanged
- **AND** the `scored_window` still starts at the evaluation instant

#### Scenario: Hours only an alternate covers add no entry

- **WHEN** every filled series ends at 03:00 and a `cloud_cover` alternate runs to 03:00 two days later
- **THEN** the `timeline`'s last entry is 03:00 on the first night

### Requirement: Confidence is present and banded

The `confidence` field SHALL always be present and SHALL contain a `band` that is exactly one of `LOW`, `MEDIUM`, or `HIGH`, and a `value` that is an integer from 0 to 100 inclusive. Confidence expresses how much to trust the verdict given how far ahead the forecast reaches, how complete the underlying data is and, when more than one provider gives cloud cover, how well their forecasts agree. Confidence SHALL rise as the evaluation instant approaches the dark window and SHALL fall when the forecast is stale, when conditions data is missing or when the providers' cloud forecasts disagree. Confidence is orthogonal to the score: a low-confidence GO and a high-confidence NO-GO are both permitted. When the verdict is a `NO-GO` because there is no dark window, no forecast is involved and the confidence SHALL be `HIGH` with a value of 100, because it rests on deterministic offline astronomy rather than on a forecast.

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
