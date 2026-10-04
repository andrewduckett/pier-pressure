## ADDED Requirements

### Requirement: The image carries Home Assistant add-on labels

The published image SHALL carry these labels, which Home Assistant reads from
add-on images:

- `io.hass.version`: the release version.
- `io.hass.type`: `addon`.

#### Scenario: Inspect the add-on labels

- **WHEN** an adopter inspects the labels of the image tagged `2026.10.1`
- **THEN** `io.hass.version` is `2026.10.1`
- **AND** `io.hass.type` is `addon`

### Requirement: A release proposes the add-on version update

After a release creates its tag and GitHub release, it SHALL open a pull request
against `main` that sets the add-on's `version` to the new release version. The
pull request SHALL change nothing else. The release SHALL NOT change `main`
itself, so the maintainer decides when add-on users see the update.

The release SHALL keep at most one version pull request open. When a release runs
while an earlier version pull request is still open, the release SHALL update that
pull request's change, title and description to the newest version.

If the release cannot open or update the pull request, the run SHALL fail with an
error that says so. The release SHALL NOT remove the image, tag or GitHub release
it has already published.

#### Scenario: Release opens the version pull request

- **WHEN** release `2026.10.1` completes and the add-on's version on `main` is
  `2026.10.0`
- **THEN** an open pull request against `main` sets the add-on version to
  `2026.10.1`
- **AND** the add-on config file is the only file it changes

#### Scenario: Earlier version pull request still open

- **WHEN** release `2026.10.2` completes while the pull request for `2026.10.1`
  is still open
- **THEN** exactly one version pull request is open
- **AND** it sets the add-on version to `2026.10.2`
- **AND** its title and description name `2026.10.2` and no earlier version

#### Scenario: Pull request cannot be opened

- **WHEN** the release pushes its image and creates its tag, but GitHub refuses to
  create the pull request
- **THEN** the release run fails with an error about the version pull request
- **AND** the image, the tag and the GitHub release for that version still exist

#### Scenario: Main is not changed by the release

- **WHEN** a release completes
- **THEN** the latest commit on `main` is the same as before the release
