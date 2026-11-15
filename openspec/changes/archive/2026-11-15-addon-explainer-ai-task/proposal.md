## Why

An add-on user who wants the narrative must today hand PierPressure an LLM API
key. Home Assistant's AI Task integration already holds that key for the
OpenAI, Google Gemini, Anthropic and Ollama integrations, and its
`ai_task.generate_data` action returns generated text (D2). If the add-on calls
that action, the key never reaches PierPressure.

## What Changes

- A new explainer provider, used only inside the add-on, that asks a named AI
  Task entity for the narrative through the Supervisor's Core API (D3, D11,
  D12).
- A new optional setting, `explainer.ai_task_entity`, that selects this
  provider. It must be an `ai_task` entity ID (D4, D5, D6). When it is set, the
  explainer does not use `model` or `api_key`, and the startup log says so
  (D9).
- Outside the add-on, a set entity gives no narrative and one startup warning;
  every verdict is still published (D10).
- The add-on's Configuration form gains two optional explainer fields:
  `enabled` and `ai_task_entity` (D7). They join `config.yaml` key by key, as
  `api_key` does (D8). A switch set to off counts as not set (D7).
- The add-on asks for `homeassistant_api: true` (D3).
- The new provider keeps the explainer's timeout, cache and failure handling,
  and logs a failure by its kind and HTTP status only (D13).
- A decision record says why calling Home Assistant for the optional narrative
  does not make Home Assistant load-bearing (D14).
- `ha-addon/DOCS.md` and `docs/llm-explainer.md` describe the AI Task path.

Nothing here is a breaking change: an install that does not set
`ai_task_entity` behaves as it does today.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `verdict-narrative`: the explainer can obtain prose from a Home Assistant AI
  Task entity, selected by `explainer.ai_task_entity`; how that request is
  made, what counts as a usable reply, how it fails, what it logs, and what
  happens outside the add-on.
- `ha-addon`: the form's `explainer` block declares `enabled` and
  `ai_task_entity` as well as `api_key`, with labels; the add-on config asks
  for `homeassistant_api`.

## Impact

- Code: `pierpressure/explain/ai_task.py` (a new provider),
  `pierpressure/explain/explainer.py` (`build_explainer`),
  `pierpressure/core/config.py` (`ExplainerConfig`), `pierpressure/__main__.py`
  (passing the Supervisor token and the startup log lines).
  `pierpressure/addon_options.py` drops a form switch set to off.
  `pierpressure/addon_settings.py` needs no new rule: its key-by-key check
  already covers every `ExplainerConfig` field.
- Add-on: `ha-addon/config.yaml` (schema and `homeassistant_api`),
  `ha-addon/translations/en.yaml`, `ha-addon/DOCS.md`.
- Docs: `docs/llm-explainer.md`, and a new record in `docs/decisions/`.
- Dependencies: none new. The provider uses `httpx`, which the Supervisor
  client already uses.
- Systems: the add-on gains administrator access to Home Assistant's Core API
  through the Supervisor's proxy. PierPressure uses it only for this one
  action.
