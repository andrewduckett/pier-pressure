## MODIFIED Requirements

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
