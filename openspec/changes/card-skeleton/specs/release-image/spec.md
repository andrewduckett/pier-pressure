## MODIFIED Requirements

### Requirement: A release passes the project checks first

Before it builds anything, the release SHALL run the project's full check gate
(lint, type check and tests) and the card's type check, tests and build against
the commit it releases. If any check fails, the release SHALL stop. It SHALL
then push no image, create no tag and create no GitHub release.

#### Scenario: Checks fail

- **WHEN** the maintainer triggers a release and a check fails on the commit
- **THEN** the release stops with a failure
- **AND** no image, tag or GitHub release exists for that run

#### Scenario: A card test fails

- **WHEN** the maintainer triggers a release and one of the card's tests fails on the commit
- **THEN** the release stops with a failure
- **AND** no image, tag or GitHub release exists for that run

#### Scenario: Checks pass

- **WHEN** the maintainer triggers a release and every check passes
- **THEN** the release goes on to compute the version and build the image

## ADDED Requirements

### Requirement: The release attaches the card

Each GitHub release SHALL carry the dashboard card's built file,
`pierpressure-card.js`, as an asset. The release SHALL build that file from the
released commit with the release version in it, before it pushes the image. If
the card build fails, the release SHALL push no image, create no tag and create
no GitHub release.

#### Scenario: The card ships with the release

- **WHEN** release `2026.11.0` completes
- **THEN** the GitHub release `2026.11.0` has an asset named `pierpressure-card.js`
- **AND** loading that file shows `2026.11.0` as the card's version

#### Scenario: The card build fails

- **WHEN** the maintainer triggers a release and the card fails to build
- **THEN** the release stops with a failure
- **AND** no image, tag or GitHub release exists for that run
