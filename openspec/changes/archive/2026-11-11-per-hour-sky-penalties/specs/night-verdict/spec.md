## RENAMED Requirements

- FROM: `### Requirement: The score is the product of four factors`
- TO: `### Requirement: The score sums each hour's usable sky, scaled by that hour's factors`

- FROM: `### Requirement: More cloud never raises the usable-sky term times the atmosphere factor`
- TO: `### Requirement: More cloud never raises the score`

## MODIFIED Requirements

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

## ADDED Requirements

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
