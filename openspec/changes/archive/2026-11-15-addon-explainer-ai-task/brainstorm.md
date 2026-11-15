## Story

#88 addon-explainer-ai-task — the narrative uses Home Assistant's own AI integration.
<https://github.com/andrewduckett/pier-pressure/issues/88>

## Decisions

The user delegated this brainstorm: pick the recommended answer, record the
alternatives, and go on. So every row the code or a document did not settle is
an `Assumption`. The issue has no comments.

| # | Question | Answer | Source |
|---|---|---|---|
| D1 | What is in scope? | Inside the add-on only: a provider behind `Provider` that calls `ai_task.generate_data` through the Supervisor; `homeassistant_api: true`; two optional form fields; the same timeout, cache and failure handling; an ADR; `ha-addon/DOCS.md` and `docs/llm-explainer.md`. The prompt and Docker or source installs are out. | Evidence: #88 packet |
| D2 | What does Home Assistant offer, and where? | `ai_task.generate_data` takes `task_name` and `instructions` (required), and `entity_id` (optional). It only returns a response, `{conversation_id, data}`, where `data` is text when `structure` is left out. Since 2025.7. | Evidence: home-assistant/core `dev` fddf359f, `components/ai_task/services.py` L75-95, `task.py` L299-314; <https://www.home-assistant.io/actions/ai_task.generate_data/> |
| D3 | How does the add-on reach it? | `POST http://supervisor/core/api/services/ai_task/generate_data?return_response` with `Authorization: Bearer $SUPERVISOR_TOKEN`; the reply is `{"changed_states": [...], "service_response": {...}}`. Without `?return_response` Core answers 400. `homeassistant_api: true` grants the access, as an administrator. | Evidence: core `components/api/__init__.py` L409-476; <https://contributors.home-assistant.io/apps/guides/communication/>; <https://contributors.home-assistant.io/apps/reference/configuration/> |
| D4 | What picks the AI Task path over Pydantic AI? | A new setting, `explainer.ai_task_entity`. When set, the explainer calls that entity; `model` and `api_key` go unused. Rejected: an `explainer.provider` selector (two settings for one choice), and a `model` prefix such as `ai_task:` (overloads a Pydantic AI spec). | Assumption |
| D5 | Must the entity be named, given Home Assistant falls back to a preferred entity? | Yes. PierPressure always sends the named entity. Leaning on the preferred entity would need another switch to pick the path, and fails with "no preferred entity set" on a fresh install. | Evidence: core `ai_task/task.py` L118-135 (fallback and `no_entity` error); Assumption (the choice) |
| D6 | What shape is the setting? | Text that must be an `ai_task` entity ID, `ai_task.<object_id>`; the core checks it and its error names `explainer.ai_task_entity`. On the form it is an optional text field in the `explainer` block. | Evidence: ADR-0022 (the core alone validates); Assumption (the name) |
| D7 | Which explainer fields does the form gain? | Two, in the `explainer` block before `api_key`: `enabled` (`bool?`) and `ai_task_entity` (`str?`). Neither goes in `options`, so both start unset. A form `enabled` of false counts as not set, because the form cannot clear a switch once it is touched. | Evidence: Supervisor `main` 98a2322, `supervisor/apps/options.py` L31-45 (`bool?` is valid); <https://contributors.home-assistant.io/apps/guides/options/> |
| D8 | How do the form's explainer fields combine with `config.yaml`? | Key by key, as `api_key` already does: a key set in both stops the add-on, and the error names it, never its value. Not one grouped setting, as the packet said. | Evidence: archived `addon-explainer-key-option` D5; `_check_explainer` in `pierpressure/addon_settings.py` |
| D9 | What if the entity and an API key are both set? | The entity wins, and the key is not used. The startup log names the AI Task entity in use and says the API key is not used. No value of the key is logged. | Assumption |
| D10 | What if the entity is set outside the add-on (no `SUPERVISOR_TOKEN`)? | No narrative. The service logs one warning at startup that AI Task works only in the add-on, still publishes every verdict, and the narrative entity reads unavailable. Rejected: stopping with a configuration error, because the optional narrative must never stop the verdict. | Assumption |
| D11 | What does PierPressure send? | A fixed `task_name`, `instructions` made of the existing system framing then the existing prompt text, the named `entity_id`, and no `structure` or attachments. The words of the prompt do not change. There is no output-length setting on the action. | Evidence: `pierpressure/explain/provider.py` (`SYSTEM_PROMPT`); Assumption (joining them) |
| D12 | What counts as a usable reply? | HTTP 200 whose `service_response.data` is non-empty text. Any other status, a body that is not JSON, or a `data` that is missing or not text is a failure: no narrative. | Evidence: D3 sources; Assumption |
| D13 | Timeout, cache and failure handling? | The same as today: the explainer's per-call timeout and wrapper, the same cache, and on any failure no narrative and an unavailable entity, with the verdict on time. The log names only the error's kind and HTTP status (#92). The token and reply text are never logged, and proxy settings in the environment never see the token. | Evidence: `verdict-narrative` spec; `pierpressure/explain/explainer.py` `_failure_kind`; `pierpressure/supervisor.py` (`trust_env=False`) |
| D14 | Does the ADR say what the issue asks? | Yes: calling Home Assistant for the optional narrative does not make it load-bearing, because only the narrative depends on the call, which is bounded and fails to "no narrative". It also records the administrator access `homeassistant_api` grants. | Evidence: #88 packet; AGENTS.md durable constraints |
| D15 | Does the glossary change? | No. The glossary's **Provider** is a forecast source. The specs say "the explainer's provider" and "AI Task entity" (Home Assistant's own term), so the meanings stay apart. | Evidence: `openspec/glossary.md` "Provider"; Assumption |
| D16 | How is it accepted? | Tests with a fake HTTP transport check the request, the reply parsing, each failure, and that no log line holds the token or reply text. Tests check the add-on schema, options, permission, labels, the combine and its conflicts, and the startup log lines. A documented manual check runs it against a real AI Task entity. | Assumption |

## Changes from the story

- The form's explainer fields join `config.yaml` key by key (D8), not as one
  grouped setting. #150 shipped after this packet and documents the key on the
  form with `enabled` and `model` in `config.yaml`; grouping would break that
  setup.
- Added a named setting, `explainer.ai_task_entity`, that selects this path
  (D4, D5). The packet named the field but not how it picks the provider.
- Added the behavior for an entity outside the add-on (D10) and for an entity
  with an API key (D9).
- Corrected a fact: AI Task first shipped in Home Assistant 2025.7; 2025.8
  announced it and added the preferred-entity setting. This changes nothing.

Confirmed by user: yes
