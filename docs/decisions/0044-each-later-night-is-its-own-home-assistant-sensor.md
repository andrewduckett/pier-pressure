---
id: adrs-adr0044
date: 2026-11-22
status: accepted
title: 'ADR0044: Each later night reaches Home Assistant as its own Night sensor, not through the Verdict attributes'
description: Architecture Decision Record. Each pier gets three Night sensors, Night 2 to Night 4. A sensor's state is its night's dusk as a timestamp and its attributes hold that night's entry, while the Verdict sensor's attributes leave the later nights out.
---

# ADR-0044: Each later night reaches Home Assistant as its own Night sensor, not through the Verdict attributes

## Context

The verdict document carries up to three later nights in a `later_nights` list,
one entry per night (ADR-0043). Home Assistant receives the document over MQTT
discovery. The Verdict sensor's attributes hold the document without its
timeline, and Home Assistant drops every attribute of an entity whose
attributes exceed 16 KiB. Each night's entry starts with a dark window, and
will soon hold a moon and up to ten ranked targets. Three such entries would
push the Verdict sensor past the limit. Cards and automations find PierPressure
entities by name, built from the pier's slug. The Target 1 to Target 10
sensors already use one sensor per item, with an `available` flag that makes
an empty item unavailable.

## Decision

Each pier gets three sensors, Night 2 to Night 4
(`sensor.pierpressure_<slug>_night_<n>`), where Night 2 is the first later
night. A sensor's state is its night's dusk as a timestamp, and its attributes
hold the night number and that night's entry. A sensor is unavailable when its
night is not in `later_nights`, and unknown when its night has no astronomical
darkness. The Verdict sensor's attributes leave out `later_nights`, as they
leave out `timeline`.

## Consequences

- **Easier:** the Verdict sensor stays the same size and shape for every
  automation that reads it today.
- **Easier:** each night stays well under the 16 KiB limit on its own, even
  with ten targets.
- **Easier:** an automation can trigger on, or show, one night's dusk with no
  template, because the state is a timestamp.
- **Easier:** a card finds a night by name, the way it finds Target 3.
- **Harder:** the number of later nights is fixed at three by the entity list.
  A fourth later night would need a new sensor and a change to every card that
  lists them.
- **Harder:** a consumer that wants every night reads three more entities.
- **Constraint accepted:** the three entity names, their state meaning and
  their attribute layout join the frozen delivery surface.

## Alternatives Considered

### Alternative 1: Carry `later_nights` in the Verdict sensor's attributes
- **Pros**: no new entities; a card reads one sensor.
- **Cons**: with each night's moon and ten targets, the attributes pass
  16 KiB, and Home Assistant then drops all of them, including the reasons and
  the dark window automations read today.
- **Why not**: it would break the product's main entity once the targets
  arrive.

### Alternative 2: One sensor holding every later night
- **Pros**: one new entity per pier.
- **Cons**: its state could not be a single night's dusk, so it would carry a
  count or a placeholder. Three nights of targets would push it toward the same
  16 KiB limit.
- **Why not**: it trades the Verdict sensor's size problem for the same problem
  on a new sensor, and gives automations nothing useful in the state.

### Alternative 3: A sensor per night per field, such as a dusk sensor and a dawn sensor
- **Pros**: every value is a plain state with no attributes to read.
- **Cons**: two or more entities per night now, more as fields arrive, and ten
  rank sensors per night would add 30 entities per pier.
- **Why not**: the entity count grows with every field, while one sensor per
  night grows only its attributes.
