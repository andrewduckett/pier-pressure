# night-verdict Specification

## Purpose

The night-verdict capability produces a single, deterministic per-pier verdict document that answers "is tonight worth setting up for" as a go/no-go decision with a score, a confidence, and human-readable reasons. This change establishes the document contract and deterministic emission with stubbed decision values; later milestones fill the same contract with real astronomy, conditions, and target ranking.

## Requirements

### Requirement: Verdict document structure

The system SHALL produce, for a single configured pier, a verdict document containing at least these fields: a pier identifier, a generation timestamp, a `verdict` value, a `score` value, a `confidence` value, a `reasons` list, a `targets` list, a `dark_window` value, and a `moon` value. The document SHALL be serializable to JSON so downstream adapters and tests can consume it without access to internal state.

#### Scenario: Document contains all required fields

- **WHEN** a verdict is produced for a valid pier configuration
- **THEN** the resulting document contains a pier identifier, a generation timestamp, a `verdict`, a `score`, a `confidence`, a `reasons` list, a `targets` list, a `dark_window`, and a `moon`
- **AND** the document can be serialized to JSON and read back with the same field values

### Requirement: Verdict value is a bounded enumeration

The `verdict` field SHALL be exactly one of `GO`, `MAYBE`, or `NO-GO`. No other value is permitted.

#### Scenario: Verdict is one of the allowed values

- **WHEN** a verdict is produced for a valid pier configuration
- **THEN** the `verdict` field equals `GO`, `MAYBE`, or `NO-GO`

### Requirement: Score is banded and nulled on gated NO-GO

The `score` field SHALL be an integer from 0 to 100 inclusive when the verdict is `GO` or `MAYBE`. When the verdict is `NO-GO` because a hard gate failed, the `score` field SHALL be null, so a dealbreaker is never presented as a numeric near-miss.

#### Scenario: Go or maybe carries a bounded score

- **WHEN** a verdict is produced and the verdict is `GO` or `MAYBE`
- **THEN** the `score` field is an integer between 0 and 100 inclusive

#### Scenario: Gated no-go carries a null score

- **WHEN** a verdict is produced and the verdict is `NO-GO` due to a failed hard gate
- **THEN** the `score` field is null

### Requirement: Reasons explain the verdict

The `reasons` field SHALL be a non-empty list of human-readable strings that itemize the terms behind the verdict, so the explanation follows from the decision itself. When the verdict is a gated NO-GO, the reasons SHALL name the failing gate. When gates pass, the reasons SHALL itemize the terms that shaped the score.

#### Scenario: Every verdict carries at least one reason

- **WHEN** a verdict is produced for a valid pier configuration
- **THEN** the `reasons` list contains at least one non-empty human-readable string

#### Scenario: A gated no-go names the failing gate

- **WHEN** a verdict is `NO-GO` because a hard gate failed
- **THEN** the `reasons` list names the gate that failed

### Requirement: Deterministic emission

Given the same pier configuration and the same evaluation instant, the system SHALL produce structurally identical verdict documents on repeated runs. The only field permitted to vary with wall-clock time is the generation timestamp, and it SHALL be derivable from an injectable clock so tests can pin it. This guarantees the decision core is reproducible and testable off Home Assistant.

#### Scenario: Same inputs yield the same document

- **WHEN** a verdict is produced twice for the same pier configuration and the same pinned evaluation instant
- **THEN** the two documents are identical in every field, including the generation timestamp

#### Scenario: Verdict does not read ambient wall-clock time directly

- **WHEN** a verdict is produced with a pinned evaluation instant supplied by the caller
- **THEN** the generation timestamp equals the pinned instant rather than the ambient system time

### Requirement: Pier configuration validation

The system SHALL require a pier configuration consisting of an identifier and a location (latitude, longitude, elevation). Latitude SHALL be within -90 to 90 degrees and longitude within -180 to 180 degrees. When required fields are missing or out of range, the system SHALL report a configuration error and SHALL NOT emit a verdict document, so a malformed site can never yield a silently wrong verdict.

#### Scenario: Valid single-pier configuration is accepted

- **WHEN** a configuration provides an identifier and a location with latitude in [-90, 90] and longitude in [-180, 180]
- **THEN** a verdict document is produced for that pier

#### Scenario: Missing or out-of-range configuration is rejected

- **WHEN** a configuration omits a required field or provides a latitude or longitude outside its valid range
- **THEN** the system reports a configuration error
- **AND** no verdict document is produced for that pier

#### Scenario: One invalid pier does not disable valid piers

- **WHEN** a configuration contains more than one pier and at least one pier is invalid while at least one is valid
- **THEN** each invalid pier is reported as a configuration error and produces no verdict document
- **AND** each valid pier still produces a verdict document

#### Scenario: A configuration with no valid pier is a hard failure

- **WHEN** a configuration contains no valid pier
- **THEN** the system reports a configuration error and exits rather than running with nothing to publish

### Requirement: Timeline altitudes are computed offline at fixed precision

Each entry's `sun_altitude` and `moon_altitude` SHALL be the geometric altitude of the body's centre in degrees at the entry's `time`, computed with no network access from the bundled ephemeris, rounded to the document's fixed angle precision, and present for every entry.

#### Scenario: Altitudes are byte-identical across runs

- **WHEN** a verdict is produced twice for the same pier, pinned instant and conditions with no network available
- **THEN** every entry's `sun_altitude` and `moon_altitude` are rounded to the document's fixed angle precision
- **AND** the two serialized timelines are byte-identical

#### Scenario: Altitudes agree with the dark window

- **WHEN** an entry's `time` falls inside the dark window
- **THEN** its `sun_altitude` is at or below minus 18.0 degrees after rounding

#### Scenario: Altitudes agree with the single-instant astronomy

- **WHEN** the sun and moon altitude for an hour are computed for the timeline and again one instant at a time with the same observer
- **THEN** the two agree at the document's fixed angle precision

### Requirement: The timeline is evidence beside the verdict

The timeline SHALL be filled whenever a provider returned rows for a variable the timeline shows, whether or not the selected night has a dark window. It SHALL NOT change the verdict, the score, the confidence, the reasons or any other existing field. It carries no verdict of its own: the verdict judges the one night the dark window names, however far the timeline reaches.

#### Scenario: The timeline fills without a dark window

- **WHEN** a verdict is produced for a pier whose selected night has no dark window and a provider returned rows
- **THEN** the `timeline` holds one entry per returned hour
- **AND** the document with `timeline` removed equals the document produced for the same pier and instant from the empty conditions value

#### Scenario: Hours outside the dark window change no other field

- **WHEN** a verdict is produced twice for the same pier and instant, once with the providers' hours limited to the dark window and once with extra hours before and after it
- **THEN** the two documents differ only in `timeline`

### Requirement: Freshness follows the cloud-cover series

The freshness that confidence reads SHALL be the issue time of the `cloud_cover`
series: the time the provider that filled cloud cover gave for its data. The
issue time of any other series SHALL NOT change the confidence. When no series
fills cloud cover, freshness SHALL be at its floor.

#### Scenario: A stale seeing series does not lower confidence

- **WHEN** two verdicts are produced for the same pier and instant from snapshots that differ only in the issue time of the `seeing` series
- **THEN** the two documents are byte-identical

#### Scenario: A stale cloud series lowers confidence

- **WHEN** two verdicts are produced for the same pier and instant from snapshots that differ only in the issue time of the `cloud_cover` series, one issued an hour before the instant and one eleven hours before
- **THEN** the confidence value of the second is lower than the first

### Requirement: Entry weather values carry the filling provider's reading for the hour

`temperature` and `dew_point` SHALL be degrees Celsius, `humidity` and `precipitation_probability` percent, `wind_speed` km/h and `wind_direction` degrees. Each SHALL be carried exactly as its series holds it for that hour, with no rounding or conversion. Each SHALL be null when its series lacks the hour or the value, or no provider filled it.

#### Scenario: Weather values pass through unchanged

- **WHEN** the weather series hold, for an hour, a temperature of `12.3`, a dew point of `9.8`, a humidity of `85.0`, a wind speed of `14.2`, a wind direction of `230.0` and a precipitation probability of `35.0`
- **THEN** that entry's `temperature` is `12.3`, `dew_point` `9.8`, `humidity` `85.0`, `wind_speed` `14.2`, `wind_direction` `230.0` and `precipitation_probability` `35.0`

#### Scenario: An hour the weather series lack carries null weather values

- **WHEN** an hour is present in the `seeing` and `transparency` series but absent from every weather series
- **THEN** that entry's six weather keys are all null
- **AND** its `seeing` and `transparency` carry their series' values

#### Scenario: A weather value the provider lacks is null on its own

- **WHEN** the provider that filled the weather series reports every weather variable but the dew point for an hour
- **THEN** that entry's `dew_point` is null
- **AND** its other five weather keys carry the reported values

### Requirement: Entry values carry each series' reading for the hour

`cloud_cover`, `cloud_low`, `cloud_mid` and `cloud_high` SHALL be percent and `wind_gust` km/h, each carried exactly as its series holds it for that hour, with no rounding. `seeing` and `transparency` SHALL be quality in 0 to 1 where 1 is best, from their series for that hour, rounded to two decimal places. Each of these keys SHALL be null when its series lacks the hour or the value, or no provider filled it.

#### Scenario: An hour one series lacks carries null for that variable

- **WHEN** an hour is present in the `seeing` and `transparency` series but absent from the `cloud_cover`, cloud-layer and `wind_gust` series
- **THEN** that entry's `cloud_cover`, `cloud_low`, `cloud_mid`, `cloud_high` and `wind_gust` are null
- **AND** its `seeing` and `transparency` carry their series' values
- **AND** its `sun_altitude` and `moon_altitude` are present

#### Scenario: Cloud and wind values pass through unchanged

- **WHEN** the `cloud_cover` series holds `37.0` and the `wind_gust` series `23.4` for an hour
- **THEN** that entry's `cloud_cover` is `37.0` and its `wind_gust` is `23.4`

#### Scenario: Seeing and transparency are emitted at two decimal places

- **WHEN** the `seeing` series holds a quality of four sevenths for an hour
- **THEN** that entry's `seeing` is `0.57`

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

### Requirement: Reasons name the first dew or frost hour

When every hard gate passes and the pier's dew margin is above zero, `reasons` SHALL carry at most one dew or frost line. It names the first scored hour whose spread, temperature minus dew point in °C, is strictly under the margin. The line SHALL read `Frost likely from <time>.` when that hour is at or below 0 °C, else `Dew likely from <time>.`. `<time>` is the hour's start in the document's UTC timestamp format. With no qualifying hour, no such line SHALL appear.

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

### Requirement: The verdict judges the scored window

The verdict SHALL judge the **scored window**: the part of the dark window
from the evaluation instant to `dark_window.end`.

`dark_window.end` has two meanings. On an ordinary night it is astronomical
dawn. In continuous polar night it is the end of the local solar day that
anchors the dark window. The rules that read `dark_window.end` work the same
for both.

The `dark_window` field SHALL keep the whole night and SHALL NOT change meaning.

#### Scenario: In continuous polar night, the scored window ends with the solar day

- **WHEN** a verdict is produced during continuous polar night, at an evaluation instant inside the dark window
- **THEN** `scored_window.end` equals `dark_window.end`
- **AND** `scored_window.start` equals `generated_at`

### Requirement: Before astronomical dusk, the scored window is the whole dark window

Before astronomical dusk, the scored window SHALL equal the dark window.

#### Scenario: Before dusk, the scored window is the whole night

- **WHEN** a verdict is produced at an evaluation instant before astronomical dusk
- **THEN** `scored_window.start` equals `dark_window.start`
- **AND** `scored_window.end` equals `dark_window.end`

### Requirement: Once the night has started, the scored window starts at the scoring instant

The **scoring instant** is the evaluation instant with its sub-second part
removed, the same whole second as `generated_at`. Once the night has started,
the scored window SHALL start at the scoring instant, so hours that have passed
no longer count.

#### Scenario: Mid-session, the scored window starts at the generation second

- **WHEN** a verdict is produced at an evaluation instant inside the dark window, with a fractional second
- **THEN** `scored_window.start` equals `generated_at`
- **AND** `scored_window.end` equals `dark_window.end`

### Requirement: The gates, the score and the completeness part of confidence run over the scored window

These rules SHALL all run over the scored window:

- the overcast gate and the wind gate;
- the wind-coverage check and the cloud-availability check;
- the score and each of its terms;
- the completeness part of confidence.

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

### Requirement: The document carries the scored window beside the dark window

The document SHALL carry a `scored_window` object with a `start` and an
`end`, in the same shape as `dark_window`.

- Both SHALL be null when there is no dark window.
- `scored_window.end` SHALL equal `dark_window.end`.
- `scored_window.start` SHALL be the later of `dark_window.start` and
  `generated_at`, and never later than `scored_window.end`.

`generated_at` is the scoring instant, so the emitted span is the span the
verdict judged.

#### Scenario: The scored window is null without a dark window

- **WHEN** a verdict is produced for a selected night that has no dark window
- **THEN** `scored_window.start` and `scored_window.end` are both null

### Requirement: An empty scored window arises only in the last partial second of the dark window

The scored window's start SHALL never be later than its end. When the
scoring instant equals `dark_window.end`, the scored window is empty.

An empty scored window can only arise in the last partial second of the
window. Three facts combine:

- `dark_window.end` is the exact end instant, floored to a whole second.
- The scoring instant is the evaluation instant floored to a whole second.
- The selected window ends at the first exact end that qualifies against the
  evaluation instant.

#### Scenario: In the floored dawn second, the scored window closes on the end of the dark window

- **WHEN** a verdict is produced at an evaluation instant inside the whole second that `dark_window.end` names, before the exact dawn crossing
- **THEN** `scored_window.start` and `scored_window.end` both equal `dark_window.end`

### Requirement: On an ordinary night, an instant on the exact dawn crossing still selects the ending night

On an ordinary night, a dawn crossing at or after the evaluation instant
SHALL qualify as the exact end of the selected window, so an instant exactly on
the crossing still selects the ending night. So the scoring instant equals
`dark_window.end` only when the evaluation instant lies in the floored second
that `dark_window.end` names and the selection still picks that window: up to
and including the exact crossing.

#### Scenario: A verdict after the exact dawn crossing judges the next night

- **WHEN** a verdict is produced at an evaluation instant after the exact astronomical dawn crossing
- **THEN** `dark_window` is the next night's window
- **AND** `scored_window` equals `dark_window`

#### Scenario: An instant exactly on the dawn crossing still judges the ending night

- **WHEN** a verdict is produced at an evaluation instant exactly on the exact astronomical dawn crossing
- **THEN** `dark_window.end` is that dawn crossing, floored to a whole second
- **AND** `scored_window.start` equals `scored_window.end`

### Requirement: In continuous polar night, an instant on the exact solar-day boundary selects the next solar day

In continuous polar night, only a solar-day boundary after the evaluation
instant SHALL qualify as the exact end of the selected window, so an instant
exactly on the boundary selects the next solar day. So the scoring instant
equals `dark_window.end` only when the evaluation instant lies in the floored
second that `dark_window.end` names and the selection still picks that window:
up to but not including the exact boundary.

#### Scenario: In continuous polar night, the exact solar-day boundary starts the next window

- **WHEN** a verdict is produced during continuous polar night, at an evaluation instant exactly on the local solar-day boundary
- **THEN** `dark_window` is the next solar day's window
- **AND** `scored_window` equals `dark_window`

#### Scenario: In continuous polar night, the floored second before the boundary is empty

- **WHEN** a verdict is produced during continuous polar night, at an evaluation instant in the whole second that `dark_window.end` names, before the exact boundary, with cloud data available
- **THEN** `scored_window.start` equals `scored_window.end`
- **AND** the `verdict` is `MAYBE` with a `score` of 0

### Requirement: An empty scored window gives MAYBE with a score of 0

When the scored window is empty, the verdict SHALL be `MAYBE` with a `score`
of 0 and a reason that no dark time remains. It SHALL NOT fail the overcast
gate, SHALL NOT be `GO`, and SHALL NOT report that conditions are unavailable.

#### Scenario: A verdict in the last partial second of the night has no usable time left

- **WHEN** a verdict is produced at an evaluation instant in the whole second that `dark_window.end` names, up to and including the exact dawn crossing, with cloud data available
- **THEN** `scored_window.start` equals `scored_window.end`
- **AND** the `verdict` is `MAYBE`
- **AND** the `score` is 0
- **AND** a reason states that no dark time remains
- **AND** no reason states that conditions are unavailable

### Requirement: Less than an hour of dark time caps the verdict at MAYBE

A short span is not worth setting up for, however clear it is. When the
scored window is shorter than 60 minutes, the verdict SHALL NOT be `GO`. This
holds whether the window is narrowed or is a whole short night. The gates and
the score still run as usual. A verdict that would otherwise be `GO` SHALL be
`MAYBE`, with a reason that the scored window holds less than an hour of dark
time. The reason SHALL read correctly before dusk and during the night, so it
SHALL NOT say that time "remains".

#### Scenario: Less than an hour of dark time caps the verdict at MAYBE

- **WHEN** a verdict is produced at an evaluation instant 30 minutes before `dark_window.end`, the remaining sky is clear, and the score is at or above the go-threshold
- **THEN** the `verdict` is `MAYBE`
- **AND** the `score` is the computed score, not 0
- **AND** a reason states that the scored window holds less than an hour of dark time

#### Scenario: A whole night shorter than an hour is capped the same way

- **WHEN** a verdict is produced before dusk for a night whose dark window is 50 minutes long, the sky is clear, and the score is at or above the go-threshold
- **THEN** the `verdict` is `MAYBE`
- **AND** a reason states that the scored window holds less than an hour of dark time

#### Scenario: An hour or more left can still be GO

- **WHEN** a verdict is produced at an evaluation instant 60 minutes before `dark_window.end`, the remaining sky is clear, no wind limit is configured, and the score is at or above the go-threshold
- **THEN** the `verdict` is `GO`

### Requirement: The dark window is the astronomical night selected from the evaluation instant

The `dark_window` field SHALL always be present and SHALL contain a `start`
and an `end`. It represents the astronomical-night boundary (astronomical dusk
to astronomical dawn, defined by the sun's centre crossing -18 degrees
altitude) for the night **selected relative to the evaluation instant**
supplied by the injectable clock — not for a calendar date. In every case,
including both extreme-latitude cases, the field SHALL be present rather than
omitted.

#### Scenario: A real astronomical-night window is computed when night exists

- **WHEN** a verdict is produced at a mid-latitude site while it is daytime, for a date whose location has a normal astronomical night
- **THEN** `dark_window.start` is the UTC instant of the next astronomical dusk at or after the evaluation instant (sun descending through -18 degrees)
- **AND** `dark_window.end` is the UTC instant of the following astronomical dawn (sun ascending through -18 degrees)
- **AND** `dark_window.start` is strictly before `dark_window.end`

### Requirement: The selected night is the one whose dawn comes first at or after the evaluation instant

The selected night SHALL be the one whose astronomical dawn is the first
astronomical dawn at or after the evaluation instant: if the instant falls
during astronomical night, the current night is selected (its dusk already
past, its dawn ahead); otherwise the next upcoming night is selected. This
makes the answer to "is tonight worth setting up for" correct whether the
question is asked in the afternoon or after midnight mid-session.

#### Scenario: The current night is selected when the instant is already dark

- **WHEN** a verdict is produced at an evaluation instant that falls within astronomical night (for example, after local midnight, mid-session)
- **THEN** `dark_window.end` is the first astronomical dawn at or after the evaluation instant
- **AND** `dark_window.start` is the astronomical dusk immediately preceding that dawn (already in the past relative to the evaluation instant)

### Requirement: A non-null dark window starts strictly before it ends

When the selected night exists, `start` and `end` SHALL be the UTC instants
of its astronomical dusk and dawn, and `start` SHALL be strictly before `end`.
If truncation to whole seconds would collapse a grazing, sub-second
astronomical night so that `start` is not strictly before `end`, the window
SHALL be reported as null — such a night provides no usable darkness — so a
non-null window always has `start` strictly before `end`.

#### Scenario: A grazing night that whole seconds collapse is reported as null

- **WHEN** the selected night's astronomical dusk and dawn fall inside the same whole second, so truncating both to whole seconds would make `start` equal `end`
- **THEN** `dark_window.start` and `dark_window.end` are both null

### Requirement: In continuous astronomical night, the dark window is non-null and covers the dark span

In **continuous astronomical night**, when the sun never rises above -18
degrees across the searched span (as in high-latitude winter, the best
observing season), `dark_window` SHALL be non-null and cover the dark span, so
a polar-winter night is never mistaken for "no night".

#### Scenario: Continuous astronomical night yields a non-null window

- **WHEN** a verdict is produced for a location and date where the sun never rises above -18 degrees across the searched span
- **THEN** `dark_window.start` and `dark_window.end` are both non-null and cover the dark span
- **AND** `dark_window.start` is strictly before `dark_window.end`
- **AND** two verdicts produced at different evaluation instants within the same anchored period yield the same `dark_window.start` and `dark_window.end`

### Requirement: The continuous-night dark window is anchored to a stable boundary

In continuous astronomical night, the dark window SHALL be anchored to a
stable boundary derived from the evaluation instant (not the moving instant
itself), so successive recomputes within the same period yield the same window
rather than one that slides forward on each poll.

#### Scenario: Two recomputes in one continuous-night period give the same window

- **WHEN** two verdicts are produced during continuous astronomical night, at evaluation instants eight hours apart within the same local solar day
- **THEN** both verdicts have the same `dark_window.start` and the same `dark_window.end`

### Requirement: In continuous non-night, the dark window's start and end are null

Continuous non-night SHALL be handled distinctly from continuous
astronomical night, because the underlying twilight search reports no
crossings in both. In **continuous non-night**, when the sun never falls below
-18 degrees across the searched span (as in high-latitude summer),
`dark_window.start` and `dark_window.end` SHALL both be null, since there is no
astronomical darkness.

#### Scenario: Continuous non-night yields a null window

- **WHEN** a verdict is produced for a location and date where the sun never falls below -18 degrees across the searched span
- **THEN** `dark_window.start` and `dark_window.end` are both null
- **AND** the field is present rather than omitted

### Requirement: Reasons keep their whole-night wording unless the scored window is narrowed

The scored window is **narrowed** when `scored_window.start` is later than
`dark_window.start`. That is the test for every rule about a narrowed scored
window. An evaluation instant in the same whole second as dusk is not narrowed:
its scored window is the whole night, so the whole-night wording is true.

When the scored window is not narrowed, no span line is present, and the
reasons SHALL keep their whole-night wording.

#### Scenario: A verdict before dusk keeps the whole-night wording

- **WHEN** a scored verdict is produced at an evaluation instant before astronomical dusk
- **THEN** the cloud reason states the usable share of the dark window
- **AND** no reason states a scored span

#### Scenario: A verdict in the dusk second keeps the whole-night wording

- **WHEN** a scored verdict is produced at an evaluation instant in the same whole second as `dark_window.start`
- **THEN** `scored_window.start` equals `dark_window.start`
- **AND** no reason states a scored span

### Requirement: A narrowed scored window puts a span line first in the reasons

When the scored window is narrowed, every verdict with a dark window SHALL
carry a span line as its first reason. The span line states the scored
window's start and end as UTC dates and times, to the second, in the same
format as the document's timestamps. This holds for a scored verdict, a gated
`NO-GO`, a missing-cloud `MAYBE`, and an empty scored window.

#### Scenario: A mid-session missing-cloud verdict names the span it judged

- **WHEN** a verdict is produced at an evaluation instant at least one second after `dark_window.start` and inside the dark window, with no cloud data for the scored window
- **THEN** the first reason states the start and end of the scored window
- **AND** a later reason states that conditions are unavailable

### Requirement: Over a narrowed scored window, reasons speak only of the rest of the night

When the scored window is narrowed, no reason SHALL make a claim about the
whole night, and no reason SHALL claim more than the forecast covers. On a
scored verdict, the cloud reason SHALL state the usable share of the remaining
night. A failed overcast gate SHALL say that the forecast shows no usably clear
sky for the rest of the night. A failed wind gate SHALL say the gust falls in
the rest of the night.

#### Scenario: A mid-session scored verdict names the span it judged

- **WHEN** a scored verdict is produced at an evaluation instant at least one second after `dark_window.start` and inside the dark window
- **THEN** the first reason states the start and end of the scored window, each as the same UTC date and time string the document emits for `scored_window.start` and `scored_window.end`
- **AND** a reason states the usable share of the remaining night

#### Scenario: A mid-session gated verdict names the span it judged

- **WHEN** a `NO-GO` verdict is produced at an evaluation instant at least one second after `dark_window.start` and inside the dark window, because the overcast gate or the wind gate failed
- **THEN** the first reason states the start and end of the scored window
- **AND** a later reason names the failing gate and refers to the rest of the night, not the whole dark window
- **AND** when the gate is overcast and some remaining hours lack cloud data, the reason claims no more than that the forecast shows no usably clear sky

### Requirement: The score reflects the extent and quality of the scored window's usable dark time

The verdict SHALL judge the night by how much usable dark time the scored
window offers, not by a single hour or a flat average. The score SHALL reflect
the extent and quality of the usable portion. Terms other than cloud SHALL be
weighted toward the hours that are usably clear, so a term's value during a
clouded-out hour does not distort the verdict.

#### Scenario: More usable clear darkness scores higher

- **WHEN** two nights are identical except that one has more of its scored window usably clear, by enough to change the rounded score, the moon is down throughout both, and no high-cloud component is present
- **THEN** the night with more usable clear darkness has the higher score

### Requirement: A scored window with some usably clear hours is not gated as overcast

A scored window with some usably clear hours SHALL NOT be gated as
overcast.

#### Scenario: A partly clear night is not gated as overcast

- **WHEN** part of the scored window is usably clear and the rest is overcast
- **THEN** the overcast gate does not fail
- **AND** the `score` is above 0
- **AND** the `score` is at most the usably clear share of the scored window, scaled to 100 and rounded

### Requirement: Usable dark time is normalized to the scored window's actual duration

The measure of usable dark time SHALL be normalized to the actual duration
of the scored window. A window whose start and end do not fall on whole-hour
boundaries still yields a score within 0 to 100.

#### Scenario: A window that does not align to whole hours still yields a bounded score

- **WHEN** a verdict is produced for a scored window whose start and end do not fall on whole-hour boundaries
- **THEN** the `score` is an integer between 0 and 100 inclusive

### Requirement: Hours without cloud data count as neither clear nor overcast

Hours of the scored window for which cloud data is unavailable SHALL count
as neither clear nor overcast. They SHALL NOT trigger the overcast gate and
SHALL NOT add usable dark time to the score, so partial cloud coverage lowers
the score rather than inflating it or gating the night.

#### Scenario: Hours without cloud data lower the score without gating

- **WHEN** two nights are identical and clear wherever cloud data exists, but one has cloud data covering the whole scored window and the other only covering half of it
- **THEN** neither night fails the overcast gate
- **AND** the night with cloud data for only half the window has the lower score

### Requirement: The moon object carries its illumination and phase

The verdict document SHALL contain a `moon` object with `illumination` (the
illuminated fraction, a number from 0 to 1) and `phase` (a phase name drawn
from a fixed enumeration of the eight standard phases: new, waxing crescent,
first quarter, waxing gibbous, full, waning gibbous, last quarter, waning
crescent). This object gives later milestones the single moon fact that changes
a night's verdict — a bright moon above the horizon during darkness — without
reshaping the document.

#### Scenario: Moon object carries illumination and a bounded phase name

- **WHEN** a verdict is produced for a valid pier configuration
- **THEN** `moon.illumination` is a number between 0 and 1 inclusive
- **AND** `moon.phase` equals one of the eight enumerated phase names

### Requirement: The moon object reports whether and when the moon is up during the dark window

The `moon` object SHALL also contain `up_during_dark` (a boolean, or null
when there is no dark window, indicating whether the moon is above the horizon
at any point during the dark window), and `rise` and `set` (the UTC instants of
moonrise and moonset that fall within the dark window, or null when the moon
does not rise/set within it or when there is no dark window).

#### Scenario: Moon above-horizon behaviour is reported across an existing dark window

- **WHEN** a verdict is produced for a location and date that has an astronomical-night window
- **THEN** `moon.up_during_dark` is a boolean indicating whether the moon is above the horizon at any point within `dark_window.start`..`dark_window.end`
- **AND** when `moon.rise` or `moon.set` is non-null, that instant falls within `dark_window.start`..`dark_window.end`

#### Scenario: Across-window moon fields are null when there is no astronomical night

- **WHEN** a verdict is produced for a location and date with no astronomical night (continuous non-night)
- **THEN** `moon.up_during_dark`, `moon.rise`, and `moon.set` are all null
- **AND** `moon.illumination` and `moon.phase` remain present

### Requirement: Moon horizon crossings use the moon's geometric centre at 0 degrees

"Above the horizon", "moonrise", and "moonset" SHALL be defined by the moon's
**geometric centre crossing 0 degrees altitude** (no atmospheric-refraction or
lunar-radius correction), so the boundary is pinned and does not vary with a
library's refraction defaults.

#### Scenario: Moonrise and moonset are the geometric centre crossing 0 degrees

- **WHEN** a verdict is produced for a night in which the moon rises or sets within the dark window
- **THEN** `moon.rise` or `moon.set` is the instant the moon's geometric centre crosses 0 degrees altitude, with no atmospheric-refraction or lunar-radius correction

### Requirement: Astronomical fields are computed offline from bundled data

The system SHALL compute the astronomical fields of the verdict document (the
night window and the moon information) without any network access at runtime,
using ephemeris and timescale data bundled with the system, so verdict
production is fully self-contained and offline. This keeps Home Assistant and
external services non-load-bearing for correctness.

#### Scenario: Verdict production performs no runtime network access

- **WHEN** a verdict is produced with no network available
- **THEN** production succeeds and the document's astronomical fields are populated (or null where no astronomical night exists)
- **AND** producing the verdict makes no outbound network request

### Requirement: Loading the bundled astronomical data raises no expiry warning

Loading the bundled ephemeris and timescale data SHALL raise no warning that
a bundled data file has expired, whatever the current date. Such a warning
tells users to expect computation errors, so it must not appear for data the
system does not read.

#### Scenario: Ephemeris loads with no warning after a bundled file's expiry date

- **WHEN** the bundled ephemeris is loaded on a date after every bundled data file's recorded expiry date
- **THEN** loading succeeds
- **AND** no warning is raised

### Requirement: A verdict outside the bundled ephemeris's range fails with an error

Producing a verdict for an evaluation instant outside the date range the
bundled ephemeris covers SHALL fail with an error that names the covered
range, and SHALL NOT emit a verdict document. The ephemeris's own range,
not a warning, is what guards against computing from data that has run out.

#### Scenario: Evaluation instant after the ephemeris's coverage ends

- **WHEN** a verdict is produced for the pinned evaluation instant 2060-01-01T22:00:00Z
- **THEN** production fails with an error stating the ephemeris covers dates through 2053-10-09
- **AND** no verdict document is returned

### Requirement: Astronomical numbers and document timestamps have a fixed precision from construction

Numeric astronomical outputs SHALL be emitted at a fixed, defined decimal
precision, and every timestamp in the document (`generated_at` as well as
`dark_window.start`/`end` and `moon.rise`/`set`) SHALL be emitted with its
sub-second component removed (whole seconds). This precision SHALL be applied
when the document is constructed (not only when it is serialized), so the
in-memory document and its JSON form agree and a document survives a
serialize-then-read-back round trip unchanged.

#### Scenario: Astronomical numeric and time fields are emitted at a fixed precision

- **WHEN** a verdict is produced twice for the same pier configuration and the same pinned evaluation instant
- **THEN** every astronomical numeric field (such as `moon.illumination`) is emitted rounded to the defined fixed precision
- **AND** every document timestamp (`generated_at`, `dark_window.start`/`end`, `moon.rise`/`set`) is emitted with no sub-second component
- **AND** the two serialized documents are byte-identical in those fields

### Requirement: Repeated runs on one platform yield byte-identical astronomical values

For a given platform and the pinned library set, the same pier configuration
and the same pinned evaluation instant SHALL yield byte-identical serialized
values on repeated runs; cross-platform identity is guarded by pinned-value
tests in CI rather than asserted as an absolute guarantee. This preserves the
deterministic-emission guarantee once real sky math is introduced.

#### Scenario: Two offline runs give byte-identical astronomical fields

- **WHEN** a verdict is produced twice, offline, on one platform, for the same pier configuration and the same pinned evaluation instant, at an instant whose night has a moonrise
- **THEN** the two serialized documents are byte-identical
- **AND** their `dark_window` and `moon.rise` fields are non-null

### Requirement: Each target carries its identity, ranking and observing fields

Each element of `targets` SHALL be a structured target object with these fields:
a designation (`id`), a common name (`name`, null when the catalog records
none), an object type (`type`), a ranking `score` from 0 to 100, an observable
`window` with a `start` and an `end`, a `remaining_window` with a `start` and an
`end`, a `max_altitude` in degrees, a `transit_time`, and a `moon_separation` in
degrees.

#### Scenario: Targets list is present and ordered when targets are rankable

- **WHEN** a verdict is produced for a night with rankable targets
- **THEN** the `targets` field is a list of target objects, each with `id`, `name`, `type`, `score`, `window`, `remaining_window`, `max_altitude`, `transit_time`, `moon_separation`, `size_arcmin`, `magnitude`, and `surface_brightness`
- **AND** the list is ordered by `score` descending, ties broken by `id`, and holds at most 10 targets

### Requirement: Each target carries its catalog size, magnitude and surface brightness

Each target object SHALL also contain an angular `size_arcmin` (null when the
catalog records none), a `magnitude` (null when the catalog records none), and a
`surface_brightness` in magnitudes per square arcsecond (null when the catalog
records none). Filling the `targets` list, and the `size_arcmin`, `magnitude`,
and `surface_brightness` fields, is additive: the meaning of every other
document field is unchanged.

#### Scenario: Catalog values absent for an object are null on the target

- **WHEN** a target appears whose catalog entry records no size, magnitude, or surface brightness
- **THEN** the corresponding `size_arcmin`, `magnitude`, or `surface_brightness` field is null rather than absent or guessed

### Requirement: The targets list is ordered by score and holds at most 10 targets

The `targets` list SHALL be ordered by `score`, highest first, with ties broken
by `id`, and SHALL contain at most the top 10 targets.

#### Scenario: Rankable targets are listed in score order, at most 10

- **WHEN** a verdict is produced for a night with rankable targets
- **THEN** the `targets` list holds at most 10 targets
- **AND** no target has a higher `score` than the one before it, and targets with equal scores are in `id` order

### Requirement: The targets list is always present, and empty when nothing is rankable

The `targets` field SHALL always be present as a list. The list SHALL be empty
rather than absent when no targets are rankable — for example when the selected
night has no dark window — so the contract shape is stable.

#### Scenario: Targets list present and empty when nothing is rankable

- **WHEN** a verdict is produced for a night with no dark window
- **THEN** the `targets` field is present and is an empty list

### Requirement: Target catalog values are emitted at a fixed precision

The `size_arcmin`, `magnitude`, and `surface_brightness` values SHALL be rounded
to a fixed precision when emitted, following the same stable-precision rule as
the document's other astronomical numeric fields, so the serialized document
stays byte-stable for the same inputs.

#### Scenario: Target catalog values are rounded to two decimal places

- **WHEN** a target's catalog values are a size of 177.8349 arcminutes, a magnitude of 3.4412 and a surface brightness of 13.9987
- **THEN** the target's `size_arcmin` is 177.83, its `magnitude` is 3.44 and its `surface_brightness` is 14.0

### Requirement: A failed hard gate is the only cause of a NO-GO

The verdict SHALL be `NO-GO` when any hard gate fails, and a failed gate SHALL
be the only cause of a `NO-GO`. There are three hard gates: no dark window, the
overcast gate and the wind gate.

#### Scenario: An unusable night is never NO-GO without a failed gate

- **WHEN** every hard gate passes
- **THEN** the `verdict` is not `NO-GO`
- **AND** the `score` is a non-null integer between 0 and 100

### Requirement: A failed hard gate leaves the score null and names the gate

When a gate fails, the `score` SHALL be null and the reasons SHALL name the
failing gate.

#### Scenario: A wind-gated verdict names the wind in its reasons

- **WHEN** a pier has a configured wind-gust limit of 40 km/h, the scored window is clear, and the forecast gust is 60 km/h at every hour of it
- **THEN** the `score` is null
- **AND** a reason names the wind

### Requirement: A selected night with no dark window fails a hard gate

A hard gate SHALL fail when the selected night has no dark window.

#### Scenario: No dark window gates to NO-GO

- **WHEN** a verdict is produced for a selected night that has no dark window
- **THEN** the `verdict` is `NO-GO`
- **AND** the `score` is null

### Requirement: The overcast gate fails when every part of the scored window with cloud data is overcast

The overcast gate SHALL fail when cloud data is available for the scored window,
and every part of that window with cloud data is overcast (no part is usably
clear). The overcast gate SHALL require cloud data to be available. When cloud
data is entirely absent, the overcast gate SHALL NOT fire; that case is the
missing-data path, not a NO-GO. The overcast gate SHALL NOT fire on an empty
scored window; that case is the no-dark-time-left path.

#### Scenario: An all-night overcast dark window gates to NO-GO

- **WHEN** every hour of the scored window is overcast, with no usably clear portion
- **THEN** the `verdict` is `NO-GO`
- **AND** the `score` is null

### Requirement: The wind gate fails when the forecast gust exceeds a configured limit

The wind gate exists only when a wind-gust limit is configured for the pier. It
SHALL fail when the forecast gust exceeds that limit at any hour of the scored
window.

#### Scenario: Configured wind-gust limit gates to NO-GO

- **WHEN** a pier has a configured wind-gust limit and the forecast gust exceeds it at any hour of the scored window
- **THEN** the `verdict` is `NO-GO`
- **AND** the `score` is null

### Requirement: A gate-passing night gets a deterministic integer score from 0 to 100

When every hard gate passes, the system SHALL compute an integer score from 0 to
100 from the observing conditions across the scored window. The same inputs
SHALL yield the same integer score.

#### Scenario: Two runs on the same inputs give the same score

- **WHEN** a verdict is produced twice for the same pier, evaluation instant and conditions, and every hard gate passes
- **THEN** both verdicts carry the same integer `score`

### Requirement: The score sums each hour's usable sky, scaled by that hour's factors

The score SHALL be a sum over the scored window's hour slots, divided by the
window's length in hours, scaled to 100 and rounded. Each slot adds its weight,
as the atmosphere factor defines it, times three factors of that hour:

- the **atmosphere factor**: `0.7 + 0.3 × a`;
- the **moon factor**: `1 − 0.5 × illumination` when the moon is up at the middle of the slot's part of the window, else 1;
- the **high-cloud factor**: `1 − 0.3 × h`, with `h` the hour's high cloud from 0 to 1, or 1 with no reading.

#### Scenario: Better seeing and transparency never lower the score

- **WHEN** two nights are identical in cloud, high cloud and moon, and one has better seeing and transparency in its usably clear hours
- **THEN** the night with the better seeing and transparency has a score no lower than the other
- **AND** when the usable-sky term is 1, the moon is down, no high cloud is present, and seeing and transparency move from 0 to 1, the `score` moves from 70 to 100

#### Scenario: The moon and high cloud cut only the hours they are in

- **WHEN** a scored window has ten clear hours with no seeing or transparency, a full moon is up in the first four hours only, and those four hours have 100% high cloud while the other six have 0%
- **THEN** the `score` is 74

### Requirement: A half-way score rounds to the even integer

A scaled score exactly half-way between two integers SHALL round to the even
one, so 12.5 gives 12 and 13.5 gives 14.

#### Scenario: A score of 12.5 rounds to 12

- **WHEN** every gate passes, one hour of an eight-hour scored window is clear and the other seven are overcast, no hour carries seeing or transparency, the moon is below the horizon throughout, and no high-cloud component is available
- **THEN** the `score` is 12

### Requirement: The atmosphere factor rests on a clarity-weighted mean of each hour's quality

The atmosphere factor SHALL rest on a per-hour quality `a`:

- `a` is the mean of the seeing and transparency values the hour carries.
- An hour that carries neither has `a` of 1.
- `A` is the weighted mean of `a` over the hour slots of the scored window.
- Each slot's weight is the share of that hour inside the scored window, times its clarity weight.
- A boundary hour half inside the window and fully clear weighs 0.5. A whole hour at the overcast knee weighs 0.

#### Scenario: An hour with only seeing takes its quality from the seeing

- **WHEN** a six-hour scored window is clear throughout, and every hour carries a seeing of 0.4 and no transparency
- **THEN** `A` is 0.4

### Requirement: The score never exceeds the usable-sky term

Because every factor is at most 1, the score SHALL never exceed the usable-sky
term scaled to 100 and rounded. Good seeing and transparency refine a clear
night; they cannot lift a cloudy one.

#### Scenario: Good seeing and transparency cannot lift a mostly cloudy night

- **WHEN** every gate passes, the usable-sky term is 0.15, seeing and transparency are both 0.71 in the usably clear hours, the moon is below the horizon throughout, and no high-cloud component is available
- **THEN** the `score` is 14

### Requirement: GO needs a score at the go-threshold, cloud data and no cap

The verdict SHALL be `GO` when the score is at or above the pier's go-threshold,
**cloud data for the scored window is available**, and no cap applies. It SHALL
be `MAYBE` otherwise. Two caps exist: wind data that does not cover the scored
window when a wind limit is configured, and a scored window shorter than 60
minutes, narrowed or not. Requiring cloud data for a `GO` SHALL hold even when
the go-threshold is 0, so a `GO` is never issued without evidence the sky is
clear.

#### Scenario: A score at or above the go-threshold with cloud data is GO

- **WHEN** every gate passes, cloud data is available, no cap applies, and the computed score is at or above the pier's go-threshold
- **THEN** the `verdict` is `GO`

#### Scenario: A score below the go-threshold is MAYBE

- **WHEN** every gate passes and the computed score is below the pier's go-threshold
- **THEN** the `verdict` is `MAYBE`

### Requirement: A brighter night never scores higher

A brighter night SHALL NOT score higher than an otherwise identical darker one.

#### Scenario: A bright moon up during darkness lowers the score

- **WHEN** two otherwise identical nights differ only in that the moon is bright and above the horizon during the scored window in one and absent in the other
- **THEN** the night with the bright moon up during darkness has the lower score

### Requirement: More cloud never raises the score

More cloud in any hour SHALL NOT raise the score, holding every other reading
fixed. That holds for any pattern of missing seeing, transparency and high-cloud
readings, because an hour without a reading counts that factor as 1.

#### Scenario: Clouding out a poor-atmosphere hour never raises the score

- **WHEN** a scored window has ten clear hours, eight with no seeing or transparency, one with both at 1, and one with both at 0, the moon is down throughout, and no high-cloud component is present
- **THEN** the `score` is 97
- **AND** when the hour with both at 0 is made overcast instead, the `score` is 90

#### Scenario: Clouding out the one cirrus hour never raises the score

- **WHEN** a scored window has ten clear hours with no seeing or transparency, the moon is down throughout, one hour has 100% high cloud, and the other nine carry no high-cloud reading
- **THEN** the `score` is 97
- **AND** when that hour is made overcast instead, the `score` is 90

### Requirement: The reasons explain the atmosphere factor

The reasons SHALL explain the atmosphere factor as computed. A scored verdict
SHALL carry a reason that states the atmosphere factor as a percentage. Each
seeing or transparency reason SHALL state the share of the usable sky its data
covers, when that share is below 100%.

#### Scenario: The reasons explain an atmosphere factor built on partial data

- **WHEN** a scored window has nine clear hours with no seeing or transparency and one clear hour with both at 0
- **THEN** a reason states an atmosphere factor of 97%
- **AND** the seeing and transparency reasons each state a quality of 0% covering 10% of the usable sky

### Requirement: A verdict is always produced when conditions are missing

When conditions data is missing, the verdict SHALL degrade rather than fail or
mislead. A verdict SHALL always be produced.

#### Scenario: A verdict is always produced despite missing conditions

- **WHEN** conditions cannot be obtained at all for a pier with a dark window
- **THEN** a verdict document is still produced

### Requirement: Missing seeing or transparency drops only its own contribution

Missing seeing or transparency SHALL drop only its own contribution and lower
confidence. When no hour carries seeing or transparency, the atmosphere factor
is 1. The missing data SHALL lower confidence instead.

#### Scenario: Missing seeing and transparency leave the score at the usable-sky term

- **WHEN** two nights are identical in cloud, high cloud and moon, and one has no seeing or transparency data at all
- **THEN** the night without seeing and transparency scores the usable-sky term cut only by the moon and high-cloud factors, scaled to 100 and rounded
- **AND** its confidence is lower

### Requirement: The hard gates come before the missing-cloud rule

The hard gates SHALL be evaluated before the missing-cloud rule applies. A
failed hard gate that does not depend on cloud data (no dark window, or a
configured wind gust over its limit) SHALL still yield `NO-GO` even when cloud
data is missing, so a safety-critical gate is never overridden by a missing
observation. The missing-cloud rule SHALL NOT apply to an empty scored window;
that case is the no-dark-time-left path.

#### Scenario: A failed wind gate yields NO-GO even when cloud data is missing

- **WHEN** cloud data is unavailable but wind-gust data is available and exceeds the pier's configured wind-gust limit during the scored window
- **THEN** the `verdict` is `NO-GO`
- **AND** the `score` is null

### Requirement: A wind-gust limit that wind data does not fully cover is unavailable

When a wind-gust limit is configured but wind data does not cover every hour of
the scored window, the limit cannot be confirmed, so it SHALL be treated as
unavailable. This holds whether wind data is absent for the whole scored window
or only for some of its hours.

#### Scenario: Partial wind coverage caps the verdict at MAYBE when a limit is configured

- **WHEN** a pier has a configured wind-gust limit, no hour with wind data exceeds it, but at least one hour of the scored window has no wind data
- **THEN** the `verdict` is not `GO`
- **AND** the `verdict` is `MAYBE`
- **AND** a reason states that wind data is unavailable

### Requirement: An unavailable wind-gust limit caps the verdict at MAYBE

When a configured wind-gust limit is treated as unavailable because wind data
does not cover every hour of the scored window, and no hour with wind data has
already failed the gate, the verdict SHALL NOT be `GO` and SHALL be capped at
`MAYBE`, with a reason that wind data is unavailable and lowered confidence.

#### Scenario: Missing wind data caps the verdict at MAYBE when a limit is configured

- **WHEN** a pier has a configured wind-gust limit, every gate that can be evaluated passes, and wind-gust data is unavailable for the scored window
- **THEN** the `verdict` is not `GO`
- **AND** the `verdict` is `MAYBE`
- **AND** a reason states that wind data is unavailable

### Requirement: Entirely missing cloud data gives MAYBE with a score of 0

Only when every hard gate passes does the missing-cloud rule apply. It applies
when cloud data for the scored window is entirely unavailable. The verdict SHALL
NOT be `GO`, because there is no evidence the sky is clear. It SHALL NOT be
`NO-GO` on account of the missing data itself, because absence of data is not a
dealbreaker. It SHALL be `MAYBE` with a `score` of 0. Its `confidence.value`
SHALL be 0 in the `LOW` band. A reason SHALL state that conditions are
unavailable.

#### Scenario: Missing cloud data caps the verdict at MAYBE when gates pass

- **WHEN** a verdict is produced for a pier with a dark window, every hard gate passes, and there is no available cloud data
- **THEN** the `verdict` is `MAYBE`
- **AND** the `verdict` is neither `GO` nor `NO-GO`
- **AND** the `score` is 0
- **AND** the `confidence.value` is 0
- **AND** the `confidence.band` is `LOW`
- **AND** a reason states that conditions are unavailable

### Requirement: A pier has three optional tuning knobs and no others

A pier configuration MAY set three tuning knobs: a go-threshold, a wind-gust
limit and a dew margin. These SHALL be the only tuning knobs; all other
thresholds and weights are fixed by the system.

#### Scenario: A pier configuration sets its go-threshold and wind-gust limit

- **WHEN** a pier configuration sets a go-threshold of 70 and a wind-gust limit of 45
- **THEN** the pier's go-threshold is 70 and its wind-gust limit is 45

### Requirement: An omitted go-threshold takes the system default

The go-threshold is an integer from 0 to 100. A gate-passing night with a score
at or above it is `GO` rather than `MAYBE`. When the go-threshold is omitted, a
system default SHALL apply.

#### Scenario: Omitted go-threshold uses the default

- **WHEN** a pier configuration omits the go-threshold
- **THEN** the system default go-threshold is applied

### Requirement: An omitted wind-gust limit disables the wind gate

The wind-gust limit enables the wind gate. When the wind-gust limit is omitted,
the wind gate SHALL be disabled and gusts SHALL NOT be able to cause a `NO-GO`.

#### Scenario: Omitted wind-gust limit disables the wind gate

- **WHEN** a pier configuration omits the wind-gust limit
- **THEN** no forecast gust can cause a `NO-GO` for that pier

### Requirement: The dew margin defaults to 4 °C, and 0 turns the dew line off

The dew margin is in °C: a finite number of 0 or more. A spread between
temperature and dew point under it makes dew or frost likely. When the dew
margin is omitted, it SHALL be 4 °C. A dew margin of 0 SHALL turn the dew line
off.

#### Scenario: Omitted dew margin is 4 °C

- **WHEN** a pier configuration omits the dew margin
- **THEN** the pier's dew margin is 4 °C

### Requirement: A negative or non-finite dew margin is a configuration error

A negative or non-finite dew margin SHALL be rejected as a configuration error.

#### Scenario: A negative or infinite dew margin is rejected

- **WHEN** a pier configuration sets a dew margin of −1, or of `.inf`
- **THEN** loading the configuration fails with an error that names the dew margin

### Requirement: High, thin cloud has a score penalty apart from total cloud

When every hard gate passes and cloud data is available, the banded score SHALL
apply a penalty for high-layer (thin cirrus) cloud across the scored window that
is distinct from the total-cloud term of the score. High cirrus can leave a low
total cloud reading yet wreck transparency for deep-sky work, so the night is
scored honestly rather than as clear.

#### Scenario: High cirrus lowers the score with its own reason

- **WHEN** two nights are identical, each with cloud data available and every hard gate passing, except that one has high, thin cloud usably up during the scored window and the other has none
- **THEN** the night with the high cirrus has the lower score
- **AND** its `reasons` list carries a high/thin-cloud line distinct from the total-cloud line

### Requirement: The high-cloud penalty has its own reason line

The high-cloud penalty SHALL be reported as its own itemized `reasons[]` line,
separate from the total-cloud reason, so the explanation names it as a distinct
term.

#### Scenario: A 60% high-cloud penalty has one reason line of its own

- **WHEN** every gate passes, every hour of a six-hour scored window has 10% total cloud and 60% high cloud, and the moon is below the horizon throughout
- **THEN** the `reasons` list carries exactly one high-cloud line, `High cloud penalty 60% (thin cirrus aloft).`
- **AND** it carries a separate total-cloud line that starts `Cloud:`

### Requirement: The high-cloud reason states the share of the usable sky its readings cover

When the hours that carry a high-cloud reading make up less than all of the
usable sky, the high-cloud reason SHALL state that share as a percentage. Its
penalty stays the mean over those hours.

#### Scenario: One cirrus hour of ten states its coverage

- **WHEN** a scored window has ten clear hours, the moon is down throughout, one hour has 100% high cloud, and the other nine carry no high-cloud reading
- **THEN** the `reasons` list carries the line `High cloud penalty 100% (thin cirrus aloft; covers 10% of the usable sky).`

#### Scenario: Full coverage adds no share

- **WHEN** every hour of a six-hour scored window has 10% total cloud and 60% high cloud, and the moon is below the horizon throughout
- **THEN** the high-cloud reason is exactly `High cloud penalty 60% (thin cirrus aloft).`

### Requirement: More high cloud never raises the score

Holding every other input fixed — including the total cloud cover — more
high-layer cloud usably up during the scored window SHALL NOT raise the score:
it lowers it or leaves it unchanged.

#### Scenario: Rising high cloud on a clear night never raises the score

- **WHEN** a six-hour scored window is clear throughout, the moon is down, and the high cloud in every hour is 0%, then 25%, 50%, 75% and 100%
- **THEN** no score is higher than the one before it
- **AND** the score with 0% high cloud is 100, and the score with 100% high cloud is lower

### Requirement: The high-cloud penalty only shapes the banded score

The high-cloud penalty SHALL only shape the banded score; it SHALL NOT introduce
a new hard gate and SHALL NOT on its own cause a `NO-GO`. This term is additive:
it does not change the meaning of the existing total-cloud term, the gates, the
bands, or the confidence.

#### Scenario: The high-cloud penalty never gates the night

- **WHEN** a night has high, thin cloud during the scored window while every hard gate passes
- **THEN** the `verdict` is not `NO-GO` on account of the high cloud
- **AND** the `score` is a non-null integer between 0 and 100 inclusive

### Requirement: The high-cloud penalty is weighted toward the usably clear hours

The high-cloud penalty SHALL be weighted toward the usably clear hours in the
same way as the other non-cloud terms, so a high-cirrus reading during a
clouded-out hour does not distort the verdict.

#### Scenario: High cloud over overcast hours adds no penalty

- **WHEN** a six-hour scored window has three clear hours with 20% high cloud and three overcast hours with 90% high cloud
- **THEN** the high-cloud penalty is 20%, the mean over the three clear hours only

### Requirement: A missing high-cloud component drops its own contribution

When the high-layer cloud component is unavailable for the scored window, the
high-cloud term SHALL drop its own contribution — no penalty and no reason line
— rather than fail or guess, exactly as the other optional terms degrade when
their data is missing.

#### Scenario: Missing high-cloud component drops the term without penalty

- **WHEN** two nights are identical and every hard gate passes, except that one has its high-layer cloud component available and clear and the other has that component unavailable while total cloud cover is available
- **THEN** neither night is penalized for high cloud
- **AND** neither `reasons` list carries a high/thin-cloud line

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

### Requirement: Hours only an alternate covers add no timeline entry

Hours only an alternate covers SHALL NOT add a timeline entry.

#### Scenario: Hours only an alternate covers add no entry

- **WHEN** every filled series ends at 03:00 and a `cloud_cover` alternate runs to 03:00 two days later
- **THEN** the `timeline`'s last entry is 03:00 on the first night

### Requirement: A variable the timeline does not show adds no timeline hour

Hours only a series of a variable the timeline does not show covers SHALL NOT
add a timeline entry.

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
