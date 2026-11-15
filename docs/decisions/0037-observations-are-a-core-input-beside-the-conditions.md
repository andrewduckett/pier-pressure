---
id: adrs-adr0037
date: 2026-11-14
status: accepted
title: 'ADR-0037: Observations are a core input beside the conditions, never a provider'
description: Architecture decision record for carrying a measured observation, such as an airport's METAR, into the core as its own plain input beside the conditions snapshot, so that it never fills a variable, never joins the provider order and reaches the verdict document as its own additive key.
---

# ADR-0037: Observations are a core input beside the conditions, never a provider

Builds on ADR-0027.

## Context

Every input to the verdict has been a forecast. Forecasts enter through
providers in an ordered list, and the core fills each variable with one hourly
series from the first provider that returned it. A METAR is different: it is
one measurement of the sky at one moment, at an airport a few kilometres from
the pier. It covers no hours ahead, it sees cloud only up to a fixed height,
and it is often old by the time the night starts. Later work will compare it
with the forecast to adjust confidence, so how it enters the core shapes that
work too.

## Decision

An observation is a separate, optional input to the verdict, beside the
conditions snapshot. It is a plain data value: the station, when it was
measured, and what it reported. It never fills a variable, adds no series or
alternate to the snapshot, and is not a provider in the provider order. The
verdict document carries it as its own additive key, and the fetch that gets
it reports health as a provider's fetch does.

## Consequences

- **Easier:** the fill, agreement and every rule about series stay exactly as
  they are. No reader of the snapshot has to learn to skip a value that is not
  a forecast.
- **Easier:** a measurement can be judged on its own terms, such as its age at
  the evaluation instant, without pretending it is an hourly forecast.
- **Easier:** another kind of observation, from another station type, can join
  the same input without touching the providers.
- **Harder:** an observation cannot stand in for missing forecast cloud. A
  pier with a station but no cloud forecast still gets the missing-cloud
  verdict.
- **Harder:** the producer has one more input to thread through, and the
  service one more fetch to guard.

## Alternatives Considered

### Alternative 1: METAR as a provider in the order that fills `cloud_cover`
- **Pros**: reuses the provider order, health and the fill with no new seam.
- **Cons**: a single report would fill one hour of cloud cover, or be held
  across the night as if it were a forecast. Its cover codes and its 12,000 ft
  ceiling do not map to a percentage of the whole sky.
- **Why not**: it would present a measurement of the past as a forecast of the
  night, and a clear report would look like a clear night.

### Alternative 2: A field on the conditions snapshot
- **Pros**: one value still carries everything the providers fetched.
- **Cons**: the snapshot is defined as one series per variable. Every reader
  of it would have to know that one field is not a series.
- **Why not**: it blurs the snapshot's single meaning for no gain over a
  separate input.
