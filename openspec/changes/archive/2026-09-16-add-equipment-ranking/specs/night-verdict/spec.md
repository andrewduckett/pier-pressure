## MODIFIED Requirements

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
