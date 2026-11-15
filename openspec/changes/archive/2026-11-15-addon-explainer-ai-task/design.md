## Context

- The explainer edge is `pierpressure/explain/`. `build_explainer` returns
  `no_op_explainer` when the explainer is off, or a `NarrativeExplainer` around
  `PydanticAIProvider`. `NarrativeExplainer` owns the cache, the per-call bound
  (`DEFAULT_TIMEOUT`, 6 s) on one worker thread, and the failure log line,
  which `_failure_kind` limits to the error's class and an integer
  `status_code` attribute (#92).
- `ExplainerConfig` in `pierpressure/core/config.py` holds `enabled`, `model`
  and `api_key`, with `extra="forbid"` and `hide_input_in_errors=True`. The core
  is the only place that checks a setting's value (ADR-0022).
- Inside the add-on, `translate_form` passes the form's `explainer` block
  through without its unset fields. `_check_explainer` reports any
  `ExplainerConfig` field set in both places, and `_merge_explainer` joins the
  rest. Both already work key by key for any field the model defines.
- `pierpressure/supervisor.py` already talks to the Supervisor with `httpx`,
  `trust_env=False` and a 5 s timeout. `load_app_config` reads
  `SUPERVISOR_TOKEN` to tell an add-on from any other install.
- Upstream facts (brainstorm D2, D3): the request is `POST
  http://supervisor/core/api/services/ai_task/generate_data?return_response`;
  the reply is `{"changed_states": [...], "service_response":
  {"conversation_id": ..., "data": ...}}`; Core keeps running a call after the
  caller goes away; the Supervisor proxy gives up after 300 s with a 502.

## Goals / Non-Goals

**Goals:**

- One new provider class behind the existing `Provider` protocol, so the cache,
  the bound and the failure log apply unchanged.
- One new config field, checked by the core.
- No new combine rule in the add-on layer.

**Non-Goals:**

- A configurable timeout, or moving the call off the publish thread.
- Structured output, attachments or a `conversation_id` follow-up.
- The AI Task path outside the add-on, such as a long-lived access token.

## Test Seams

- **Primary test seam:** the new provider driven through `NarrativeExplainer`
  with an injected `httpx.Client(transport=httpx.MockTransport(...))`. It
  observes the request, the narrative or `None`, and the log records
  (`caplog`). This covers the request, reply, failure, bound and log
  requirements.
- **Existing seams reused:** `tests/test_explainer_config.py` (the new field),
  `tests/test_explainer.py` (`build_explainer`), `tests/test_main.py`
  (`build_delivery_and_explainer`, startup log lines, the add-on path with
  `SUPERVISOR_TOKEN` and `/data/options.json`), `tests/test_addon_settings.py`
  (the combine), `tests/test_ha_addon.py` (schema, options, permission,
  translations), `tests/test_explainer_docs.py` and the DOCS tests in
  `tests/test_ha_addon.py`.

## Scrutiny Tier & Blast Radius

- **Tier:** high. The change crosses a trust boundary: the add-on gains
  administrator access to Home Assistant's Core API, and the Supervisor token
  goes into a new request.
- **Blast radius:** `pierpressure/explain/`, one field in
  `pierpressure/core/config.py`, the wiring in `pierpressure/__main__.py`, and
  `ha-addon/`. The verdict document, the delivery surface and the conditions
  edge do not change.

## Decisions

### DD1 — A new `AiTaskProvider` in `pierpressure/explain/ai_task.py`

A dataclass with `entity_id`, `token` (`repr=False`), `timeout =
PROVIDER_TIMEOUT` and an optional injected `client`. `generate` builds the body,
posts it, and returns the reply's text. Without an injected client it creates
one `httpx.Client(timeout=timeout, trust_env=False)` on first use and keeps it.
The explainer runs one worker, so the client is never shared across threads at
once.

A module of its own, because it shares nothing with Pydantic AI except
`SYSTEM_PROMPT` and `PROVIDER_TIMEOUT`, which it imports. Rejected: a generic
"Home Assistant client" module shared with `supervisor.py`. The two requests
differ in path, method, retries and errors, and sharing would couple the broker
wait to the narrative.

### DD2 — The request body

`{"task_name": "PierPressure narrative", "instructions": SYSTEM_PROMPT + "\n\n" +
prompt.text, "entity_id": <entity>}`. The action has no separate system prompt,
so the framing goes first in `instructions`. The prompt's words do not change
(packet scope `out`). The action has no output-length setting; the framing
already asks for two to four sentences.

### DD3 — Failures raise `AiTaskError` with a `status_code`

A non-200 status raises `AiTaskError(status_code=<int>)`. A 200 reply that is
not JSON, or whose `service_response.data` is not non-empty text, raises
`AiTaskError(status_code=None)`. `httpx` transport and timeout errors pass
through as they are. `_failure_kind` then logs `AiTaskError (HTTP 400)`,
`AiTaskError` or `ConnectError`, and nothing else. `AiTaskError` carries no
text from the reply, so even a future log of `str(exc)` holds nothing secret.

Rejected: `httpx.Response.raise_for_status()`. Its `HTTPStatusError` keeps the
status on `.response`, not `.status_code`, so `_failure_kind` would drop it;
and its message quotes the URL.

### DD4 — `ExplainerConfig.ai_task_entity: str | None = None`

A `field_validator` accepts `^ai_task\.[a-z0-9_]+$` and otherwise raises a fixed
message, "must be an AI Task entity ID, such as ai_task.openai", that quotes no
input. The add-on schema declares it as plain `str?`, not a `match(...)`, so the
one rule lives in the core (ADR-0022).

### DD5 — `build_explainer(config, *, supervisor_token=None)` picks the provider

| `enabled` | `ai_task_entity` | token | Result |
|---|---|---|---|
| false or absent | any | any | `no_op_explainer`, no entity |
| true | unset | any | Pydantic AI provider, as today |
| true | set | set | `NarrativeExplainer(AiTaskProvider(...))`; info log names the entity, and says `explainer.api_key` is not used when one is set |
| true | set | unset | `no_op_explainer`; one warning names `explainer.ai_task_entity` and says it works only in the Home Assistant add-on |

`build_delivery_and_explainer` keeps managing the narrative entity whenever
`enabled` is true, so the last row's entity reads unavailable, as the specs
ask. `main` passes `os.environ.get("SUPERVISOR_TOKEN")`. The token never goes
into `AppConfig`, so printing the settings can never show it.

Rejected: a configuration error for the last row. It would stop every verdict
over an optional narrative.

### DD6 — Add-on files

- `ha-addon/config.yaml`: `homeassistant_api: true`, and the schema's
  `explainer` block becomes `enabled: bool?`, `ai_task_entity: str?`,
  `api_key: password?`, in that order. `options.explainer` stays `{}`.
- `ha-addon/translations/en.yaml`: labels **Enabled** and **AI Task entity**,
  each description starting `Optional.`. The section description names
  `explainer.enabled`, AI Task, `explainer.model` and `config.yaml`.
- `addon_options.py`: `translate_form` drops the form's `explainer.enabled`
  when it is false, so a switch turned on and then off counts as not set. The
  form's switch can only turn the explainer on; `config.yaml` can still turn
  it off.
- No change to `addon_settings.py`. Its key-by-key code reads
  `ExplainerConfig.model_fields`, so the new field joins it. Tests pin that.

### DD7 — Same bound and cache

The client timeout is `PROVIDER_TIMEOUT` (5 s) and the wrapper's bound stays
`DEFAULT_TIMEOUT` (6 s), as the packet asks. A failed call caches nothing, so
the next recompute tries again. A reply that arrives after the bound is
dropped.

### DD8 — A decision record

The ADR step records why calling Home Assistant for the narrative does not make
Home Assistant load-bearing, and the administrator access it grants (brainstorm
D14).

## Risks / Trade-offs

- [A slow model, such as a local Ollama, takes longer than 5 s and never gives a
  narrative] → Same bound as today, by the packet's scope. `docs/llm-explainer.md`
  says so; a configurable timeout is an open question.
- [Core keeps running a call PierPressure gave up on, so the user's LLM still
  bills for it] → The cache means that happens at most once per changed verdict
  per pier. The docs say so.
- [`homeassistant_api` makes the add-on an administrator of Home Assistant] →
  PierPressure calls only this one action. The ADR records the grant, and the
  docs tell the user.
- [The form's switch cannot turn off an explainer that `config.yaml` turns on]
  → A switch set to off counts as not set (DD6), so it never conflicts.
  DOCS.md says to set `explainer.enabled` in one place only.
- [An AI Task integration returns non-text `data` when no `structure` is sent]
  → Treated as a failed call: no narrative. Anthropic, OpenAI, Google and
  Ollama return text (brainstorm D2 research).

## Migration & Rollback

N/A. The new setting and form fields start unset, so an existing install keeps
its behavior. Rolling back the add-on to an earlier release drops the two form
fields; the Supervisor logs a warning for each saved value the schema no longer
declares and leaves it out (Supervisor `main` 98a2322,
`supervisor/apps/options.py` L274-283).

## Open Questions

- Should the explainer's per-call timeout become a setting, for slow local
  models? This waits for user reports; it does not change this plan.
