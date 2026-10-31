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

### Requirement: Targets list is an ordered ranked list

The `targets` field SHALL always be present as a list. Each element SHALL be a
structured target object with these fields: a designation (`id`), a common name
(`name`, null when the catalog records none), an object type (`type`), a ranking
`score` from 0 to 100, an observable `window` with a `start` and an `end`, a
`max_altitude` in degrees, a `transit_time`, a `moon_separation` in degrees, an
angular `size_arcmin` (null when the catalog records none), a `magnitude` (null
when the catalog records none), and a `surface_brightness` in magnitudes per
square arcsecond (null when the catalog records none). The list SHALL be ordered
by `score`, highest first, with ties broken by `id`, and SHALL contain at most the
top 10 targets. The list SHALL be empty rather than absent when no targets are
rankable — for example when the selected night has no dark window — so the
contract shape is stable. Filling this list, and the `size_arcmin`, `magnitude`,
and `surface_brightness` fields, is additive: the meaning of every other document
field is unchanged. The `size_arcmin`, `magnitude`, and `surface_brightness` values
SHALL be rounded to a fixed precision when emitted, following the same
stable-precision rule as the document's other astronomical numeric fields, so the
serialized document stays byte-stable for the same inputs.

#### Scenario: Targets list is present and ordered when targets are rankable

- **WHEN** a verdict is produced for a night with rankable targets
- **THEN** the `targets` field is a list of target objects, each with `id`, `name`, `type`, `score`, `window`, `max_altitude`, `transit_time`, `moon_separation`, `size_arcmin`, `magnitude`, and `surface_brightness`
- **AND** the list is ordered by `score` descending, ties broken by `id`, and holds at most 10 targets

#### Scenario: Catalog values absent for an object are null on the target

- **WHEN** a target appears whose catalog entry records no size, magnitude, or surface brightness
- **THEN** the corresponding `size_arcmin`, `magnitude`, or `surface_brightness` field is null rather than absent or guessed

#### Scenario: Targets list present and empty when nothing is rankable

- **WHEN** a verdict is produced for a night with no dark window
- **THEN** the `targets` field is present and is an empty list

### Requirement: Night window is the astronomical-night boundary

The `dark_window` field SHALL always be present and SHALL contain a `start` and an `end`. It represents the astronomical-night boundary (astronomical dusk to astronomical dawn, defined by the sun's centre crossing -18 degrees altitude) for the night **selected relative to the evaluation instant** supplied by the injectable clock — not for a calendar date. The selected night SHALL be the one whose astronomical dawn is the first astronomical dawn at or after the evaluation instant: if the instant falls during astronomical night, the current night is selected (its dusk already past, its dawn ahead); otherwise the next upcoming night is selected. This makes the answer to "is tonight worth setting up for" correct whether the question is asked in the afternoon or after midnight mid-session.

When the selected night exists, `start` and `end` SHALL be the UTC instants of its astronomical dusk and dawn, and `start` SHALL be strictly before `end`. If truncation to whole seconds would collapse a grazing, sub-second astronomical night so that `start` is not strictly before `end`, the window SHALL be reported as null — such a night provides no usable darkness — so a non-null window always has `start` strictly before `end`.

The two extreme-latitude boundary cases SHALL be handled distinctly, because the underlying twilight search reports no crossings in both:

- **Continuous astronomical night** (the sun never rises above -18 degrees across the searched span — e.g. high-latitude winter, the best observing season): `dark_window` SHALL be non-null and cover the dark span, so a polar-winter night is never mistaken for "no night". The window SHALL be anchored to a stable boundary derived from the evaluation instant (not the moving instant itself), so successive recomputes within the same period yield the same window rather than one that slides forward on each poll.
- **Continuous non-night** (the sun never falls below -18 degrees across the searched span — e.g. high-latitude summer): `dark_window.start` and `dark_window.end` SHALL both be null, since there is no astronomical darkness.

In every case the field SHALL be present rather than omitted.

#### Scenario: A real astronomical-night window is computed when night exists

- **WHEN** a verdict is produced at a mid-latitude site while it is daytime, for a date whose location has a normal astronomical night
- **THEN** `dark_window.start` is the UTC instant of the next astronomical dusk at or after the evaluation instant (sun descending through -18 degrees)
- **AND** `dark_window.end` is the UTC instant of the following astronomical dawn (sun ascending through -18 degrees)
- **AND** `dark_window.start` is strictly before `dark_window.end`

#### Scenario: The current night is selected when the instant is already dark

- **WHEN** a verdict is produced at an evaluation instant that falls within astronomical night (for example, after local midnight, mid-session)
- **THEN** `dark_window.end` is the first astronomical dawn at or after the evaluation instant
- **AND** `dark_window.start` is the astronomical dusk immediately preceding that dawn (already in the past relative to the evaluation instant)

#### Scenario: Continuous astronomical night yields a non-null window

- **WHEN** a verdict is produced for a location and date where the sun never rises above -18 degrees across the searched span
- **THEN** `dark_window.start` and `dark_window.end` are both non-null and cover the dark span
- **AND** `dark_window.start` is strictly before `dark_window.end`
- **AND** two verdicts produced at different evaluation instants within the same anchored period yield the same `dark_window.start` and `dark_window.end`

#### Scenario: Continuous non-night yields a null window

- **WHEN** a verdict is produced for a location and date where the sun never falls below -18 degrees across the searched span
- **THEN** `dark_window.start` and `dark_window.end` are both null
- **AND** the field is present rather than omitted

### Requirement: Moon information across the dark window

The verdict document SHALL contain a `moon` object with these fields: `illumination` (the illuminated fraction, a number from 0 to 1), `phase` (a phase name drawn from a fixed enumeration of the eight standard phases: new, waxing crescent, first quarter, waxing gibbous, full, waning gibbous, last quarter, waning crescent), `up_during_dark` (a boolean, or null when there is no dark window, indicating whether the moon is above the horizon at any point during the dark window), `rise` and `set` (the UTC instants of moonrise and moonset that fall within the dark window, or null when the moon does not rise/set within it or when there is no dark window). "Above the horizon", "moonrise", and "moonset" SHALL be defined by the moon's **geometric centre crossing 0 degrees altitude** (no atmospheric-refraction or lunar-radius correction), so the boundary is pinned and does not vary with a library's refraction defaults. This gives later milestones the single moon fact that changes a night's verdict — a bright moon above the horizon during darkness — without reshaping the document.

#### Scenario: Moon object carries illumination and a bounded phase name

- **WHEN** a verdict is produced for a valid pier configuration
- **THEN** `moon.illumination` is a number between 0 and 1 inclusive
- **AND** `moon.phase` equals one of the eight enumerated phase names

#### Scenario: Moon above-horizon behaviour is reported across an existing dark window

- **WHEN** a verdict is produced for a location and date that has an astronomical-night window
- **THEN** `moon.up_during_dark` is a boolean indicating whether the moon is above the horizon at any point within `dark_window.start`..`dark_window.end`
- **AND** when `moon.rise` or `moon.set` is non-null, that instant falls within `dark_window.start`..`dark_window.end`

#### Scenario: Across-window moon fields are null when there is no astronomical night

- **WHEN** a verdict is produced for a location and date with no astronomical night (continuous non-night)
- **THEN** `moon.up_during_dark`, `moon.rise`, and `moon.set` are all null
- **AND** `moon.illumination` and `moon.phase` remain present

### Requirement: Astronomical fields are computed offline with stable precision

The system SHALL compute the astronomical fields of the verdict document (the night window and the moon information) without any network access at runtime, using ephemeris and timescale data bundled with the system, so verdict production is fully self-contained and offline. Numeric astronomical outputs SHALL be emitted at a fixed, defined decimal precision, and every timestamp in the document (`generated_at` as well as `dark_window.start`/`end` and `moon.rise`/`set`) SHALL be emitted with its sub-second component removed (whole seconds). This precision SHALL be applied when the document is constructed (not only when it is serialized), so the in-memory document and its JSON form agree and a document survives a serialize-then-read-back round trip unchanged. For a given platform and the pinned library set, the same pier configuration and the same pinned evaluation instant SHALL yield byte-identical serialized values on repeated runs; cross-platform identity is guarded by pinned-value tests in CI rather than asserted as an absolute guarantee. This preserves the deterministic-emission guarantee once real sky math is introduced and keeps Home Assistant and external services non-load-bearing for correctness.

#### Scenario: Verdict production performs no runtime network access

- **WHEN** a verdict is produced with no network available
- **THEN** production succeeds and the document's astronomical fields are populated (or null where no astronomical night exists)
- **AND** producing the verdict makes no outbound network request

#### Scenario: Astronomical numeric and time fields are emitted at a fixed precision

- **WHEN** a verdict is produced twice for the same pier configuration and the same pinned evaluation instant
- **THEN** every astronomical numeric field (such as `moon.illumination`) is emitted rounded to the defined fixed precision
- **AND** every document timestamp (`generated_at`, `dark_window.start`/`end`, `moon.rise`/`set`) is emitted with no sub-second component
- **AND** the two serialized documents are byte-identical in those fields

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

### Requirement: The verdict judges the remaining night

The verdict SHALL judge the **scored window**: the part of the dark window from the evaluation instant to `dark_window.end`.

`dark_window.end` has two meanings. On an ordinary night it is astronomical dawn. In continuous polar night it is the end of the local solar day that anchors the dark window. The rules below read `dark_window.end` and work the same for both.

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

An empty scored window can only arise in the last partial second of the window. Three facts combine:

- `dark_window.end` is the exact end instant, floored to a whole second.
- The scoring instant is the evaluation instant floored to a whole second.
- The selected window ends at the first exact end that qualifies against the evaluation instant.

Which exact end qualifies differs by case. On an ordinary night, a dawn crossing at or after the evaluation instant qualifies, so an instant exactly on the crossing still selects the ending night. In continuous polar night, only a solar-day boundary after the evaluation instant qualifies, so an instant exactly on the boundary selects the next solar day.

So the scoring instant equals `dark_window.end` only when the evaluation instant lies in that floored second and the selection still picks that window. For a dawn crossing, that is up to and including the exact crossing. For a polar solar-day boundary, that is up to but not including the exact boundary.

When the scored window is empty, the verdict SHALL be `MAYBE` with a `score` of 0 and a reason that no dark time remains. It SHALL NOT fail the overcast gate, SHALL NOT be `GO`, and SHALL NOT report that conditions are unavailable.

A short span is not worth setting up for, however clear it is. When the scored window is shorter than 60 minutes, the verdict SHALL NOT be `GO`. This holds whether the window is narrowed or is a whole short night. The gates and the score still run as usual. A verdict that would otherwise be `GO` SHALL be `MAYBE`, with a reason that the scored window holds less than an hour of dark time. The reason SHALL read correctly before dusk and during the night, so it SHALL NOT say that time "remains".

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

#### Scenario: Less than an hour of dark time caps the verdict at MAYBE

- **WHEN** a verdict is produced at an evaluation instant 30 minutes before `dark_window.end`, the remaining sky is clear, and the score is at or above the go-threshold
- **THEN** the `verdict` is `MAYBE`
- **AND** the `score` is the computed score, not 0
- **AND** a reason states that the scored window holds less than an hour of dark time

#### Scenario: A whole night shorter than an hour is capped the same way

- **WHEN** a verdict is produced before dusk for a night whose dark window is 50 minutes long, the sky is clear, and the score is at or above the go-threshold
- **THEN** the `verdict` is `MAYBE`
- **AND** a reason states that the scored window holds less than an hour of dark time

#### Scenario: In continuous polar night, the scored window ends with the solar day

- **WHEN** a verdict is produced during continuous polar night, at an evaluation instant inside the dark window
- **THEN** `scored_window.end` equals `dark_window.end`
- **AND** `scored_window.start` equals `generated_at`

#### Scenario: In continuous polar night, the exact solar-day boundary starts the next window

- **WHEN** a verdict is produced during continuous polar night, at an evaluation instant exactly on the local solar-day boundary
- **THEN** `dark_window` is the next solar day's window
- **AND** `scored_window` equals `dark_window`

#### Scenario: In continuous polar night, the floored second before the boundary is empty

- **WHEN** a verdict is produced during continuous polar night, at an evaluation instant in the whole second that `dark_window.end` names, before the exact boundary, with cloud data available
- **THEN** `scored_window.start` equals `scored_window.end`
- **AND** the `verdict` is `MAYBE` with a `score` of 0

#### Scenario: An hour or more left can still be GO

- **WHEN** a verdict is produced at an evaluation instant 60 minutes before `dark_window.end`, the remaining sky is clear, no wind limit is configured, and the score is at or above the go-threshold
- **THEN** the `verdict` is `GO`

#### Scenario: A verdict after the exact dawn crossing judges the next night

- **WHEN** a verdict is produced at an evaluation instant after the exact astronomical dawn crossing
- **THEN** `dark_window` is the next night's window
- **AND** `scored_window` equals `dark_window`

### Requirement: Reasons name the scored span

The scored window is **narrowed** when `scored_window.start` is later than `dark_window.start`. That is the test for every rule in this requirement. An evaluation instant in the same whole second as dusk is not narrowed: its scored window is the whole night, so the whole-night wording is true.

When the scored window is narrowed, every verdict with a dark window SHALL carry a span line as its first reason. The span line states the scored window's start and end as UTC dates and times, to the second, in the same format as the document's timestamps. This holds for a scored verdict, a gated `NO-GO`, a missing-cloud `MAYBE`, and an empty scored window.

When the scored window is narrowed, no reason SHALL make a claim about the whole night, and no reason SHALL claim more than the forecast covers. On a scored verdict, the cloud reason SHALL state the usable share of the remaining night. A failed overcast gate SHALL say that the forecast shows no usably clear sky for the rest of the night. A failed wind gate SHALL say the gust falls in the rest of the night.

When the scored window is not narrowed, no span line is present, and the reasons keep their whole-night wording.

#### Scenario: A mid-session scored verdict names the span it judged

- **WHEN** a scored verdict is produced at an evaluation instant at least one second after `dark_window.start` and inside the dark window
- **THEN** the first reason states the start and end of the scored window, each as the same UTC date and time string the document emits for `scored_window.start` and `scored_window.end`
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
- the **atmosphere factor**: `0.7 + 0.3 × A`, defined below;
- the **moon factor**: the moon's brightness weighted by how much of the usably clear scored window it is above the horizon, as today;
- the **high-cloud factor**, as today.

The atmosphere factor rests on a per-hour quality `a`:

- `a` is the mean of the seeing and transparency values the hour carries.
- An hour that carries neither has `a` of 1.
- `A` is the weighted mean of `a` over the hour slots of the scored window.
- Each slot's weight is the share of that hour inside the scored window, times its clarity weight.
- A boundary hour half inside the window and fully clear weighs 0.5. A whole hour at the overcast knee weighs 0.
- When no hour carries seeing or transparency, the factor is 1. The missing data SHALL lower confidence instead.

Because every factor is at most 1, the score SHALL never exceed the usable-sky term scaled to 100 and rounded. Good seeing and transparency refine a clear night; they cannot lift a cloudy one. The same inputs SHALL yield the same integer score.

The verdict SHALL be `GO` when the score is at or above the pier's go-threshold, **cloud data for the scored window is available**, and no cap applies. It SHALL be `MAYBE` otherwise. Two caps exist: wind data that does not cover the scored window when a wind limit is configured, and a scored window shorter than 60 minutes, narrowed or not. Requiring cloud data for a `GO` SHALL hold even when the go-threshold is 0, so a `GO` is never issued without evidence the sky is clear.

A brighter night SHALL NOT score higher than an otherwise identical darker one.

More cloud SHALL NOT raise the product of the usable-sky term and the atmosphere factor. That holds for any pattern of missing seeing and transparency, because an hour without data counts as 1.

The moon and high-cloud factors keep today's rules. Each is a ratio over the usably clear hours. Clouding out the one hour that carried the moon or the cirrus can therefore still raise the score. The spec does not promise monotonicity in cloud through those two factors. Issue #112 covers that gap.

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

- **WHEN** two nights are identical except that one has more of its scored window usably clear, by enough to change the rounded score, the moon is down throughout both, and no high-cloud component is present
- **THEN** the night with more usable clear darkness has the higher score

### Requirement: The verdict degrades honestly when conditions are unavailable

When conditions data is missing, the verdict SHALL degrade rather than fail or mislead. A verdict SHALL always be produced. The rules, in the order they apply:

- **Missing optional data.** Missing seeing or transparency SHALL drop only its own contribution and lower confidence.
- **Gates first.** The hard gates SHALL be evaluated before the missing-cloud rule applies. A failed hard gate that does not depend on cloud data (no dark window, or a configured wind gust over its limit) SHALL still yield `NO-GO` even when cloud data is missing, so a safety-critical gate is never overridden by a missing observation.
- **Empty scored window.** The missing-cloud rule SHALL NOT apply to an empty scored window; that case is the no-dark-time-left path.
- **Wind limit set but wind not fully covered.** When a wind-gust limit is configured but wind data does not cover every hour of the scored window, the limit cannot be confirmed, so it SHALL be treated as unavailable. This holds whether wind data is absent for the whole scored window or only for some of its hours. When the limit is treated as unavailable this way, and no hour with wind data has already failed the gate, the verdict SHALL NOT be `GO` and SHALL be capped at `MAYBE`, with a reason that wind data is unavailable and lowered confidence.
- **Cloud entirely missing.** Only when every hard gate passes does the missing-cloud rule apply. It applies when cloud data for the scored window is entirely unavailable. The verdict SHALL NOT be `GO`, because there is no evidence the sky is clear. It SHALL NOT be `NO-GO` on account of the missing data itself, because absence of data is not a dealbreaker. It SHALL be `MAYBE` with a `score` of 0. Its `confidence.value` SHALL be 0 in the `LOW` band. A reason SHALL state that conditions are unavailable.

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

### Requirement: Optional pier tuning configuration

A pier configuration MAY set a go-threshold (an integer from 0 to 100 that sets the score at or above which a gate-passing night is `GO` rather than `MAYBE`) and MAY set a wind-gust limit that enables the wind gate. When the go-threshold is omitted, a system default SHALL apply. When the wind-gust limit is omitted, the wind gate SHALL be disabled and gusts SHALL NOT be able to cause a `NO-GO`. These are the only tuning knobs; all other thresholds and weights are fixed by the system.

#### Scenario: Omitted go-threshold uses the default

- **WHEN** a pier configuration omits the go-threshold
- **THEN** the system default go-threshold is applied

#### Scenario: Omitted wind-gust limit disables the wind gate

- **WHEN** a pier configuration omits the wind-gust limit
- **THEN** no forecast gust can cause a `NO-GO` for that pier

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

### Requirement: The document carries an hourly timeline

The verdict document SHALL carry a `timeline` list: the hourly series of sky and weather for the pier. The list SHALL hold one entry per clock hour across the union of the hours the conditions providers returned, including hours already past, sorted by hour ascending, with no hour repeated. The list SHALL be empty, never absent, when no provider returned rows.

#### Scenario: The timeline spans the union of both providers' hours

- **WHEN** a verdict is produced with a base source covering 00:00 to 23:00 on one day and a secondary source covering 12:00 on that day to 11:00 two days later
- **THEN** the `timeline` holds one entry for every hour from the first day's 00:00 to the third day's 11:00, in ascending order, with no hour repeated

#### Scenario: No provider rows yield an empty timeline

- **WHEN** a verdict is produced with the empty conditions value
- **THEN** the document's `timeline` is an empty list
- **AND** the verdict is produced without error

#### Scenario: Past hours stay in the timeline

- **WHEN** a verdict is produced inside the dark window, with the evaluation instant later than some hours a provider returned
- **THEN** the entries for those earlier hours are present and unchanged
- **AND** the `scored_window` still starts at the evaluation instant

### Requirement: A timeline entry has a fixed flat shape

Each timeline entry SHALL carry exactly these keys, always present and in this order: `time`, `sun_altitude`, `moon_altitude`, `cloud_cover`, `cloud_low`, `cloud_mid`, `cloud_high`, `wind_gust`, `seeing`, `transparency`. `time` SHALL be the top of the hour, emitted like every other document timestamp.

#### Scenario: A read-back entry equals the emitted one

- **WHEN** a document with a timeline is serialized to JSON and read back
- **THEN** every entry's keys, order and values are unchanged

### Requirement: Entry values carry each source's reading for the hour

`cloud_cover`, `cloud_low`, `cloud_mid` and `cloud_high` SHALL be percent and `wind_gust` km/h, carried exactly as the base source's reading for that hour, with no rounding, each null when the base source lacks the hour or the value. `seeing` and `transparency` SHALL be quality in 0 to 1 where 1 is best, from the secondary source's reading for that hour, rounded to two decimal places, each null when the secondary source lacks the hour or the value.

#### Scenario: An hour one source lacks carries null for that source's fields

- **WHEN** an hour is present in the secondary source but absent from the base source
- **THEN** that entry's `cloud_cover`, `cloud_low`, `cloud_mid`, `cloud_high` and `wind_gust` are null
- **AND** its `seeing` and `transparency` carry the secondary source's values
- **AND** its `sun_altitude` and `moon_altitude` are present

#### Scenario: Cloud and wind values pass through unchanged

- **WHEN** the base source reports cloud cover `37.0` and a gust of `23.4` for an hour
- **THEN** that entry's `cloud_cover` is `37.0` and its `wind_gust` is `23.4`

#### Scenario: Seeing and transparency are emitted at two decimal places

- **WHEN** the secondary source reports a seeing quality of four sevenths for an hour
- **THEN** that entry's `seeing` is `0.57`

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

The timeline SHALL be filled whenever a provider returned rows, whether or not the selected night has a dark window. It SHALL NOT change the verdict, the score, the confidence, the reasons or any other existing field. It carries no verdict of its own: the verdict judges the one night the dark window names, however far the timeline reaches.

#### Scenario: The timeline fills without a dark window

- **WHEN** a verdict is produced for a pier whose selected night has no dark window and a provider returned rows
- **THEN** the `timeline` holds one entry per returned hour
- **AND** the document with `timeline` removed equals the document produced for the same pier and instant from the empty conditions value

#### Scenario: Hours outside the dark window change no other field

- **WHEN** a verdict is produced twice for the same pier and instant, once with the providers' hours limited to the dark window and once with extra hours before and after it
- **THEN** the two documents differ only in `timeline`
