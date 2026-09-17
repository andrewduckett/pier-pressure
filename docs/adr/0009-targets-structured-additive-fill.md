---
id: adrs-adr0009
date: 2026-09-11
status: accepted
title: 'ADR0009: The targets field is filled additively with a structured, numbers-only target element'
description: Architecture Decision Record for filling the verdict document's reserved targets list with structured objects of computed numbers rather than prose, without changing any other field, and leaving per-target prose to the optional explainer.
---

# ADR-0009: The targets field is filled additively with a structured, numbers-only target element

## Context

PierPressure publishes one verdict document each night, and an earlier decision
froze it as a contract (ADR-0001): existing fields never change meaning, and the
document may only grow by adding new fields. A field can be reserved early —
present but empty — before its shape is settled. The list of suggested targets is
one such field. It has shipped from the start as an empty list of names, reserved
on purpose with no defined element shape. This decision is where that shape is
filled. Once the shape ships it is frozen, so choosing what each target carries —
and whether it carries prose — is a durable, hard-to-reverse decision. A later,
optional explainer that turns the verdict into plain prose is the main downstream
consumer.

## Decision

Fill the targets list with structured objects, each a set of computed numbers: an
identity and type for the object, its ranking score, the window when it is
observable, and its geometry against the sky and the moon. This is additive fill
of a reserved, shapeless stub, not a change to any existing field's meaning. This
step fills the targets list only, and every other field of the document stays
byte-identical. Every value is a number the ranking already computes. The
structure itself is the explanation, so a target carries no prose of its own.

## Consequences

- **Easier:** consumers get machine-readable ranking detail without parsing prose.
  A dashboard card, or the optional explainer, reads the numbers directly.
- **Easier:** the additive-only claim is testable. In every recorded fixture, only
  the targets list changes, and a test asserts every other field stays
  byte-identical.
- **Easier:** the optional explainer has structured inputs to turn into prose,
  which keeps the rule that the language layer explains but never computes
  (ADR-0001) clean.
- **Constraint accepted:** the element shape is now frozen. New per-target facts
  arrive as added fields, and no field is reserved before the work that defines it
  — so no field for equipment fit exists until the equipment work lands.
- **Constraint accepted:** the list is bounded to the top ten and stably ordered —
  by score, with a fixed tie-break — so the contract and anything built on it have
  a stable, deterministic size and order.
- **Constraint accepted:** any consumer of the old names-only list would need to
  read objects instead. In practice there were none — the list only ever shipped
  empty — and the empty-list shape still appears when nothing is rankable.

## Alternatives Considered

### Alternative 1: Keep a names-only list

- **Pros**: no shape change, and the smallest possible document growth.
- **Cons**: a bare name cannot express ranking, timing, or the moon relationship,
  so every consumer would need a side channel to explain why a target is listed.
- **Why not**: the value here is the ranking detail. Hiding it defeats the purpose
  and would force a real reshape later, which the frozen contract resists.

### Alternative 2: Carry a per-target list of prose reasons, mirroring the verdict

- **Pros**: symmetry with the verdict's own explainability, and human-readable per
  target.
- **Cons**: assembling a string per target bloats the contract and complicates
  determinism, and it pre-empts the optional explainer, whose whole job is turning
  numbers into prose.
- **Why not**: the structured numbers already carry the "why" as data. Prose is the
  explainer's responsibility, and keeping it out here preserves the
  compute-versus-explain boundary.

### Alternative 3: Let target ranking also adjust the top-level verdict score or reasons

- **Pros**: a note like "best target peaks at 78 degrees" could enrich the
  top-level verdict.
- **Cons**: it couples the additive ranking layer to the frozen go/no-go math, so
  this step would change fields beyond the targets list, and every recorded verdict
  could shift.
- **Why not**: keeping this step to the targets list alone gives a clean
  determinism and review story and honours the additive-growth rule. Using targets
  at the verdict level can be a later, deliberate decision.
