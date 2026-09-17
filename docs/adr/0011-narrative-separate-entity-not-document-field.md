---
id: adrs-adr0011
date: 2026-09-16
status: accepted
title: 'ADR0011: The LLM narrative is delivered as a separate entity, not a verdict-document field'
description: Architecture Decision Record for delivering the optional LLM-generated prose narrative as an additive Home Assistant entity beside the verdict document, rather than as a field inside the frozen, deterministic verdict document, so the numbers document stays byte-identical and the LLM can never alter a decision.
---

# ADR-0011: The LLM narrative is delivered as a separate entity, not a verdict-document field

## Context

PierPressure publishes one verdict document each night, and an earlier decision
froze it as a contract (ADR-0001): the delivery surface and the meaning of
existing fields never change, though new ones may be added. Two rules bind the
language layer in particular. It is optional and never feeds the math, and the
core emits one document that is byte-identical for the same inputs. We now add an
optional prose narrative that explains an already-computed verdict, written by a
large language model (LLM). An LLM is non-deterministic and needs the network, so
where its prose lands is a durable, hard-to-reverse choice. Once the delivery
surface ships it is frozen, and this choice decides whether the byte-identity
guarantee needs a caveat.

Delivery to Home Assistant is a set of entities — the sensors a user sees. The
contract already allows new entities to be added, as long as existing ones keep
their meaning. So adding a narrative entity is sanctioned additive growth, not a
change to the frozen contract.

## Decision

Deliver the narrative as a separate, additive Home Assistant entity — a narrative
sensor whose attributes carry the full prose. The verdict document gains no
narrative field. The LLM output is never merged into the document, and never read
back into any decision. A stage at the edge produces the narrative after the pure
core has run. When the explainer is turned off, unconfigured, or failing, the
entity simply reports unavailable.

## Consequences

- **Easier:** the verdict document stays byte-identical for the same inputs, with
  no caveat. The core-purity and determinism tests are unchanged, because the pure,
  offline core produces the numbers document alone.
- **Easier:** "the LLM never changes the numbers" becomes structural, not a
  promise. The prose is a separate entity that the decision path never reads.
- **Easier:** degrading gracefully is trivial. No narrative means one unavailable
  entity, and every other entity and the whole verdict path are untouched.
- **Constraint accepted:** the narrative entity is now part of the frozen delivery
  surface. It is additive and stays additive, and a consumer that wants both the
  numbers and the prose reads two entities.
- **Constraint accepted:** the prose is a presentation concern, not part of the
  one-document contract. Tools that consume only the document never see it.

## Alternatives Considered

### Alternative 1: An additive narrative field on the verdict document, filled at the edge

- **Pros**: it keeps everything in one document and matches the pattern of a
  reserved field filled as new science arrives.
- **Cons**: every other field is filled inside the deterministic core. A field
  filled by a non-deterministic edge splits the document into a core version and a
  delivered version, and forces a caveat onto the byte-identity guarantee.
- **Why not**: it muddies the "core emits one deterministic document" rule for a
  value that is language, not a number. Separation keeps that rule clean.

### Alternative 2: A narrative field made "deterministic" by caching on the reason terms

- **Pros**: one document, plus stable prose for identical skies.
- **Cons**: a cold cache, or a first generation, is still non-deterministic, so the
  document's byte-identity would appear to depend on cache state — which makes a
  performance optimization load-bearing for the contract.
- **Why not**: the cache must stay a non-load-bearing optimization, as the ranking
  cache is. The contract cannot depend on it.

### Alternative 3: Rewrite or augment the existing reason terms with the prose

- **Pros**: it reuses the existing field and entity, with no new delivery surface.
- **Cons**: **BREAKING** — the reason terms are itemized gate and score entries that
  downstream consumers may read one by one. Replacing them with prose changes the
  meaning of an existing field.
- **Why not**: the frozen-contract rule forbids it (ADR-0001). The meaning of an
  existing field never changes.
