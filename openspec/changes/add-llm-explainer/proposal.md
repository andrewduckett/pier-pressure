## Why

The verdict document already explains itself: `reasons[]` is an itemized list of
gate and score terms, and `targets[]` carries the structured "why" for each ranked
object. That is precise but terse — a reader still has to assemble the story
themselves. M7 adds an optional prose layer that reads the finished verdict and
says it in sentences, so the answer to "is tonight worth it, and what should I
point at?" arrives as a short paragraph a person can read at a glance. This is the
last milestone in the roadmap's planned arc, and it is purely additive: nothing
downstream depends on it.

## What Changes

- Add an **optional LLM explainer**: a downstream edge stage that consumes the
  already-computed verdict document and produces a short prose narrative of the
  verdict, its reasons, and its top-ranked targets.
- Deliver the narrative as a **new read-only Home Assistant sensor entity**, published beside
  the existing verdict entities. The narrative is **not** added as a field of the
  verdict document — the numbers document is never touched by the LLM.
- Add an **explainer provider interface** with a default **model-agnostic**
  provider built on Pydantic AI, mirroring the conditions-provider edge seam. The
  configured `model` string (`provider:model-name`, e.g. `anthropic:claude-opus-5`,
  `openai:gpt-4o`) selects the LLM provider, so no provider is hard-coded. The
  provider is **disabled by default** and enabled through configuration.
- Degrade gracefully, distinguishing disabled from failed. When the explainer is
  disabled or unconfigured (the default), no narrative entity is published at all,
  so a default deployment is unchanged. When the explainer is enabled but a call
  fails, the service still publishes the verdict and actively publishes the
  narrative entity as unavailable — never a silent skip, since its retained state
  would otherwise keep showing an earlier narrative as current. The explainer never
  raises into the loop.
- Cache the narrative in memory, keyed on the full prompt input (the verdict,
  score, confidence, reasons, and every emitted target field — everything the prose
  depends on), so repeated recomputes with identical inputs reuse identical prose
  and avoid repeat LLM calls.
- Clean up stale references that call this "the M6 LLM layer" (M6 shipped as
  equipment ranking); the LLM explainer is M7. Touches comments and a decision
  record only — no behavior.

Non-goals (explicitly deferred):

- **Suggestions.** The roadmap title reads "LLM explainer + suggestions"; M7
  delivers the explainer only. Action-oriented suggestions ("start with M31, it
  transits at 01:20") are deferred to keep the LLM from looking load-bearing.
- **Per-target prose.** No structured per-target narrative field is added; ADR-0009
  keeps the per-target "why" as structured data. The verdict-level narrative may
  mention top targets, which it receives as context.

## Capabilities

### New Capabilities

- `verdict-narrative`: the optional LLM-generated prose layer — what it consumes
  from the finished verdict, the guarantee that it never alters the numbers, its
  disabled-by-default and graceful-degradation behavior, and its determinism-safe
  caching.

### Modified Capabilities

- `ha-delivery`: add the narrative sensor entity to the delivery surface (a new
  entity in the entity mapping). Additive only; no existing topic, entity, or
  field changes meaning.

## Impact

- **New code:** an explainer edge package (e.g. `pierpressure/explain/`) holding
  the provider interface, the default Pydantic AI provider, the input-building and
  caching logic, and the graceful-fallback wrapper. It is wired by
  `pierpressure/service.py` and is never imported by `pierpressure/core/`. The
  core-purity boundary test (`tests/test_core_boundary.py`) is extended so its
  `_FORBIDDEN` list also rejects importing the explainer package and the LLM SDK
  (`pydantic_ai`, `anthropic`) from `core/`, making the new boundary mechanically
  enforced rather than merely currently true.
- **Delivery:** `pierpressure/delivery/` gains one read-only sensor entity in its MQTT
  discovery output; the verdict document serialization is unchanged.
- **Config:** `pierpressure/core/config.py` gains optional explainer settings
  (enable flag, provider/model, API key reference). Disabled by default.
- **Dependencies:** a new runtime dependency on Pydantic AI — a model-agnostic LLM
  client (`pydantic-ai-slim` with the Anthropic, OpenAI, and Google provider extras,
  added with `uv add`) — used only inside the explainer edge.
- **Determinism:** the verdict document remains byte-identical for identical
  inputs — the LLM output lives entirely outside it.
- **Docs:** `docs/roadmap.md` M7 status flips to done in the landing PR; stale
  "M6 LLM layer" references corrected.
