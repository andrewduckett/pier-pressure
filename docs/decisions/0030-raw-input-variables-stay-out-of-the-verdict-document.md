---
id: adrs-adr0030
date: 2026-11-03
status: accepted
title: 'ADR-0030: Raw input variables stay out of the verdict document'
description: Architecture decision record for carrying raw input variables, such as aerosol optical depth, in the conditions snapshot only, so that the timeline shows a fixed subset of the variables and a variable it does not show never adds a key or an hour to the verdict document.
---

# ADR-0030: Raw input variables stay out of the verdict document

Builds on ADR-0025.

## Context

The conditions snapshot holds one series per variable, and until now every
variable also became a key of each timeline entry in the verdict document.
ADR-0025 made those keys part of the frozen contract: the document only
grows, so a key, once published, can never be removed or renamed. Some
variables are now raw inputs to core math rather than evidence a person reads:
aerosol optical depth and fine particulates, and later column water vapour and
layer temperatures. Their meaning to a reader is weak until the core turns
them into an index such as transparency, and the index that reads them may
change which inputs it needs.

## Decision

A variable is either shown or raw. The core holds one fixed list of the
variables the timeline shows. A raw variable travels in the conditions
snapshot only. It never becomes a timeline key, and it never adds a timeline
hour, so two snapshots that differ only in raw variables yield byte-identical
verdict documents. A raw variable reaches the document only through a shown
variable that the core computes from it.

## Consequences

- **Easier:** a provider of raw inputs can be added, reordered or dropped with
  no effect on the frozen contract, the Home Assistant sensors or the
  dashboard.
- **Easier:** computed indices can change which raw inputs they read without
  leaving dead keys in the document.
- **Easier:** an empty timeline still means that no provider returned anything
  a person can read, even when a raw-input provider succeeded.
- **Harder:** a raw value cannot be inspected from Home Assistant. Someone who
  wants to see aerosol optical depth must read the provider's response or the
  logs, or wait for the computed index.
- **Harder:** adding a variable now needs a choice: shown or raw. Making a raw
  variable shown later is an additive change, so it stays possible. Making a
  shown variable raw is not, because its key is already part of the contract.

## Alternatives Considered

### Alternative 1: Every variable is a timeline key, as ADR-0025 first described
- **Pros**: one rule for all variables; every value is visible in Home
  Assistant with no extra work.
- **Cons**: each raw input becomes a permanent key and a permanent sensor, and
  a later choice of different inputs leaves keys that nothing fills.
- **Why not**: the contract only grows, so publishing an input whose use is not
  settled yet commits the document to it for good.

### Alternative 2: Raw variables in a separate block of the document
- **Pros**: raw values are visible to a reader of the document without touching
  the timeline entries.
- **Cons**: the block's shape would have to be fixed before the indices that
  read the inputs exist, and it becomes frozen like any other field.
- **Why not**: it reserves a shape before the change that defines it. Add such
  a block when there is a reader for it.
