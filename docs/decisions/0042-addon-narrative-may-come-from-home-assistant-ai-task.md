---
id: adrs-adr0042
date: 2026-11-15
status: accepted
title: 'ADR0042: In the add-on, the narrative may come from Home Assistant''s AI Task without making Home Assistant load-bearing'
description: Architecture Decision Record. Inside the Home Assistant add-on, the optional explainer may ask a Home Assistant AI Task entity for its prose through the Supervisor. Only the narrative depends on that call, which is bounded and fails to no narrative, so Home Assistant stays outside the verdict's freshness and correctness.
---

# ADR-0042: In the add-on, the narrative may come from Home Assistant's AI Task without making Home Assistant load-bearing

## Context

PierPressure has a durable rule: Home Assistant is never load-bearing for the
verdict's freshness or correctness. The service owns its own schedule, and
Home Assistant only receives what it publishes. The optional explainer writes a
short prose narrative of a finished verdict, on its own entity beside the
verdict (ADR-0011). Until now it called an LLM service directly, with an API key
the user handed to PierPressure.

Home Assistant's AI Task integration already holds the user's LLM key for the
OpenAI, Google Gemini, Anthropic and Ollama integrations. Its
`ai_task.generate_data` action returns generated text. An add-on can call it
through the Supervisor's proxy to the Core API, but only after it asks for
`homeassistant_api`, which makes it an administrator of Home Assistant.

So the question is whether PierPressure may call Home Assistant at all, and on
what terms. A reader who sees the rule "never load-bearing" could remove this
call. A reader who sees the call could take it as leave to make other features
depend on Home Assistant.

## Decision

Inside the add-on, the explainer may get its prose from a named Home Assistant
AI Task entity, through the Supervisor's Core API. This holds only on these
terms:

- Only the narrative depends on the call. The verdict, its score, its
  confidence, its targets and its publish time never wait for or read anything
  from Home Assistant.
- The call has the same time bound as any explainer call. When Home Assistant
  is slow, down or wrong, there is no narrative for that recompute, its entity
  reads unavailable, and the verdict is published on time.
- PierPressure uses its Core API access for this one action and nothing else.

## Consequences

- Easier: an add-on user gets the narrative without giving PierPressure an LLM
  key. The key stays in Home Assistant, where they already manage it.
- Easier: any LLM that Home Assistant supports through AI Task works, including
  a local one, with no change to PierPressure.
- Harder: the add-on now holds administrator access to Home Assistant. That
  widens what a bug or a compromised image could do there. The docs say so,
  and the code calls only `ai_task.generate_data`.
- Harder: a narrative from Home Assistant can fail for reasons PierPressure
  cannot see, such as a missing entity or a removed integration. Only the
  error's kind and HTTP status are logged, so the user must check Home
  Assistant's own logs for the cause.
- Constraint kept: any future feature that calls Home Assistant must meet the
  same terms. It must be optional, bounded and fail without touching the
  verdict. A call that the verdict or its schedule would wait on breaks the
  rule this record keeps.

## Alternatives Considered

### Alternative 1: Keep the API key as the only path

- **Pros**: no new permission, and PierPressure needs nothing from Home
  Assistant.
- **Cons**: the user copies a secret into a second place and keeps it in step.
  A local model behind Home Assistant cannot be reached at all.
- **Why not**: the key already lives in Home Assistant, and the narrative is
  optional, so a bounded call to fetch it does not threaten the verdict.

### Alternative 2: Let Home Assistant write the narrative itself, in an automation

- **Pros**: PierPressure makes no call to Home Assistant, and needs no
  permission.
- **Cons**: every user must build an automation that watches the verdict, calls
  AI Task, and stores the text. The narrative's prompt, cache and failure rules
  would live in each user's YAML instead of being tested here.
- **Why not**: it moves a tested feature into untested, per-user configuration
  for no gain in safety. The bounded call gives the same isolation.

### Alternative 3: Call Home Assistant outside the add-on too, with a long-lived access token

- **Pros**: Docker and source installs could use AI Task as well.
- **Cons**: the user must create and store a token with full access, plus Home
  Assistant's URL, which is the same kind of secret this path avoids.
- **Why not**: it brings back the secret handling the add-on path removes.
  Outside the add-on, the API key path stays.
