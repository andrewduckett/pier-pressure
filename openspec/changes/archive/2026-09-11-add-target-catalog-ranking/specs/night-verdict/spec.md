## ADDED Requirements

### Requirement: Targets list is an ordered ranked list

The `targets` field SHALL always be present as a list. Each element SHALL be a
structured target object with these fields: a designation (`id`), a common name
(`name`, null when the catalog records none), an object type (`type`), a ranking
`score` from 0 to 100, an observable `window` with a `start` and an `end`, a
`max_altitude` in degrees, a `transit_time`, and a `moon_separation` in degrees.
The list SHALL be ordered by `score`, highest first, with ties broken by `id`,
and SHALL contain at most the top 10 targets. The list SHALL be empty rather than
absent when no targets are rankable — for example when the selected night has no
dark window — so the contract shape is stable. Filling this list is additive: the
meaning of every other document field is unchanged.

#### Scenario: Targets list is present and ordered when targets are rankable

- **WHEN** a verdict is produced for a night with rankable targets
- **THEN** the `targets` field is a list of target objects, each with `id`, `name`, `type`, `score`, `window`, `max_altitude`, `transit_time`, and `moon_separation`
- **AND** the list is ordered by `score` descending, ties broken by `id`, and holds at most 10 targets

#### Scenario: Targets list present and empty when nothing is rankable

- **WHEN** a verdict is produced for a night with no dark window
- **THEN** the `targets` field is present and is an empty list

## REMOVED Requirements

### Requirement: Targets list is present and defaults empty

**Reason**: Superseded now that target ranking exists (milestone M5). The
`targets` field is no longer always empty; it carries an ordered ranked list, as
defined by the new "Targets list is an ordered ranked list" requirement above.

**Migration**: None for consumers that treated `targets` as an opaque list. A
consumer that relied on the list being empty SHALL instead read the structured
target objects defined by the replacement requirement; an empty list still
appears when no targets are rankable.
