---
id: adrs-adr0013
date: 2026-10-03
status: accepted
title: 'ADR0013: Release versions are monthly CalVer, and the git tag is their only source'
description: Architecture Decision Record for numbering PierPressure releases as YYYY.M.N calendar versions. Each version lives only in its git tag, and the package and the image read it from there.
---

# ADR-0013: Release versions are monthly CalVer, and the git tag is their only source

## Context

PierPressure ships as a container image that people run at home, usually beside
Home Assistant. Adopters pin an image version so that an update never surprises
them. Once adopters pin a numbering scheme, changing it is costly. Every pinned
tag, upgrade note and automation that compares versions depends on it.

The project also needs one place where the version lives. Before this decision,
the maintainer wrote the version `0.1.0` by hand in two source files, and the
package manager copied it into the lockfile. Nothing kept the copies in step. The default branch only accepts
reviewed pull requests, so an automated release cannot commit a version bump to
it. The container build also has no access to git history.

## Decision

Number releases with calendar versioning (CalVer) in the form `YYYY.M.N`. `YYYY`
is the year and `M` is the month, without a leading zero. `N` counts releases
within the month, starting at 0. The first release in October 2026 is therefore
`2026.10.0`.

Store each version only as a git tag on the released commit. The package build
reads the version from the tag. The release process passes the same value into
the container build, because the build cannot see git. No source file holds a
version number.

## Consequences

- **Easier:** a version tells adopters when a build was released. The format
  matches Home Assistant's own scheme, which the project's adopters already know.
- **Easier:** the package and the image cannot disagree about their version.
  Cutting a release needs no commit, so it works with a protected default branch.
- **Easier:** a build that is not a release says so. A development checkout
  reports a development version, and an image built locally reports a
  placeholder.
- **Harder:** CalVer says nothing about compatibility. The maintainer must
  announce a breaking change in the release notes, because the number cannot
  signal it.
- **Harder:** the build depends on a version plugin and on git tags being
  present. A shallow clone without tags reports a placeholder version, not an
  error.

## Alternatives Considered

### Alternative 1: Semantic versioning (`MAJOR.MINOR.PATCH`)
- **Pros**: the number signals breaking changes, and Python tooling expects it.
- **Cons**: someone must judge each release's impact. The project has no public
  API beyond its configuration and its Home Assistant entities.
- **Why not**: the delivery surface is frozen, so major versions would almost
  never move. Dates tell adopters more about how current a build is.

### Alternative 2: A version number committed in the source
- **Pros**: anyone can read the version in the source tree, and no plugin is
  needed.
- **Cons**: a release needs a commit on the protected default branch, or a pull
  request for every release. Copies of the number drift apart.
- **Why not**: it breaks the one-action release and keeps the drift problem this
  decision removes.

### Alternative 3: Stamp the version into the container image only
- **Pros**: the simplest change. It needs only a build argument and a label.
- **Cons**: the Python package would report a different version from the image
  that contains it.
- **Why not**: two answers to "which version is this?" defeat the purpose.
