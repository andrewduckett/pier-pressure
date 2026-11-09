## ADDED Requirements

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
that `dark_window.end` names, up to and including the exact crossing.

#### Scenario: A verdict after the exact dawn crossing judges the next night

- **WHEN** a verdict is produced at an evaluation instant after the exact astronomical dawn crossing
- **THEN** `dark_window` is the next night's window
- **AND** `scored_window` equals `dark_window`

### Requirement: In continuous polar night, an instant on the exact solar-day boundary selects the next solar day

In continuous polar night, only a solar-day boundary after the evaluation
instant SHALL qualify as the exact end of the selected window, so an instant
exactly on the boundary selects the next solar day. So the scoring instant
equals `dark_window.end` only when the evaluation instant lies in the floored
second that `dark_window.end` names, up to but not including the exact
boundary.

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

## REMOVED Requirements

### Requirement: The verdict judges the remaining night

**Reason**: It bundled ten behaviors. It is split into "The verdict judges the
scored window", "Before astronomical dusk, the scored window is the whole dark
window", "Once the night has started, the scored window starts at the scoring
instant", "The gates, the score and the completeness part of confidence run over
the scored window", "The document carries the scored window beside the dark
window", "An empty scored window arises only in the last partial second of the
dark window", "On an ordinary night, an instant on the exact dawn crossing still
selects the ending night", "In continuous polar night, an instant on the exact
solar-day boundary selects the next solar day", "An empty scored window gives
MAYBE with a score of 0" and "Less than an hour of dark time caps the verdict at
MAYBE". Its 14 scenarios move word for word, and one scenario is added. Drift:
at the exact poles, latitude 90 or -90, the code anchors continuous polar night
to the UTC calendar day, because the sun has no meridian transit there
(`pierpressure/core/sky.py`, `_local_solar_day`). This text says the local solar
day. The split keeps the text's meaning.

**Migration**: Nothing changes for users or code. Later changes MODIFY the new
requirements.

### Requirement: Night window is the astronomical-night boundary

**Reason**: It bundled six behaviors. It is split into "The dark window is the
astronomical night selected from the evaluation instant", "The selected night is
the one whose dawn comes first at or after the evaluation instant", "A non-null
dark window starts strictly before it ends", "In continuous astronomical night,
the dark window is non-null and covers the dark span", "The continuous-night
dark window is anchored to a stable boundary" and "In continuous non-night, the
dark window's start and end are null". Its 4 scenarios move word for word, and
two scenarios are added.

**Migration**: Nothing changes for users or code. Later changes MODIFY the new
requirements.

### Requirement: Reasons name the scored span

**Reason**: It bundled three behaviors. It is split into "Reasons keep their
whole-night wording unless the scored window is narrowed", "A narrowed scored
window puts a span line first in the reasons" and "Over a narrowed scored
window, reasons speak only of the rest of the night". Its 5 scenarios move word
for word.

**Migration**: Nothing changes for users or code. Later changes MODIFY the new
requirements.

### Requirement: Conditions are evaluated across the whole scored window

**Reason**: It bundled four behaviors. It is split into "The score reflects the
extent and quality of the scored window's usable dark time", "A scored window
with some usably clear hours is not gated as overcast", "Usable dark time is
normalized to the scored window's actual duration" and "Hours without cloud data
count as neither clear nor overcast". Its 4 scenarios move word for word.

**Migration**: Nothing changes for users or code. Later changes MODIFY the new
requirements.

### Requirement: Moon information across the dark window

**Reason**: It bundled three behaviors. It is split into "The moon object
carries its illumination and phase", "The moon object reports whether and when
the moon is up during the dark window" and "Moon horizon crossings use the
moon's geometric centre at 0 degrees". Its 3 scenarios move word for word, and
one scenario is added.

**Migration**: Nothing changes for users or code. Later changes MODIFY the new
requirements.

### Requirement: Astronomical fields are computed offline with stable precision

**Reason**: It bundled three behaviors. It is split into "Astronomical fields
are computed offline from bundled data", "Astronomical numbers and document
timestamps have a fixed precision from construction" and "Repeated runs on one
platform yield byte-identical astronomical values". Its 2 scenarios move word
for word, and one scenario is added.

**Migration**: Nothing changes for users or code. Later changes MODIFY the new
requirements.
