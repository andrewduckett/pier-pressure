---
id: adrs-adr0043
date: 2026-11-22
status: accepted
title: 'ADR0043: Later nights are a list of per-night entries after the verdict document''s existing fields'
description: Architecture Decision Record. The verdict document carries the nights after the selected night as a later_nights list, one entry per night in date order, each holding that night's fields in the same shapes as the top-level ones. Tonight's fields stay where they are, and no later night gets a verdict.
---

# ADR-0043: Later nights are a list of per-night entries after the verdict document's existing fields

## Context

The verdict document judges one night, the selected night, and is a frozen
contract. Existing fields never move or change meaning, and new fields are
only added. Its hourly timeline already reaches about 72 hours ahead, as
evidence beside the verdict (ADR-0025), so a dashboard can pan to the next two
or three nights. But only the selected night has a dark window, moon and
targets in the document. A later night is one local solar day after the
selected night's, counted while the timeline holds an hour that starts inside
it, up to three. Each later night needs its own dark window now, and its own
moon and ranked targets next. The gates and the confidence are built for the
selected night's lead time, so a later night gets no verdict, score or
confidence.

## Decision

The document gains `later_nights`, a list after every existing field. It holds
one entry per later night, in date order. Each entry holds that night's fields
in the same shapes as the top-level ones: first `dark_window`, with `moon` and
`targets` to follow. The selected night's fields stay at the top level, and are
not repeated in the list. An entry never carries `verdict`, `score`,
`confidence` or `reasons`.

## Consequences

- **Easier:** every consumer that reads tonight's fields keeps working
  unchanged, because nothing existing moves.
- **Easier:** a reader of a later night uses the same code it uses for
  tonight's `dark_window`, `moon` and `targets`, because the shapes are the
  same.
- **Easier:** a later night grows by adding a key to its entry, and each entry
  stays self-contained. Adding `moon` and `targets` changes no key that already
  exists.
- **Harder:** a consumer that wants every night must read two places: the top
  level for the selected night, and `later_nights` for the rest. The list
  starts at the second night.
- **Harder:** the absence of a verdict in an entry is deliberate. A later
  per-night verdict would be its own decision, and would add keys to the
  entries, not reuse the top-level ones.
- **Constraint accepted:** the entry's position and its existing keys are now
  part of the frozen contract.

## Alternatives Considered

### Alternative 1: A `nights` list that includes the selected night
- **Pros**: one shape for every night; a consumer reads one list.
- **Cons**: tonight's `dark_window`, `moon` and `targets` would either move
  into the list, which breaks every existing consumer, or appear twice.
- **Why not**: moving them breaks the frozen contract, and repeating them gives
  two copies of one fact that a future change could let drift apart.

### Alternative 2: Parallel top-level lists, such as `later_dark_windows` and `later_moons`
- **Pros**: each list is flat and easy to read on its own.
- **Cons**: a night is spread across lists tied together only by position, and
  every new per-night field adds another top-level key.
- **Why not**: a consumer must zip lists by index and trust that they have the
  same length. One entry per night keeps a night's facts together.

### Alternative 3: An object keyed by each night's date
- **Pros**: a consumer can look a night up by date.
- **Cons**: a night spans two calendar dates and belongs to a local solar day,
  so the key's meaning is ambiguous. JSON object order is not something every
  consumer keeps.
- **Why not**: a list in date order needs no key convention, and its order is
  the contract.

### Alternative 4: One full verdict document per night
- **Pros**: every night gets everything, including a verdict.
- **Cons**: the gates, the score and the confidence assume the selected night's
  lead time, and their meaning for a night two days out is undecided.
- **Why not**: it would publish verdicts whose meaning nobody has defined, and
  it would multiply the delivery surface by the number of nights.
