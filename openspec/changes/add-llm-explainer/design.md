## Context

See proposal.md — Why. The verdict document is real and frozen: `reasons[]` is a
list of itemized gate/score terms and `targets[]` carries each ranked object's
structured "why". The service already owns freshness — `Service._publish` fetches
conditions, calls `produce_verdict(pier, clock, conditions)`, and hands the
document to `MqttDelivery.publish_verdict`.

Constraints that shape the approach:

- **Pure, deterministic core.** `test_core_boundary.py` forbids `core/` from
  importing delivery, `httpx`, or the conditions provider package. The explainer
  is network-facing and non-deterministic, so it must live at the edge, exactly
  like the conditions provider — never inside `core/`.
- **The verdict document is the numbers contract.** Its delivery surface and the
  meaning of existing fields are frozen; it may grow additively. The LLM output
  is language, not a number, and the "LLM never feeds the math / never
  load-bearing" invariant means it must not be able to alter any decision.
- **Existing edge pattern to follow.** `ConditionsProvider = Callable[[PierConfig],
  Conditions]` is injected into `Service`, never raises, and degrades to an empty
  value on failure. The ranking cache keys on `(pier, night)` and is a performance
  optimization only. The explainer reuses both shapes.

## Goals / Non-Goals

**Goals:**

- Add an optional edge stage that turns a finished verdict into short prose.
- Deliver the prose as one additive read-only Home Assistant sensor entity.
- Keep the verdict document byte-identical whether or not the explainer runs.
- Fail safe: a disabled, unconfigured, or failing explainer never blocks a verdict.

**Non-Goals:**

- **Prose in the verdict document.** The narrative is delivered beside the
  document, never merged into it (the durable call, recorded in adr.md).
- **Suggestions and per-target prose.** Out of scope per proposal.md.
- **Moving the LLM call off the publish path.** M7 calls synchronously with a
  timeout; asynchronous generation is a later concern (see Open Questions).

## Decisions

### D1 — The explainer is an injected edge callable, never in the core

Add a new package `pierpressure/explain/` and inject an
`Explainer = Callable[[VerdictDocument], str | None]` into `Service`, mirroring
`ConditionsProvider`. `Service._publish` produces the document, calls the
explainer for an optional narrative, then passes both to delivery:

```
conditions = self._conditions_provider(pier)
document = produce_verdict(pier, self._clock, conditions)
narrative = self._explainer(document)          # never raises; may be None
self._delivery.publish_verdict(document, narrative=narrative)
```

The default explainer is a no-op that returns `None` (explainer disabled), so the
existing behavior is the default. `core/` imports nothing from `explain/`. The
boundary test is not merely left passing: `test_core_boundary.py`'s `_FORBIDDEN`
list is extended with `pierpressure.explain` and `anthropic`, so the mechanical
guard actively fails if the core ever imports the network-facing explainer or the
SDK rather than only happening to pass today.

- **Why a callable, not a method on the core:** the core is pure and offline; the
  explainer does I/O and is optional. It belongs where conditions I/O already
  lives — at the service edge.
- **Why not a second delivery pass from a background worker:** the service's main
  thread owns all publishing (no concurrent writes). Producing the narrative
  inline on that thread keeps that invariant; the timeout and cache (D4, D5) bound
  the cost.

### D2 — The narrative is delivered as a separate entity, not a document field

The verdict document gains no narrative field. Delivery treats the narrative entity
as **managed only when the explainer is enabled**, which it learns once at
construction from config (D7) — separately from the per-publish `narrative` value.
This split is what keeps three states distinct:

- **Explainer disabled (the default):** delivery does not manage the narrative
  entity — it publishes no narrative discovery or state, so a default deployment
  gains no entity and sees no unexpected messages. The service is stateless across
  restarts and so cannot know an entity was ever created; it therefore does not
  auto-remove one. An operator who enabled then disabled the feature clears the
  orphaned entity by clearing its retained discovery topic once — a documented step
  (see Migration Plan), not an automatic per-publish action.
- **Enabled, narrative present this recompute:** publish the entity with the full
  prose in its JSON attributes (entity state values are length-limited; the state
  carries a short marker).
- **Enabled, narrative absent this recompute** (provider failed or timed out):
  the adapter **actively publishes the entity's unavailable state — it does not
  skip the update.** Every entity's state and attributes are published retained
  (spec ha-delivery), so skipping would leave the broker serving the previous
  recompute's prose as if it explained tonight's verdict; an explicit unavailable
  payload prevents that. `publish_verdict(document, narrative=None)` reaches this
  branch only when the entity is managed, so it never fires for a disabled feature.

No other entity is affected in any of the three states.

This is the milestone's durable decision and is recorded in adr.md. Adding a new
entity is additive growth of the delivery surface — the same sanctioned move M5
made with its top-target sensor ("every existing entity, topic, and mapping is
unchanged", spec ha-delivery) — so it changes no existing entity and does not
supersede the frozen-contract ADR-0001. Keeping the LLM output out of the numbers
document makes byte-identity hold with no caveat and makes "the LLM never changes
the numbers" structural — the prose is a different entity the decision path never
reads back.

- **Alternative considered — an additive `narrative` field filled by the edge:**
  matches the "stubbed field filled by a milestone" pattern, but every other field
  is filled *inside* the deterministic core; a field filled by a non-deterministic
  edge would split the document into a core version and a delivered version and
  force a caveat onto the byte-identity guarantee. Rejected in favor of separation.

### D3 — A provider interface with a default LLM provider, off by default

The explainer obtains prose through a small provider interface (a callable or
protocol taking the built input and returning text). The default provider is built
on **Pydantic AI**, which is model-agnostic: the configured `model` string
(`provider:model-name`) selects the LLM provider, so nothing is hard-coded to one
vendor. That provider is the *only* component permitted a network call. A test
double — or an injected Pydantic AI `TestModel`/`FunctionModel` — replaces it with
no network. The provider is selected by configuration and is **disabled by
default**: with no `explainer` config, the service wires the no-op explainer.

- **Why an interface:** swappability and testability, and it keeps the network at
  a single named seam, consistent with the conditions provider edge.
- **Why Pydantic AI as the default:** it lets any configured provider (Anthropic,
  OpenAI, Google, …) write the prose from one code path, is pydantic-native (already
  a core dependency) and typed for the strict-mypy gate, and keeps the choice of
  vendor from being load-bearing. The default `model` is `anthropic:claude-opus-5`.
- **Credentials:** the optional `api_key` is exported to the selected provider's
  standard key variable (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`);
  omitting it lets the provider read that variable directly. A missing key raises
  inside Pydantic AI, which the graceful wrapper (D5) turns into no narrative.

### D4 — Cache the narrative on the deterministic verdict terms

Key an in-memory cache on a stable hash of **the exact input handed to the
provider** (D6) — the verdict, score, confidence, the `reasons` list, and the
emitted fields of the targets included in the prompt. The key must cover
everything that influences the prose: keying on target `id`s alone would serve a
stale narrative on a later night whose targets share those ids but have new
`transit_time`, `max_altitude`, or `moon_separation`, or whose `confidence` band
has shifted. Identical input reuses the cached prose without a new provider call;
any changed input misses and regenerates. This mirrors the ranking's per-night
cache: a performance and cost bound that also gives identical inputs identical
prose. Correctness never depends on it — a cold cache with the explainer disabled
is just "no narrative".

- **Why the whole prompt input, not a hand-picked subset:** the safe key is a hash
  of the same bytes the provider sees, so no prompt-influencing field can drift out
  of the key. Only `generated_at` is excluded (it is not part of the prompt), which
  is what lets successive recomputes of an unchanged verdict reuse one narrative.

### D5 — Graceful degradation and bounded latency

The explainer wrapper catches every provider error, logs it, and returns `None`;
`Service._publish` publishes the verdict regardless. The provider call carries a
short timeout so a slow or hung LLM cannot stall the publish thread — on timeout
the wrapper returns `None` and the verdict still goes out on time. In steady state
the cache (D4) makes most publishes a local hit, so the timeout matters only on a
cache miss.

- [Blocking the publish thread] → short per-call timeout + cache; on timeout,
  return `None` and deliver the verdict.
- [Per-pier timeouts stack on the interval recompute] → `publish_all` runs piers
  sequentially on the one publish thread, so on a cache-cold interval each pier's
  timeout adds to the next, delaying later piers. Today the deployment runs a
  single pier and the cache makes steady state a local hit, so this is bounded now;
  if multi-pier latency becomes real, the fix is the asynchronous path in Open
  Questions, not a larger timeout.
- [The explainer raising into the loop] → the wrapper never propagates; a failure
  is a logged miss, exactly like the conditions provider's failure path.

### D6 — Prompt input is the verdict terms only; output is opaque text

The provider input is built from the document's terms only — the verdict, score,
confidence, the `reasons[]` strings, and the top targets — with a system
instruction to explain those terms in plain sentences and introduce no numbers or
claims beyond them. The returned text is treated as opaque: it is delivered as-is
and never parsed back into any field. Whether the prose reads as a faithful
summary is a documented manual acceptance check (spec verdict-narrative), because
generated language is not asserted mechanically.

### D7 — Configuration

Add an optional `explainer` block to `AppConfig`: an `enabled` flag (default
`false`), the provider/model identifier, and an API key that supports the existing
`${ENV}` expansion so the secret need not sit in plaintext (like the broker
credentials). The same `enabled` flag drives both edges: on `enabled: false` (or an
absent block) the service wires the no-op explainer *and* tells delivery not to
manage the narrative entity (D2), so no provider is constructed and no narrative
entity appears; on `enabled: true` it wires the real provider and delivery manages
the entity. The key is never logged.

## Risks / Trade-offs

- [New runtime dependency — Pydantic AI] → isolated to `pierpressure/explain/`;
  `core/` still imports nothing network-facing, so the boundary test is unaffected.
  Added with `uv add` so `pyproject.toml`/`uv.lock` stay in step.
- [LLM cost and rate limits] → disabled by default, and the deterministic-terms
  cache collapses repeated identical skies to one call.
- [Secret leakage] → API key via `${ENV}`, never logged; the explainer degrades to
  no-narrative when the key is missing rather than erroring.
- [Every golden delivery fixture gains an entity] → the narrative entity is
  additive and appears only when the explainer is enabled; with the default
  (disabled) config the delivery output is unchanged, and a test asserts the verdict
  document and existing entities are unchanged, guarding the additive-only claim.

## Migration Plan

Additive and behind the `explainer.enabled` flag (default off). On deploy with the
flag unset, nothing changes — no new entity, no verdict-document change. With the
flag on and a provider configured, Home Assistant gains one auto-discovered
narrative sensor. Rollback is reverting the change or clearing the flag: delivery
stops managing the entity, so it is no longer published or updated. To remove a
sensor that was created while the feature was enabled, clear its retained discovery
topic once (the standard Home Assistant discovery removal) — a documented operator
step, not an automatic per-publish action, because the stateless service cannot
detect a prior-enabled entity. No data migration.

## Open Questions

- Should the narrative eventually be generated off the publish thread (async or a
  worker) so a cache miss never adds any latency to delivery? Deferrable: it does
  not change the specs, the entity, or the task breakdown — only the internal
  timing of when the narrative appears. M7 ships the synchronous-with-timeout path.
