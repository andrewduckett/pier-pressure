# release-image Specification

## Purpose

The release-image capability lets the maintainer cut a versioned release with one
manual action. It also defines what an adopter can rely on in the published
container image: where it lives, how it is tagged, which platforms it runs on, and
how it reports its version.

## Requirements

### Requirement: Maintainer starts a release by hand from main

The release SHALL start only when the maintainer triggers it by hand. It SHALL
release only the latest commit on the `main` branch. A merge to `main` SHALL NOT
start a release on its own.

#### Scenario: Release started from main

- **WHEN** the maintainer triggers the release on the `main` branch
- **THEN** the release runs against the latest commit on `main`

#### Scenario: Release started from another branch

- **WHEN** the maintainer triggers the release on any branch other than `main`
- **THEN** the release fails before it builds, pushes or tags anything

#### Scenario: Merge does not release

- **WHEN** a pull request merges into `main`
- **THEN** no release runs, no image is pushed and no tag is created

### Requirement: A release passes the project checks first

Before it builds anything, the release SHALL run the project's full check gate
(lint, type check and tests) against the commit it releases. If any check fails,
the release SHALL stop. It SHALL then push no image, create no tag and create no
GitHub release.

#### Scenario: Checks fail

- **WHEN** the maintainer triggers a release and a check fails on the commit
- **THEN** the release stops with a failure
- **AND** no image, tag or GitHub release exists for that run

#### Scenario: Checks pass

- **WHEN** the maintainer triggers a release and every check passes
- **THEN** the release goes on to compute the version and build the image

### Requirement: Versions follow monthly CalVer

Each release SHALL get a version of the form `YYYY.M.N`:

- `YYYY` is the four-digit year and `M` is the month number without a leading
  zero. Both come from the UTC date when the release runs.
- `N` is a counter that starts at `0` for the first release of a month. Each
  later release in the same month adds 1 to the highest `N` already tagged for
  that month.

The version SHALL contain no prefix, such as `v`, and no leading zeros.

#### Scenario: First release of a month

- **WHEN** a release runs on 2026-10-03 UTC and no tag matches `2026.10.*`
- **THEN** the release version is `2026.10.0`

#### Scenario: Later release in the same month

- **WHEN** a release runs in October 2026 and the tags `2026.10.0` and
  `2026.10.1` exist
- **THEN** the release version is `2026.10.2`

#### Scenario: Counter resets in a new month

- **WHEN** a release runs on 2026-11-01 UTC, the tag `2026.10.4` exists, and no
  tag matches `2026.11.*`
- **THEN** the release version is `2026.11.0`

#### Scenario: Counter compares numbers, not text

- **WHEN** a release runs in October 2026 and the tags `2026.10.9` and
  `2026.10.10` exist
- **THEN** the release version is `2026.10.11`

### Requirement: Each commit is released at most once

The release SHALL fail if the commit it would release already carries a release
version tag. It SHALL then push no image and create no tag or GitHub release.

#### Scenario: Commit already released

- **WHEN** the maintainer triggers a release and the latest commit on `main`
  already has the tag `2026.10.0`
- **THEN** the release fails with a message naming the existing version
- **AND** it pushes no image and creates no new tag

### Requirement: Releases never share a version

Two releases SHALL NOT receive the same version. When the maintainer triggers a
second release while one is still running, the second SHALL wait for the first
to finish before it computes its version. At most one release SHALL wait at a
time. A newer trigger SHALL cancel the waiting release before that release
starts. A cancelled release SHALL push no image and create no tag or GitHub
release.

#### Scenario: Two releases triggered close together

- **WHEN** the maintainer triggers two releases a few seconds apart
- **THEN** the second release starts its work only after the first has finished
- **AND** the two runs never compute the same version

#### Scenario: Third release triggered while one waits

- **WHEN** one release is running, a second is waiting, and the maintainer
  triggers a third
- **THEN** GitHub cancels the second release before it pushes an image or
  creates a tag
- **AND** the third release waits for the first to finish

### Requirement: The image is published to GHCR for amd64 and arm64

A successful release SHALL push one multi-platform image to
`ghcr.io/andrewduckett/pier-pressure`. The image SHALL run on `linux/amd64` and
`linux/arm64`. The image SHALL be tagged with the release version and with
`latest`. After the release, `latest` SHALL point to the same image as the newest
version tag.

#### Scenario: Pull a pinned version

- **WHEN** an adopter runs `docker pull ghcr.io/andrewduckett/pier-pressure:2026.10.0`
  after release `2026.10.0`
- **THEN** the pull succeeds on both an amd64 host and an arm64 host

#### Scenario: Latest follows the newest release

- **WHEN** release `2026.10.1` completes after release `2026.10.0`
- **THEN** the `latest` tag has the same image digest as the `2026.10.1` tag

### Requirement: The image carries its version in OCI labels

The published image SHALL carry these OCI (Open Container Initiative) labels:

- `org.opencontainers.image.version`: the release version.
- `org.opencontainers.image.revision`: the full git commit SHA that was released.
- `org.opencontainers.image.source`: the repository URL.

The image index that groups the platforms SHALL carry the same three values as
OCI annotations.

#### Scenario: Inspect the index annotations

- **WHEN** an adopter reads the raw image index of the tag `2026.10.0`, for
  example with `docker buildx imagetools inspect --raw`
- **THEN** its annotations include `org.opencontainers.image.version` set to
  `2026.10.0`
- **AND** its annotations include `org.opencontainers.image.revision` and
  `org.opencontainers.image.source` with the same values as the labels

#### Scenario: Inspect the labels

- **WHEN** an adopter inspects the labels of the image tagged `2026.10.0`
- **THEN** `org.opencontainers.image.version` is `2026.10.0`
- **AND** `org.opencontainers.image.revision` is the SHA of the tagged commit
- **AND** `org.opencontainers.image.source` is
  `https://github.com/andrewduckett/pier-pressure`

### Requirement: The release tags the commit only after it pushes the image

After it pushes the image, the release SHALL tag the released commit with the
version. It SHALL also create a GitHub release with the same name and
automatically generated notes. If the image build or push fails, the release
SHALL create no tag and no GitHub release.

#### Scenario: Successful release

- **WHEN** the image for `2026.10.0` is pushed successfully
- **THEN** the git tag `2026.10.0` points at the released commit
- **AND** a GitHub release named `2026.10.0` exists with generated notes

#### Scenario: Image push fails

- **WHEN** the image build or push fails
- **THEN** no git tag and no GitHub release exist for that version

### Requirement: The running service reports its version

The service SHALL log its version as the first thing it logs on startup, before it
loads its configuration. In a released image, the logged version SHALL equal the
release version.

#### Scenario: Released image starts

- **WHEN** an adopter starts the image tagged `2026.10.0`
- **THEN** the first log line contains `2026.10.0`

#### Scenario: Configuration is invalid

- **WHEN** the service starts with a configuration file that fails to load
- **THEN** the version log line appears before the configuration error

### Requirement: Builds outside a release do not claim a release version

A build made outside the release workflow SHALL NOT report a version that looks
like a release. A build from a git checkout reports a development version derived
from the nearest release tag. An image built without git history reports a
placeholder version that is not CalVer.

#### Scenario: Local image build

- **WHEN** a developer runs `docker build .` without passing a version
- **THEN** the service in that image logs a version that does not match `YYYY.M.N`

#### Scenario: Development checkout after a release

- **WHEN** a developer runs the service from a checkout three commits after the
  tag `2026.10.0`
- **THEN** the logged version is a development version, not `2026.10.0`
