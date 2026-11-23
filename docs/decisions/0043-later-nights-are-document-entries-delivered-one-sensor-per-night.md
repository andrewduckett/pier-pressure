---
id: adrs-adr0043
date: 2026-11-22
status: accepted
title: 'ADR-0043: Later nights are entries in the verdict document, delivered one sensor per night'
description: Architecture decision record for carrying the nights after the selected night as a later_nights list of per-night entries in the verdict document, left out of the Verdict sensor's attributes and delivered to Home Assistant as one Night sensor per slot, Night 2 to Night 4.
---

# ADR-0043: Later nights are entries in the verdict document, delivered one sensor per night

Builds on ADR-0025.

## Context

The verdict judges one night, the selected night. The hourly timeline beside it
often reaches two or three days further (ADR-0025), so a dashboard can pan to
later nights, but it has nothing to frame them: no dusk, no dawn, and later no
moon or targets. The verdict document is a frozen contract. It may only grow,
and Home Assistant reads it through MQTT discovery entities. Home Assistant's
recorder does not store a state's attributes once they pass 16 KiB, so the
Verdict sensor can carry only a limited amount. A later night has no verdict, score or confidence
of its own. It is up to three nights of astronomy, one per local solar day
after the selected night.

## Decision

The verdict document gains a `later_nights` list after its other keys, with one
entry per later night in date order, up to three, and an empty list when the
forecast reaches no later night. Each entry is an object that holds that
night's fields in the same shapes as the selected night's top-level fields,
starting with `dark_window`. Fields for the moon and targets are added to the
entry when they arrive. Tonight's fields are never repeated in an entry and
never change.

The Verdict sensor's attributes leave out `later_nights`, as they leave out
`timeline`. Each pier gets three Night sensors, Night 2 to Night 4, one per
slot in the list. A Night sensor's state is that night's dusk as a timestamp,
and its attributes hold that night's entry. It is unavailable when its slot is
empty, and unknown but available when its night has no astronomical darkness.

## Consequences

- Easier: the next fields for a later night, such as its moon and targets, are
  new keys on an entry and new attributes on an existing sensor. No new
  entity, topic or document key is needed.
- Easier: a dashboard reads a later night from one sensor, with the same field
  names and shapes it already reads for tonight.
- Easier: the Verdict sensor's attributes stay the same size however many later
  nights there are, so they stay well under the 16 KiB limit.
- Harder: the number of Night sensors is fixed at three. Showing more nights
  needs new entities, not only a longer list.
- Harder: a later night's fields are spread over a list in the document and
  three sensors in Home Assistant, so a reader who wants every night must read
  four entities.
- Harder: "Night 2" names a slot, not a date. When the selected night moves on
  at dawn, every Night sensor's content moves one slot.

## Alternatives Considered

### Alternative 1: Per-field lists on the top level, such as `later_dark_windows`

- **Pros**: each list is small, and a dashboard that needs only dusk and dawn
  reads one key.
- **Cons**: every new field for a later night needs a new top-level key, and
  the lists must stay in step by position.
- **Why not**: the moon and targets for later nights are already planned, so
  this would add at least three parallel keys whose meaning depends on staying
  in the same order.

### Alternative 2: Keep the later nights in the Verdict sensor's attributes

- **Pros**: no new entities; a card reads one sensor as it does today.
- **Cons**: each later night's targets alone are up to ten objects, so three
  nights would multiply the attributes' size.
- **Why not**: with targets added, the attributes would pass the recorder's
  16 KiB limit, and the recorder would stop storing all of them, tonight's
  verdict details included.

### Alternative 3: One "Later nights" sensor holding the whole list

- **Pros**: one new entity per pier.
- **Cons**: its attributes would carry every later night's targets, so it
  meets the same size limit; and it has no single state that means something,
  such as a dusk time.
- **Why not**: it moves the size problem to another sensor instead of solving
  it, and automations could not trigger on one night's dusk.
