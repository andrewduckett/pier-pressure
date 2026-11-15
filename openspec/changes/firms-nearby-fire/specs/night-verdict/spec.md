## ADDED Requirements

### Requirement: Only a confident, recent fire detection within 50 km counts

A fire detection SHALL count for the verdict only when all of these hold: its
confidence is `nominal` or `high`; its time is no later than the evaluation
instant and no more than 24 hours before it; and its great-circle distance from
the pier is at most 50 km.

#### Scenario: A low confidence detection does not count

- **WHEN** the pier's only fire detection is 10 km away, 3 hours before the evaluation instant, with confidence `low`
- **THEN** no fire detection counts

#### Scenario: A detection more than 24 hours old does not count

- **WHEN** the pier's only fire detection is 10 km away, with confidence `high`, 25 hours before the evaluation instant
- **THEN** no fire detection counts

#### Scenario: A detection after the evaluation instant does not count

- **WHEN** the pier's only fire detection is 10 km away, with confidence `high`, 1 minute after the evaluation instant
- **THEN** no fire detection counts

#### Scenario: A detection beyond 50 km does not count

- **WHEN** the pier's only fire detection is 51 km away, 3 hours before the evaluation instant, with confidence `nominal`
- **THEN** no fire detection counts

#### Scenario: A detection exactly 24 hours old counts

- **WHEN** the pier's only fire detection is 10 km away, with confidence `nominal`, exactly 24 hours before the evaluation instant
- **THEN** that fire detection counts

### Requirement: A counted fire detection adds one reason line that names the nearest

When at least one fire detection counts, `reasons` SHALL carry exactly one line
`A satellite detected a fire <distance> km <bearing> of the pier at <time> (<count>
within 50 km).`. `<distance>` and `<bearing>` are those of the nearest counted
detection. `<time>` is its time. `<count>` is `1 detection` or `<n>
detections`. With none counted, no such line SHALL appear.

#### Scenario: One detection

- **WHEN** the one counted fire detection is 23 km north-west of the pier, detected at `2026-11-13T07:35:00Z`
- **THEN** `reasons` contains `A satellite detected a fire 23 km NW of the pier at 2026-11-13T07:35:00Z (1 detection within 50 km).`

#### Scenario: Several detections name the nearest and the count

- **WHEN** four fire detections count, and the nearest is 8 km east of the pier, detected at `2026-11-13T05:54:00Z`
- **THEN** `reasons` contains `A satellite detected a fire 8 km E of the pier at 2026-11-13T05:54:00Z (4 detections within 50 km).`

#### Scenario: No counted detection, no line

- **WHEN** the pier has fire detections and none of them counts
- **THEN** no line in `reasons` starts with `A satellite detected a fire`

### Requirement: The fire line rounds the distance and gives an 8-point bearing

The fire line's distance SHALL be the great-circle distance in kilometres,
rounded to the nearest whole number, and at least 1. Its bearing SHALL be the
initial bearing from the pier to the fire, given as `N`, `NE`, `E`, `SE`, `S`,
`SW`, `W` or `NW`. Each point covers the 45° centred on it, with a bearing on a
boundary taking the next point clockwise.

#### Scenario: A fire close to the pier says 1 km

- **WHEN** the nearest counted fire detection is 0.3 km due south of the pier
- **THEN** the fire line says `1 km S of the pier`

#### Scenario: A bearing on a boundary goes clockwise

- **WHEN** the nearest counted fire detection is at a bearing of exactly 22.5° from the pier
- **THEN** the fire line gives the bearing `NE`

### Requirement: The nearest of equally near detections is the latest

When two or more counted fire detections are equally near, the fire line SHALL
name the one with the latest time. When those times are equal too, it SHALL
name the first of them in the order received.

#### Scenario: Two detections at the same distance

- **WHEN** two counted fire detections are both 12 km from the pier, one at `2026-11-13T05:54:00Z` and one at `2026-11-13T07:35:00Z`
- **THEN** the fire line names the time `2026-11-13T07:35:00Z`

### Requirement: The fire line follows the observation lines on every verdict

The fire line SHALL appear on every verdict with a counted fire detection, a
gated `NO-GO` and a night with no dark window included. It SHALL come after
every other line the core emits for the verdict, the observation line and the
observed-cloud line included, and before the equipment notes about the top
pick.

#### Scenario: The line follows the observation line

- **WHEN** a verdict is `GO` with a usable observation that does not lower confidence, and a counted fire detection, for a pier with no equipment
- **THEN** the last two reasons are the observation line and the fire line, in that order

#### Scenario: The line comes before the equipment notes

- **WHEN** a verdict is `GO` with a counted fire detection, for a pier with equipment and a top pick
- **THEN** the fire line comes before every equipment note

#### Scenario: A gated NO-GO keeps the line

- **WHEN** a verdict is `NO-GO` for an overcast dark window, with a counted fire detection and no observation
- **THEN** `reasons` names the overcast gate first
- **AND** its last line is the fire line

### Requirement: Fire detections change nothing but the fire line

Fire detections SHALL NOT change the verdict, the gates, the score, the
confidence, the agreement, the timeline, the targets or any key of the verdict
document. The document SHALL gain no key for them.

#### Scenario: The same verdict with and without fires

- **WHEN** two verdicts are produced for the same pier, instant and conditions, one with a counted fire detection and one with none
- **THEN** the two documents are equal except that the first one's `reasons` holds the fire line
