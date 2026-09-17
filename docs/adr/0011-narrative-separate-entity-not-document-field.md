---
id: adrs-adr0011
date: 2026-09-16
status: accepted
title: 'ADR0011: The LLM narrative is delivered as a separate entity, not a verdict-document field'
description: Architecture Decision Record for delivering the optional LLM-generated prose narrative as an additive Home Assistant entity beside the verdict document, rather than as a field inside the frozen, deterministic verdict document, so the numbers document stays byte-identical and the LLM can never alter a decision.
---

# ADR-0011: The LLM narrative is delivered as a separate entity, not a verdict-document field

## Context

The verdict document is the frozen contract (ADR-0001): its delivery surface and
the meaning of existing fields never change, though it may grow additively. Two
invariants bind the LLM layer specifically — it is optional and never feeds the
math, and the core emits one document that is byte-identical for the same inputs.
Milestone M7 adds an optional prose narrative that explains an already-computed
verdict. An LLM is non-deterministic and online, so where the prose lands is a
durable, hard-to-reverse decision: once the delivery surface ships it is frozen,
and the choice governs whether the byte-identity guarantee needs a caveat.

The frozen-contract rule forbids changing the meaning of *existing* topics,
entities, and fields; it explicitly permits the contract to grow additively. M5
already exercised this on the delivery side by adding a top-target sensor as a new
entity that left "every existing entity, topic, and mapping unchanged" (spec
ha-delivery). Adding a narrative entity is the same sanctioned additive growth, so
this decision does not change or supersede that frozen contract (ADR-0001).

## Decision

Deliver the narrative as a separate, additive Home Assistant entity (a narrative
sensor whose attributes carry the full prose). The verdict document gains no
narrative field; the LLM output is never merged into the document nor read back
into any decision. The narrative is produced by an edge stage after the pure core
runs and is absent (the entity resolves to unavailable) whenever the explainer is
disabled, unconfigured, or fails.

## Consequences

- Easier: the verdict document stays byte-identical for the same inputs with no
  caveat, and the core-purity and determinism tests are unchanged — the numbers
  document is produced entirely by the pure, offline core.
- Easier: "the LLM never changes the numbers" becomes structural, not a promise —
  the prose is a different entity the decision path never reads.
- Easier: graceful degradation is trivial — no narrative means one unavailable
  entity, and every other entity and the whole verdict path are untouched.
- Constraint accepted: the narrative entity is now part of the frozen delivery
  surface; it is additive and stays additive, and a consumer wanting both the
  numbers and the prose reads two entities.
- Constraint accepted: the prose is a presentation concern, not part of the
  single-document contract, so downstream tools that consume only the document do
  not see it.

## Alternatives Considered

### Alternative 1: An additive `narrative` field on the verdict document, filled by the edge

- **Pros**: keeps everything in one document; matches the established pattern of a
  reserved field filled as a milestone's science arrives.
- **Cons**: every other field is filled *inside* the deterministic core; a field
  filled by a non-deterministic edge splits the document into a core version and a
  delivered version and forces a caveat onto the byte-identity guarantee.
- **Why not**: it muddies the "core emits one deterministic document" invariant for
  a value that is language, not a number; separation keeps that invariant clean.

### Alternative 2: A `narrative` field made "deterministic" by caching on the reasons

- **Pros**: single-document contract plus stable prose for identical skies.
- **Cons**: a cold cache or first generation is still non-deterministic, so the
  document's byte-identity would appear to depend on cache state — making a
  performance optimization load-bearing for the contract.
- **Why not**: the cache must remain a non-load-bearing optimization (as the
  ranking cache is); the contract cannot depend on it.

### Alternative 3: Rewrite or augment `reasons[]` with the prose

- **Pros**: reuses the existing field and entity; no new delivery surface.
- **Cons**: **BREAKING** — `reasons[]` are itemized gate/score terms that
  downstream consumers may read term by term; replacing them with prose changes the
  meaning of an existing field.
- **Why not**: forbidden by the frozen-contract rule (ADR-0001); the meaning of an
  existing field never changes.
