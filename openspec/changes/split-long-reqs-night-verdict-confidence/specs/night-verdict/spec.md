## ADDED Requirements

### Requirement: Confidence is always present with a band and a value from 0 to 100

The `confidence` field SHALL always be present and SHALL contain a `band` that
is exactly one of `LOW`, `MEDIUM`, or `HIGH`, and a `value` that is an integer
from 0 to 100 inclusive. Confidence expresses how much to trust the verdict
given how far ahead the forecast reaches, how complete the underlying data is
and, when more than one provider gives cloud cover, how well their forecasts
agree.

#### Scenario: Confidence carries a band and a bounded value

- **WHEN** a verdict is produced for a valid pier configuration
- **THEN** the `confidence.band` field equals `LOW`, `MEDIUM`, or `HIGH`
- **AND** the `confidence.value` field is an integer between 0 and 100 inclusive

### Requirement: Confidence rises as the evaluation instant approaches the dark window

Confidence SHALL rise as the evaluation instant approaches the dark window.

#### Scenario: Confidence rises as the dark window nears

- **WHEN** two verdicts are produced for the same pier, one long before the dark window begins and one shortly before it begins, each using a forecast freshly issued at its evaluation instant so freshness and data completeness are equal for both
- **THEN** the confidence produced shortly before the dark window is at least as high as the confidence produced long before it

### Requirement: Confidence falls when the forecast is stale, data is missing or forecasts disagree

Confidence SHALL fall when the forecast is stale, when conditions data is
missing or when the providers' cloud forecasts disagree. Confidence is
orthogonal to the score: a low-confidence GO and a high-confidence NO-GO are
both permitted.

#### Scenario: Missing optional data lowers confidence

- **WHEN** a verdict is produced from conditions in which optional fields (seeing or transparency) are unavailable
- **THEN** the confidence is lower than it would be for the same conditions with those fields available
- **AND** the missing optional data does not fail a gate and does not null the score

### Requirement: A NO-GO with no dark window has full confidence

When the verdict is a `NO-GO` because there is no dark window, no forecast is
involved and the confidence SHALL be `HIGH` with a value of 100, because it
rests on deterministic offline astronomy rather than on a forecast.

#### Scenario: Astronomy-only NO-GO is fully confident

- **WHEN** the verdict is `NO-GO` because the selected night has no dark window
- **THEN** the `confidence.band` is `HIGH`
- **AND** the `confidence.value` is 100

### Requirement: The timeline holds one entry per hour a shown variable's filled series covers

The verdict document SHALL carry a `timeline` list: the hourly series of sky and
weather for the pier. The list SHALL hold one entry per clock hour that a filled
series of a shown variable covers, including hours already past. A shown
variable is one the timeline carries as a key. The list SHALL be sorted by hour
ascending, with no hour repeated.

#### Scenario: The timeline spans the union of both providers' hours

- **WHEN** a verdict is produced with a cloud-cover series covering 00:00 to 23:00 on one day and a seeing series covering 12:00 on that day to 11:00 two days later
- **THEN** the `timeline` holds one entry for every hour from the first day's 00:00 to the third day's 11:00, in ascending order, with no hour repeated

#### Scenario: Past hours stay in the timeline

- **WHEN** a verdict is produced inside the dark window, with the evaluation instant later than some hours a provider returned
- **THEN** the entries for those earlier hours are present and unchanged
- **AND** the `scored_window` still starts at the evaluation instant

### Requirement: Hours that only an alternate or a hidden variable covers add no timeline entry

Hours only an alternate covers SHALL NOT add a timeline entry. Hours only a
series of a variable the timeline does not show covers SHALL NOT add a timeline
entry.

#### Scenario: Hours only an alternate covers add no entry

- **WHEN** every filled series ends at 03:00 and a `cloud_cover` alternate runs to 03:00 two days later
- **THEN** the `timeline`'s last entry is 03:00 on the first night

#### Scenario: Hours only a hidden variable covers add no entry

- **WHEN** every filled series of a variable the timeline shows ends at 03:00 and an `aerosol_optical_depth` series runs to 03:00 two days later
- **THEN** the `timeline`'s last entry is 03:00 on the first night

### Requirement: The timeline is empty, never absent, when no provider returned rows

The `timeline` list SHALL be empty, never absent, when no provider returned rows
for a variable the timeline shows.

#### Scenario: No provider rows yield an empty timeline

- **WHEN** a verdict is produced with the empty conditions value
- **THEN** the document's `timeline` is an empty list
- **AND** the verdict is produced without error

### Requirement: A timeline entry carries exactly eighteen keys in a fixed order

Each timeline entry SHALL carry exactly these keys, always present and in this
order: `time`, `sun_altitude`, `moon_altitude`, `cloud_cover`, `cloud_low`,
`cloud_mid`, `cloud_high`, `wind_gust`, `seeing`, `transparency`, `temperature`,
`dew_point`, `humidity`, `wind_speed`, `wind_direction`,
`precipitation_probability`, `cloud_cover_min`, `cloud_cover_max`. The two cloud
band keys come last, after the six weather keys, so every key that preceded them
keeps its position.

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

### Requirement: A timeline entry's time is the top of the hour

A timeline entry's `time` SHALL be the top of the hour, emitted like every other
document timestamp.

#### Scenario: An entry's time is emitted as a UTC timestamp

- **WHEN** a timeline entry is built for the hour that starts at 01:00 on 2026-09-08 at UTC+02:00
- **THEN** its serialized `time` is `2026-09-07T23:00:00Z`

### Requirement: The agreement object has a cloud-cover entry only when two providers share a scored hour

The verdict document SHALL carry an `agreement` object, always present, keyed by
variable. Its `cloud_cover` entry SHALL be present exactly when at least one
hour of the scored window has a cloud-cover value from two or more providers,
counting the filled `cloud_cover` series and its alternates. Otherwise
`agreement` SHALL be the empty object.

#### Scenario: One provider yields no agreement

- **WHEN** a verdict is produced from a snapshot whose `cloud_cover` series has no alternate
- **THEN** `agreement` is the empty object `{}`

#### Scenario: An alternate that covers no scored hour does not count

- **WHEN** a verdict is produced mid-session and the only `cloud_cover` alternate covers hours that have already passed
- **THEN** `agreement` is the empty object `{}`

#### Scenario: Providers that never share an hour yield no agreement

- **WHEN** the filled series covers only the first two hours of the scored window and the only alternate covers only its last two hours
- **THEN** `agreement` is the empty object `{}`

#### Scenario: No dark window means no agreement

- **WHEN** a verdict is `NO-GO` because the selected night has no dark window, and the snapshot carries a `cloud_cover` alternate
- **THEN** `agreement` is the empty object `{}`

### Requirement: The cloud-cover agreement entry holds a band, a spread and its providers

The `cloud_cover` entry of `agreement` SHALL hold three fields. `band` is
exactly one of `AGREE`, `MIXED` or `DISAGREE`. `spread` is the night's mean
cloud gap in percentage points, rounded to a whole number. `providers` lists the
keys of every provider that gives a value for at least one counted hour, the
filled series' provider first when it is among them, then the alternates in
configured order.

#### Scenario: Two providers that nearly agree

- **WHEN** a verdict is produced before dusk, the filled `cloud_cover` series and one alternate each cover the whole dark window, and their values differ by 8 points in every hour
- **THEN** `agreement.cloud_cover.band` is `AGREE`
- **AND** `agreement.cloud_cover.spread` is `8`
- **AND** `agreement.cloud_cover.providers` lists the filled series' provider key first and the alternate's second

#### Scenario: A provider that shares no counted hour is not listed

- **WHEN** three providers return cloud cover, two cover the whole scored window and the third covers only hours after it
- **THEN** `agreement.cloud_cover.providers` lists the two providers only

### Requirement: An hour's cloud gap is the highest reading minus the lowest

The gap for an hour SHALL be the highest cloud cover any participating provider
gives for that hour minus the lowest, counted only for an hour two or more of
them cover.

#### Scenario: An hour one provider covers is left out of the mean

- **WHEN** the filled series covers the whole dark window and the alternate covers only its first half, differing by 40 points there
- **THEN** `agreement.cloud_cover.spread` is `40`

### Requirement: The mean cloud gap weights each hour by its coverage and its clearest reading

The night's mean gap SHALL weight each counted hour by its coverage of the
scored window times the clarity weight of that hour's lowest cloud cover, on the
same clarity curve the score uses. When every weight is zero, the mean SHALL be
0.

#### Scenario: Disagreement in an hour the filled series calls overcast still counts

- **WHEN** the filled series gives `95` for every hour of the dark window and the alternate gives `20`
- **THEN** `agreement.cloud_cover.band` is `DISAGREE`
- **AND** `agreement.cloud_cover.spread` is `75`

#### Scenario: Clear hours weigh more than cloudy ones

- **WHEN** the filled series and the alternate differ by 50 points in hours where the lowest value is `5`, and by 5 points in hours where the lowest value is `85`
- **THEN** `agreement.cloud_cover.spread` is closer to `50` than to `5`

#### Scenario: Unanimous overcast is agreement

- **WHEN** the filled series and the alternate each give `95` or more for every hour of the dark window
- **THEN** `agreement.cloud_cover.band` is `AGREE`
- **AND** `agreement.cloud_cover.spread` is `0`

### Requirement: The agreement band is decided on the rounded spread

The agreement `band` SHALL be decided on the rounded `spread`: `AGREE` below 15
points, `MIXED` from 15 to 35 inclusive, and `DISAGREE` above 35, so the band
and the spread a reader sees never disagree.

#### Scenario: A mixed and a disagreeing night

- **WHEN** two verdicts are produced from snapshots where the filled series and one alternate differ by 25 points in every hour, and by 45 points in every hour
- **THEN** the first document's `agreement.cloud_cover.band` is `MIXED` with `spread` `25`
- **AND** the second's is `DISAGREE` with `spread` `45`

#### Scenario: The band follows the rounded spread

- **WHEN** the unrounded mean gap is 14.6 points
- **THEN** `agreement.cloud_cover.spread` is `15` and `agreement.cloud_cover.band` is `MIXED`

### Requirement: Confidence is multiplied by an agreement factor set by the band

Confidence SHALL multiply by an agreement factor: 1 when `agreement.cloud_cover`
is absent or `AGREE`, about 0.9 when `MIXED`, and about 0.67 when `DISAGREE`.
The factor SHALL be a tuning constant fixed in code with its justification.

#### Scenario: Disagreement lowers confidence further

- **WHEN** two verdicts are produced from snapshots that differ only in the alternate's values, so one is `MIXED` and the other `DISAGREE`
- **THEN** the `DISAGREE` document's `confidence.value` is lower than the `MIXED` document's

#### Scenario: An already LOW confidence still falls

- **WHEN** a verdict that would have a confidence of `30` without alternates is produced with an alternate that makes the band `DISAGREE`
- **THEN** `confidence.value` is `20`

### Requirement: Agreement alone never takes confidence below MEDIUM

The agreement factor SHALL never take a confidence that is `MEDIUM` or `HIGH`
without it below `MEDIUM`: when the value before the factor is at or above the
`MEDIUM` threshold, the value after it SHALL be at least that threshold.

#### Scenario: Disagreement alone never reaches LOW

- **WHEN** a verdict that would have a confidence of `100` without alternates is produced with an alternate that makes the band `DISAGREE`
- **THEN** `confidence.band` is `MEDIUM`

#### Scenario: Disagreement at a long lead time stays MEDIUM

- **WHEN** a verdict a day before dusk, with a fresh and complete forecast, would have a confidence of `50` without alternates, and an alternate makes the band `DISAGREE`
- **THEN** `confidence.value` is `40` and `confidence.band` is `MEDIUM`

### Requirement: Agreement changes no gate, score or verdict

Agreement SHALL change no gate, no score and no verdict value.

#### Scenario: Mixed agreement lowers confidence

- **WHEN** two verdicts are produced for the same pier and instant from snapshots that differ only in the alternate's values, so one is `AGREE` and the other `MIXED`
- **THEN** the `MIXED` document's `confidence.value` is lower than the `AGREE` document's
- **AND** the two documents have the same `verdict` and `score`

### Requirement: An alternate's issue time never changes confidence

An alternate's issue time SHALL NOT change confidence.

#### Scenario: A stale alternate does not lower confidence

- **WHEN** two verdicts are produced for the same pier and instant from snapshots that differ only in the issue time of a `cloud_cover` alternate
- **THEN** the two documents are byte-identical

### Requirement: A cloud-cover agreement entry adds exactly one reason line

When `agreement.cloud_cover` is present, the `reasons` list SHALL carry exactly
one line `Cloud agreement <agree|mixed|disagree>: <n> providers, spread <spread>
points.`. `<n>` is the number of providers listed and `<spread>` the document's
spread. When the band is `MIXED` or `DISAGREE`, the line SHALL end with `
Confidence lowered.`. When `agreement` is empty, no such line SHALL appear.

#### Scenario: A scored verdict names the agreement

- **WHEN** a verdict is `GO` with `agreement.cloud_cover` of band `AGREE`, spread `8` and two providers
- **THEN** `reasons` contains `Cloud agreement agree: 2 providers, spread 8 points.`
- **AND** it follows the `Score N/100.` line

#### Scenario: One provider adds no line

- **WHEN** a verdict is produced from a snapshot whose `cloud_cover` series has no alternate
- **THEN** no reason line begins with `Cloud agreement`

### Requirement: The cloud agreement line comes after the gate and score lines

The cloud agreement line SHALL come after the lines that name the gate or
itemize the score, on a gated `NO-GO` as well as a scored verdict, so every
earlier line keeps its position.

#### Scenario: A gated verdict names the agreement

- **WHEN** a verdict is `NO-GO` for an overcast dark window and `agreement.cloud_cover` is `DISAGREE` with spread `60` across two providers
- **THEN** `reasons` names the overcast gate first
- **AND** then contains `Cloud agreement disagree: 2 providers, spread 60 points. Confidence lowered.`

### Requirement: Variables the timeline does not show leave the document unchanged

The timeline does not show these variables in the conditions: today,
`aerosol_optical_depth`, `pm2_5`, `column_water_vapour` and the seeing column's
36 variables. The verdict document SHALL NOT depend on them. No gate, score,
reason, confidence, agreement, timeline entry or timeline hour SHALL change with
their presence, absence or values. A value derived from them reaches the
document only as a shown variable's series in the snapshot, such as the computed
source's `transparency` and `seeing`.

#### Scenario: Air-quality series leave the document byte-identical

- **WHEN** two verdicts are produced for the same pier and pinned instant, from snapshots that differ only in whether `aerosol_optical_depth` and `pm2_5` series are present and in their values
- **THEN** the two serialized documents are byte-identical

#### Scenario: Air-quality series alone yield the empty-conditions document

- **WHEN** a verdict is produced from a snapshot whose only series are `aerosol_optical_depth` and `pm2_5`
- **THEN** the serialized document is byte-identical to the one produced for the same pier and instant from the empty conditions value
- **AND** its `timeline` is an empty list

#### Scenario: A column water vapour series leaves the document byte-identical

- **WHEN** two verdicts are produced for the same pier and pinned instant, from snapshots that differ only in whether a `column_water_vapour` series is present and in its values
- **THEN** the two serialized documents are byte-identical

#### Scenario: Seeing-column series leave the document byte-identical

- **WHEN** two verdicts are produced for the same pier and pinned instant, from snapshots that differ only in whether the seeing column's series are present and in their values
- **THEN** the two serialized documents are byte-identical

## REMOVED Requirements

### Requirement: Confidence is present and banded

**Reason**: It bundled four behaviors. It is split into "Confidence is always
present with a band and a value from 0 to 100", "Confidence rises as the
evaluation instant approaches the dark window", "Confidence falls when the
forecast is stale, data is missing or forecasts disagree" and "A NO-GO with no
dark window has full confidence". Its 4 scenarios move word for word. No
scenario is added.

**Migration**: Nothing changes for users or code. Later changes MODIFY the new
requirements.

### Requirement: The document carries an hourly timeline

**Reason**: It bundled three behaviors. It is split into "The timeline holds one
entry per hour a shown variable's filled series covers", "Hours that only an
alternate or a hidden variable covers add no timeline entry" and "The timeline
is empty, never absent, when no provider returned rows". Its 5 scenarios move
word for word. No scenario is added.

**Migration**: Nothing changes for users or code. Later changes MODIFY the new
requirements.

### Requirement: A timeline entry has a fixed flat shape

**Reason**: It bundled two behaviors. It is split into "A timeline entry carries
exactly eighteen keys in a fixed order" and "A timeline entry's time is the top
of the hour". Its 3 scenarios move word for word. One scenario is added.

**Migration**: Nothing changes for users or code. Later changes MODIFY the new
requirements.

### Requirement: The document carries cloud agreement

**Reason**: It bundled two behaviors. It is split into "The agreement object has
a cloud-cover entry only when two providers share a scored hour" and "The
cloud-cover agreement entry holds a band, a spread and its providers". Its 6
scenarios move word for word. No scenario is added.

**Migration**: Nothing changes for users or code. Later changes MODIFY the new
requirements.

### Requirement: Cloud agreement is the clarity-weighted mean gap over the scored window

**Reason**: It bundled three behaviors. It is split into "An hour's cloud gap is
the highest reading minus the lowest", "The mean cloud gap weights each hour by
its coverage and its clearest reading" and "The agreement band is decided on the
rounded spread". Its 6 scenarios move word for word. No scenario is added.

**Migration**: Nothing changes for users or code. Later changes MODIFY the new
requirements.

### Requirement: Confidence falls with low agreement

**Reason**: It bundled four behaviors. It is split into "Confidence is
multiplied by an agreement factor set by the band", "Agreement alone never takes
confidence below MEDIUM", "Agreement changes no gate, score or verdict" and "An
alternate's issue time never changes confidence". Its 6 scenarios move word for
word. No scenario is added.

**Migration**: Nothing changes for users or code. Later changes MODIFY the new
requirements.

### Requirement: Reasons name the agreement

**Reason**: It bundled two behaviors. It is split into "A cloud-cover agreement
entry adds exactly one reason line" and "The cloud agreement line comes after
the gate and score lines". Its 3 scenarios move word for word. No scenario is
added.

**Migration**: Nothing changes for users or code. Later changes MODIFY the new
requirements.

### Requirement: Variables the timeline does not show never change the document

**Reason**: It ran past 500 characters. It states one behavior, so it is
replaced by "Variables the timeline does not show leave the document unchanged",
which says the same in tighter wording. Its 4 scenarios move word for word. No
scenario is added.

**Migration**: Nothing changes for users or code. Later changes MODIFY the new
requirements.
