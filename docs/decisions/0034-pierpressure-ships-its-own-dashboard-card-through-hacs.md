---
id: adrs-adr0034
date: 2026-11-06
status: accepted
title: 'ADR-0034: PierPressure ships its own dashboard card, from this repository, through HACS'
description: Architecture Decision Record for shipping PierPressure's own Home Assistant dashboard card from this repository through HACS, released with the app. It replaces the decision to add no JavaScript card.
---

# ADR-0034: PierPressure ships its own dashboard card, from this repository, through HACS

> **Superseded in part on 2026-11-08 by ADR-0035.** The YAML dashboard in the
> docs is removed, so the sentence "The YAML dashboard in the docs stays, as the
> route for anyone who will not install a card" no longer holds. The rest
> stands: PierPressure ships its own card through HACS, and the card is now the
> only dashboard PierPressure documents.

## Context

PierPressure publishes its verdict and an hourly timeline to Home Assistant as
MQTT sensors. Until now its dashboard has been a block of YAML in the docs, on
Home Assistant's core cards plus the community plotly-graph-card. That YAML
cannot draw the night the way PierPressure means it. That view is one time
axis with the coloured condition rows, the darkness, the moon and the target
windows, each placed from the published entities. The logic it does have is JavaScript inside
the YAML, which no test runs.

A Home Assistant dashboard card is a JavaScript file the browser loads from a
URL. An add-on cannot serve it: dashboard resources need a URL the browser
loads directly, and add-on ingress URLs do not qualify. HACS, the Home
Assistant Community Store, installs cards from a GitHub repository. It reads
`hacs.json` at the repository root and takes the card's file from the latest
GitHub release. The Supervisor reads a different root file, `repository.yaml`,
for add-ons, so one repository can be both. HACS gives a repository one
category, so a repository that holds cards can never also hold a HACS custom
integration.

PierPressure already cuts each release from this repository, with a monthly
CalVer version. The card reads entities whose names and attributes change only
when PierPressure changes.

## Decision

PierPressure ships its own dashboard card, built from source in this
repository with Lit and TypeScript into one JavaScript file. The repository is
a HACS Dashboard repository as well as the add-on repository. Each release
builds the card with the release version and attaches the file to the GitHub
release, so the card's version is always the app's. The card only displays
published entities: it never computes a verdict or fetches data.

This supersedes ADR-0026's decision that PierPressure adds no JavaScript card
of its own. The YAML dashboard in the docs stays, as the route for anyone who
will not install a card.

## Consequences

- **Easier:** the card can draw exactly the night PierPressure means, with
  logic that the project's tests run.
- **Easier:** a card and the entities it reads always come from the same
  release, so the card needs no version check against the document. It only
  has to tolerate a missing entity or attribute.
- **Easier:** users install and update the card from HACS, as they do other
  cards, with no YAML to paste.
- **Harder:** PierPressure now has a frontend: Node and npm in the toolchain, a
  JavaScript dependency tree to keep updated, and a card build in CI and in
  every release.
- **Harder:** the card depends on Home Assistant's frontend loading custom
  cards and its `ha-card` element. A frontend release can break it, and only a
  person looking at a real Home Assistant sees how it renders.
- **Harder:** this repository can never also be a HACS custom integration.
  PierPressure has none, and its core stays outside Home Assistant.
- **Harder:** a card fix ships only with a full release of the app.

## Alternatives Considered

### Alternative 1: Keep only the YAML dashboard
- **Pros**: no frontend code, build or release asset; readers can edit every
  part of it.
- **Cons**: it cannot draw the strip PierPressure wants, its logic is untested
  JavaScript inside YAML, and it depends on a community card's releases.
- **Why not**: the strip it can draw is the ceiling, and that is not the night
  view PierPressure needs. It stays as the no-card route instead.

### Alternative 2: A separate repository for the card
- **Pros**: the card releases on its own schedule; this repository keeps no
  JavaScript.
- **Cons**: the card and the entities it reads would be versioned apart, so
  the card would need to detect which entity shapes it can read, and users
  would add two repositories.
- **Why not**: release pairing is what lets the card skip version detection.
  A second repository throws it away for a release schedule nobody needs.

### Alternative 3: Bundle the card in a Home Assistant custom integration
- **Pros**: one install could serve the card and register it as a resource.
- **Cons**: it puts PierPressure code inside Home Assistant's process, and the
  integration would be only a file server.
- **Why not**: PierPressure keeps all of its code outside Home Assistant's
  process, and an integration that only serves a file costs more than HACS's
  own card install.
