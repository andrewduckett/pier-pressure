## ADDED Requirements

### Requirement: A release opens a version pull request for the add-on

After a release creates its tag and GitHub release, it SHALL open a pull request
against `main` that sets the add-on's `version` to the new release version. This
is the version pull request. The pull request SHALL change nothing else.

#### Scenario: Release opens the version pull request

- **WHEN** release `2026.10.1` completes and the add-on's version on `main` is
  `2026.10.0`
- **THEN** an open pull request against `main` sets the add-on version to
  `2026.10.1`
- **AND** the add-on config file is the only file it changes

### Requirement: A release does not change `main`

The release SHALL NOT change `main` itself, so the maintainer decides when add-on
users see the update.

#### Scenario: Main is not changed by the release

- **WHEN** a release completes
- **THEN** the latest commit on `main` is the same as before the release

### Requirement: A release keeps at most one version pull request open

The release SHALL keep at most one version pull request open. When a release runs
while an earlier version pull request is still open, the release SHALL update that
pull request's change, title and description to the newest version.

#### Scenario: Earlier version pull request still open

- **WHEN** release `2026.10.2` completes while the pull request for `2026.10.1`
  is still open
- **THEN** exactly one version pull request is open
- **AND** it sets the add-on version to `2026.10.2`
- **AND** its title and description name `2026.10.2` and no earlier version

### Requirement: A failed version pull request fails the release run

If the release cannot open or update the version pull request, the run SHALL fail
with an error that says so. The release SHALL NOT remove the image, tag or GitHub
release it has already published.

#### Scenario: Pull request cannot be opened

- **WHEN** the release pushes its image and creates its tag, but GitHub refuses to
  create the pull request
- **THEN** the release run fails with an error about the version pull request
- **AND** the image, the tag and the GitHub release for that version still exist

## REMOVED Requirements

### Requirement: A release proposes the add-on version update

**Reason**: It stated four behaviors in more than 500 characters. It is split into "A release opens a version pull request for the add-on", "A release does not change `main`", "A release keeps at most one version pull request open" and "A failed version pull request fails the release run", which keep all of its SHALL statements and all four of its scenarios.
**Migration**: None. Nothing changes for users or code: the release workflow and its version pull request behave as before.
