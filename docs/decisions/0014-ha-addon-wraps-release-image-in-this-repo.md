---
id: adrs-adr0014
date: 2026-10-03
status: accepted
title: 'ADR0014: The Home Assistant add-on lives in this repository and runs the released image'
description: Architecture Decision Record for packaging PierPressure as a Home Assistant add-on from the main repository, pulling the published release image rather than building on the user's machine, with releases proposing each add-on version update as a pull request.
---

# ADR-0014: The Home Assistant add-on lives in this repository and runs the released image

## Context

PierPressure is a Python service that publishes a nightly observing verdict to
Home Assistant over MQTT. Each release publishes one container image for amd64
and arm64 computers. Many Home Assistant users run Home Assistant OS. Home
Assistant OS cannot run arbitrary containers. Its users can only install
add-ons, which Home Assistant also calls apps.

An add-on is a folder of metadata in a Git repository. Users add that
repository's URL in Home Assistant, and Home Assistant installs add-ons from it.
That URL is hard to change later. Every user who added it would have to remove it
and add a new one by hand. Home Assistant can either build an add-on's image on
the user's machine, or pull a published image. It offers users an update only
when the add-on's version field changes in the repository.

The project's releases never commit to the default branch. The release version
lives only in the release's git tag.

## Decision

Keep the add-on in this repository: a `repository.yaml` at the root and one
add-on folder. The add-on pulls the published release image at a pinned release
version. Home Assistant never builds it.

After each release publishes its image and tag, the release opens a pull request
that changes the add-on's version. The maintainer merges that pull request to
deliver the update to add-on users.

## Consequences

- **Easier:** Docker users and add-on users run the identical image. A bug report
  from either group is about the same build.
- **Easier:** users add the project's own URL. One repository holds the code,
  the releases and the add-on, so they cannot fall out of step unnoticed.
- **Easier:** small machines such as a Raspberry Pi install in seconds, because
  they pull an image instead of building Python dependencies.
- **Harder:** each release needs one more merge before add-on users see it.
  This also lets the maintainer hold an update back from add-on users.
- **Harder:** the add-on supports only the platforms the release builds. Adding a
  platform means changing the release build first.
- **Harder:** Home Assistant downloads the whole project repository to read one
  add-on folder. The repository is small, so this is a minor cost.

## Alternatives Considered

### Alternative 1: A separate add-on repository
- **Pros**: Home Assistant downloads only the add-on files. Add-on commits stay
  out of the project's history.
- **Cons**: two repositories to keep in step. The version update would cross
  repositories and need a token with access to both.
- **Why not**: the add-on is packaging only. A second repository adds upkeep and
  gives no benefit to users.

### Alternative 2: Home Assistant builds the image from a Dockerfile in the add-on folder
- **Pros**: no registry needed, and the add-on always matches its folder.
- **Cons**: slow installs on small machines. The add-on image can differ from the
  release image that Docker users run.
- **Why not**: one image for every user matters more than avoiding a registry
  the project already uses.

### Alternative 3: The release commits the new add-on version straight to the default branch
- **Pros**: add-on users get each release with no extra step.
- **Cons**: an automated process writes to the default branch, which only takes
  reviewed pull requests.
- **Why not**: it breaks the rule that releases never commit, and it takes the
  timing of updates away from the maintainer.
