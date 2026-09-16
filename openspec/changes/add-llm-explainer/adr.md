# ADR Review Manifest

- Status: completed
- Review date: 2026-09-16

## Review Summary

ADR review completed for the add-llm-explainer change. The design was checked
against every in-force repository ADR for conflicts and supersession, and one new
durable decision — where the LLM narrative is delivered — was recorded.

Note on ADR numbering: this working tree is on `main`, whose highest ADR is 0009.
Milestone M6 (equipment ranking) introduces ADR-0010 on its own not-yet-merged
branch, so this change takes ADR-0011 to avoid a collision when the branches merge.

## In-Force ADRs Reviewed

- ADR-0001 — core is Home-Assistant-agnostic and emits one JSON verdict document
  (the frozen contract this decision builds on).
- ADR-0002 — gates then a banded score.
- ADR-0003 — astronomical-night hard clamp.
- ADR-0004 — deterministic offline astronomy.
- ADR-0005 — conditions provider edge seam (the pattern the explainer edge mirrors).
- ADR-0006 — conditions as per-source groups.
- ADR-0007 — canonical horizon representation.
- ADR-0008 — vendored OpenNGC catalog.
- ADR-0009 — targets filled additively as structured, numbers-only objects, with
  per-target prose deferred to the LLM milestone (this change).

No in-force ADR is superseded by this change. ADR-0011 adds a new delivery entity,
which is additive growth of the delivery surface — the frozen-contract rule
(ADR-0001, CLAUDE.md) forbids changing existing topics, entities, and field
meanings but permits additive growth, as M5 already did by adding its top-target
sensor. Adding an entity therefore does not change or supersede ADR-0001.

## New Durable ADRs Created

- ADR-0011 — The LLM narrative is delivered as a separate entity, not a
  verdict-document field (`docs/adr/0011-narrative-separate-entity-not-document-field.md`).
