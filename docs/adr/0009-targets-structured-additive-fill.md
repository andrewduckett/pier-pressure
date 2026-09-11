---
id: adrs-adr0009
date: 2026-09-11
status: accepted
title: 'ADR0009: The targets field is filled additively with a structured, numbers-only target element'
description: Architecture Decision Record for defining the frozen shape of the verdict document's targets list as structured target objects (id, name, type, score, window, max_altitude, transit_time, moon_separation), filling a reserved-but-shapeless stub without changing any other field, and carrying no per-target prose.
---

# ADR-0009: The targets field is filled additively with a structured, numbers-only target element

## Context

The verdict document is the frozen contract (ADR-0001): the delivery surface and
the meaning of existing fields never change, but the document may grow additively
as a milestone's science arrives, and a field may be reserved before its shape is
known. `targets` has shipped since M1 as a present-but-empty `list[str]` — reserved
with no element shape on purpose. Milestone M5 is the milestone that defines it.
Once the element shape ships it is frozen, so choosing its fields — and whether to
carry per-target prose — is a durable decision with M6 (the LLM explainer)
downstream.

## Decision

Fill `targets` with structured target objects, each carrying `id`, `name`
(nullable), `type`, `score` (0–100, unbanded), `window` (`start`, `end`),
`max_altitude`, `transit_time`, and `moon_separation`. This is additive fill of a
reserved-but-shapeless stub, not a change to the meaning of any field: M5 fills
`targets` only, and every other document field stays byte-identical. Each field is
a value M5 actually computes, and the structure is the explanation — targets carry
no per-target prose `reasons`.

## Consequences

- Easier: consumers get machine-readable ranking detail (a dashboard card, the M6
  LLM) without parsing prose; the numbers are the explanation.
- Easier: the additive-only claim is testable — in every golden fixture, only the
  `targets` array changes, and a test asserts the other fields are byte-identical.
- Easier: M6 has structured inputs to turn into prose, keeping the "LLM explains,
  never computes" boundary (ADR-0001) clean.
- Constraint accepted: the element shape is now frozen; new per-target facts arrive
  as additive fields, and no field is reserved before the milestone that defines it
  (so no `fov_fit` field exists until equipment work lands).
- Constraint accepted: the list is bounded (top 10) and stably ordered (score
  descending, `id` tie-break) so the contract and any entity built on it have a
  stable, deterministic size and order.
- Constraint accepted: `list[str]` consumers (there were none in practice — the
  list only ever shipped empty) would need to read objects; the empty-list shape
  still appears when nothing is rankable.

## Alternatives Considered

### Alternative 1: Keep `list[str]` — target names only

- **Pros**: no shape change; smallest possible document growth.
- **Cons**: a bare name cannot express ranking, timing, or the moon relationship,
  so every consumer would need a side channel to explain why a target is listed.
- **Why not**: the milestone's value is the ranking detail; hiding it defeats the
  purpose and would force a real reshape later, which the frozen contract resists.

### Alternative 2: Carry a per-target `reasons` string list, mirroring the verdict

- **Pros**: symmetry with the verdict's explainability; human-readable per target.
- **Cons**: string assembly per target bloats the contract and complicates
  determinism, and it pre-empts M6, whose whole job is turning numbers into prose.
- **Why not**: the structured fields already carry the "why" as data; prose is M6's
  responsibility, and keeping it out here preserves the compute/explain boundary.

### Alternative 3: Let target ranking also adjust the verdict score or reasons

- **Pros**: "best target peaks at 78 degrees" could enrich the top-level verdict.
- **Cons**: it couples the additive ranking layer to the frozen go/no-go math, so
  M5 would change fields beyond `targets` and every golden's verdict could shift.
- **Why not**: keeping M5 to `targets` only gives a clean determinism and review
  story and honors the additive-growth rule; verdict-level use of targets can be a
  later, deliberate decision.
