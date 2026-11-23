<!-- Plain language: Name the actor, condition and observable result. Explain necessary domain terms using the agreed glossary. Keep requirement and scenario headings and WHEN/THEN syntax exactly as required. -->

## ADDED Requirements

### Requirement: A later night is ranked over its whole dark window on its own moon

Each later night's targets SHALL be ranked by the rules that rank the selected
night's targets, with that later night's `dark_window` as the dark window and
its own `moon` as the moon. The evaluation instant is before every later
night's dusk, so a later night SHALL be ranked over its whole dark window: each
of its targets' `remaining_window` SHALL equal its `window`.

#### Scenario: The next night's top target

- **WHEN** a verdict is produced for a pier at latitude 51.5, longitude −0.12, elevation 30 m, at 2026-09-08T18:00:00Z, with a `cloud_cover` series that covers 2026-09-08T18:00:00Z to 2026-09-10T18:00:00Z
- **THEN** the first later night's first target has the `id` `NGC7394` and the score 99
- **AND** its `window` and its `remaining_window` both run from 2026-09-09T20:27:57Z to 2026-09-10T03:28:02Z

#### Scenario: A brighter moon changes the list

- **WHEN** a verdict is produced for the same pier at 2026-11-21T12:00:00Z, with a `cloud_cover` series that covers 2026-11-21T12:00:00Z to 2026-11-23T18:00:00Z
- **THEN** the top-level first target has the `id` `NGC1491`
- **AND** the first later night's first target has the `id` `IC0463`, and the second later night's has the `id` `NGC3690A`

#### Scenario: Every later night target's remaining window is its window

- **WHEN** a verdict is produced with at least one later night that has targets
- **THEN** every target of every later night has a `remaining_window` equal to its `window`

### Requirement: A recompute reuses the catalog scan of every night it ranked

Within one running process, a recompute for a pier SHALL NOT scan the catalog
again for a night whose dark window it scanned in that pier's previous
recompute, however many other piers were recomputed in between. The scan keeps
the ranking the same: a recompute's target lists SHALL be byte-identical to
those of a first computation at the same instant.

#### Scenario: Four nights of three piers

- **WHEN** three piers each with a selected night and three later nights are recomputed one after another, and then the first pier is recomputed again in the same night
- **THEN** the second recompute of the first pier scans the catalog for no night
- **AND** its target lists, top-level and for each later night, are byte-identical to those of a first computation at the same instant

#### Scenario: A new night is scanned once

- **WHEN** a pier at latitude 51.5, longitude −0.12, elevation 30 m is computed at 2026-09-08T18:00:00Z with three later nights, and recomputed at 2026-09-09T18:00:00Z with a forecast that also reaches three later nights
- **THEN** the recompute scans the catalog for one night only: its third later night, whose solar day starts on 2026-09-12
- **AND** the selected night of the recompute, from 2026-09-09T20:27:57Z to 2026-09-10T03:28:02Z, is not scanned again
