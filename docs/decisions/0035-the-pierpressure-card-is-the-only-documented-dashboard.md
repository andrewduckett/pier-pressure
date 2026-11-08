---
id: adrs-adr0035
date: 2026-11-08
status: accepted
title: 'ADR-0035: The PierPressure card is the only dashboard PierPressure documents'
description: Architecture Decision Record for retiring the YAML night dashboard, so the PierPressure card is the only Home Assistant dashboard PierPressure documents. It supersedes ADR-0034's sentence that the YAML dashboard stays.
---

# ADR-0035: The PierPressure card is the only dashboard PierPressure documents

## Context

ADR-0034 made PierPressure ship its own dashboard card, and kept the YAML
night dashboard in the docs for anyone who would not install a card. Since
then, PierPressure has had two dashboards. The card has grown past the YAML: it
shows the moon, the reasons, every timeline row and the target lanes, and every
recent story has built on the card only.

Two dashboards cause two problems:

- When a feature is designed, the two keep getting mixed up. A story has to
  say which dashboard it changes, and whether the other one follows.
- The YAML dashboard depends on the community plotly-graph-card, and its logic
  is JavaScript inside YAML that no test runs. The docs, a doc test and the
  dashboard check all keep it alive.

The maintainer is the only user, so nobody depends on the YAML dashboard.

## Decision

The PierPressure card is the only Home Assistant dashboard PierPressure
documents. The YAML night dashboard is removed: its docs page, its screenshot,
its spec and its doc test. Nothing is left at the old page's path.
`mise run dashboard-check` stays, and checks the card only.

This supersedes ADR-0034's sentence "The YAML dashboard in the docs stays, as
the route for anyone who will not install a card." The rest of ADR-0034
stands. With it, nothing of ADR-0026 stands.

## Consequences

- **Easier:** a story that changes the dashboard changes the card, with no
  second dashboard to keep in step.
- **Easier:** PierPressure no longer depends on plotly-graph-card, and the
  dashboard check downloads nothing.
- **Harder:** a person who will not install a custom card has no documented
  dashboard. They can still build their own from the published entities, which
  do not change.
- **Harder:** the old docs page's links break, with no note to say where it
  went. Archived changes keep their links as history.

## Alternatives Considered

### Alternative 1: Keep the YAML dashboard, marked as frozen
- **Pros**: a no-card route stays for anyone who wants one.
- **Cons**: it still has to be told apart from the card in every design, and
  its doc test and the dashboard check still carry it.
- **Why not**: the confusion is the problem, and a frozen copy keeps it.

### Alternative 2: Leave a stub page that points to the card
- **Pros**: old links still land somewhere useful.
- **Cons**: one more page to keep.
- **Why not**: the maintainer is the only user, so no outside links need to
  keep working.
