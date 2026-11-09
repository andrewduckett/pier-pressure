## ADDED Requirements

### Requirement: Each target carries its identity, ranking and observing fields

Each element of `targets` SHALL be a structured target object with these fields:
a designation (`id`), a common name (`name`, null when the catalog records
none), an object type (`type`), a ranking `score` from 0 to 100, an observable
`window` with a `start` and an `end`, a `max_altitude` in degrees, a
`transit_time`, and a `moon_separation` in degrees.

#### Scenario: Targets list is present and ordered when targets are rankable

- **WHEN** a verdict is produced for a night with rankable targets
- **THEN** the `targets` field is a list of target objects, each with `id`, `name`, `type`, `score`, `window`, `max_altitude`, `transit_time`, `moon_separation`, `size_arcmin`, `magnitude`, and `surface_brightness`
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

### Requirement: The score is the product of four factors

The score SHALL be the product of four factors, each from 0 to 1, scaled to 100
and rounded to the nearest integer. The factors are:

- the **usable-sky term**: the share of the scored window that is usably clear. This is the dominant term;
- the **atmosphere factor**: `0.7 + 0.3 × A`, defined below;
- the **moon factor**: the moon's brightness weighted by how much of the usably clear scored window it is above the horizon, as today;
- the **high-cloud factor**, as today.

#### Scenario: Better seeing and transparency never lower the score

- **WHEN** two nights are identical in cloud, high cloud and moon, and one has better seeing and transparency in its usably clear hours
- **THEN** the night with the better seeing and transparency has a score no lower than the other
- **AND** when the usable-sky term is 1, the moon is down, no high cloud is present, and seeing and transparency move from 0 to 1, the `score` moves from 70 to 100

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

### Requirement: More cloud never raises the usable-sky term times the atmosphere factor

More cloud SHALL NOT raise the product of the usable-sky term and the atmosphere
factor. That holds for any pattern of missing seeing and transparency, because
an hour without data counts as 1.

The moon and high-cloud factors keep today's rules. Each is a ratio over the
usably clear hours. Clouding out the one hour that carried the moon or the
cirrus can therefore still raise the score. The spec does not promise
monotonicity in cloud through those two factors. Issue #112 covers that gap.

#### Scenario: Clouding out a poor-atmosphere hour never raises the score

- **WHEN** a scored window has ten clear hours, eight with no seeing or transparency, one with both at 1, and one with both at 0, the moon is down throughout, and no high-cloud component is present
- **THEN** the `score` is 97
- **AND** when the hour with both at 0 is made overcast instead, the `score` is 90

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

When the wind-gust limit is treated as unavailable this way, and no hour with
wind data has already failed the gate, the verdict SHALL NOT be `GO` and SHALL
be capped at `MAYBE`, with a reason that wind data is unavailable and lowered
confidence.

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

#### Scenario: A pier configuration sets all three tuning knobs

- **WHEN** a pier configuration sets a go-threshold of 70, a wind-gust limit of 45 and a dew margin of 3
- **THEN** the pier's go-threshold is 70, its wind-gust limit is 45 and its dew margin is 3 °C

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

## REMOVED Requirements

### Requirement: Targets list is an ordered ranked list

**Reason**: It bundled five behaviors. It is split into "Each target carries its
identity, ranking and observing fields", "Each target carries its catalog size,
magnitude and surface brightness", "The targets list is ordered by score and
holds at most 10 targets", "The targets list is always present, and empty when
nothing is rankable" and "Target catalog values are emitted at a fixed
precision". Its 3 scenarios move word for word. Two scenarios are added.

**Migration**: Nothing changes for users or code. Later changes MODIFY the new
requirements.

### Requirement: Hard gates decide a NO-GO

**Reason**: It bundled five behaviors. It is split into "A failed hard gate is
the only cause of a NO-GO", "A failed hard gate leaves the score null and names
the gate", "A selected night with no dark window fails a hard gate", "The
overcast gate fails when every part of the scored window with cloud data is
overcast" and "The wind gate fails when the forecast gust exceeds a configured
limit". Its 4 scenarios move word for word. One scenario is added.

**Migration**: Nothing changes for users or code. Later changes MODIFY the new
requirements.

### Requirement: A banded score decides GO versus MAYBE

**Reason**: It bundled ten behaviors. It is split into "A gate-passing night
gets a deterministic integer score from 0 to 100", "The score is the product of
four factors", "A half-way score rounds to the even integer", "The atmosphere
factor rests on a clarity-weighted mean of each hour's quality", "The score
never exceeds the usable-sky term", "GO needs a score at the go-threshold, cloud
data and no cap", "A brighter night never scores higher", "More cloud never
raises the usable-sky term times the atmosphere factor" and "The reasons explain
the atmosphere factor". Its rule for a scored window with no seeing or
transparency joins "Missing seeing or transparency drops only its own
contribution", with its scenario. Its 8 scenarios move word for word. Three
scenarios are added.

**Migration**: Nothing changes for users or code. Later changes MODIFY the new
requirements.

### Requirement: The verdict degrades honestly when conditions are unavailable

**Reason**: It bundled six behaviors. It is split into "A verdict is always
produced when conditions are missing", "Missing seeing or transparency drops
only its own contribution", "The hard gates come before the missing-cloud rule",
"A wind-gust limit that wind data does not fully cover is unavailable", "An
unavailable wind-gust limit caps the verdict at MAYBE" and "Entirely missing
cloud data gives MAYBE with a score of 0". Its 5 scenarios move word for word.
No scenario is added.

**Migration**: Nothing changes for users or code. Later changes MODIFY the new
requirements.

### Requirement: Optional pier tuning configuration

**Reason**: It bundled five behaviors. It is split into "A pier has three
optional tuning knobs and no others", "An omitted go-threshold takes the system
default", "An omitted wind-gust limit disables the wind gate", "The dew margin
defaults to 4 °C, and 0 turns the dew line off" and "A negative or non-finite
dew margin is a configuration error". Its 4 scenarios move word for word. One
scenario is added.

**Migration**: Nothing changes for users or code. Later changes MODIFY the new
requirements.

### Requirement: High, thin cloud is a distinct score penalty

**Reason**: It bundled six behaviors. It is split into "High, thin cloud has a
score penalty apart from total cloud", "The high-cloud penalty has its own
reason line", "More high cloud never raises the score", "The high-cloud penalty
only shapes the banded score", "The high-cloud penalty is weighted toward the
usably clear hours" and "A missing high-cloud component drops its own
contribution". Its 3 scenarios move word for word. Three scenarios are added.

**Migration**: Nothing changes for users or code. Later changes MODIFY the new
requirements.
