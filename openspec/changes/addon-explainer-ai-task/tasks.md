## 1. The setting

- [x] 1.1 [easy] `explainer.ai_task_entity` accepts `ai_task.google_ai_task`, and rejects `light.kitchen` with a configuration error that names `explainer.ai_task_entity` and does not contain the value (design DD4) (verify: uv run pytest tests/test_explainer_config.py) (✓ uv run pytest tests/test_explainer_config.py passed, 17 tests)

## 2. The AI Task provider [depends-on: 1]

- [x] 2.1 [medium] The AI Task provider sends one `POST http://supervisor/core/api/services/ai_task/generate_data?return_response` with `Authorization: Bearer <token>` and a JSON body of exactly `task_name`, `instructions` (system framing, then the prompt text) and `entity_id`, from a client that ignores proxy settings in the environment (DD1, DD2) (verify: uv run pytest tests/test_ai_task_provider.py) (✓ uv run pytest tests/test_ai_task_provider.py passed, 5 tests)
- [x] 2.2 [medium] Through `NarrativeExplainer`, a 200 reply whose `service_response.data` is text becomes the stripped narrative; a 200 reply that is not JSON, or whose `data` is missing, empty or not text, gives no narrative (DD3) (verify: uv run pytest tests/test_ai_task_provider.py) (✓ uv run pytest tests/test_ai_task_provider.py passed, 14 tests)
- [x] 2.3 [medium] Through `NarrativeExplainer`, statuses 400, 401, 403, 500 and 502, a refused connection, and a request that never answers each give no narrative within the explainer's bound; the one log line names only the error's kind and any HTTP status, and no log line holds the reply text or the token (DD3, DD7) (verify: uv run pytest tests/test_ai_task_provider.py) (✓ uv run pytest tests/test_ai_task_provider.py passed, 27 tests)
- [x] 2.4 [medium] `build_explainer` picks the provider by the DD5 table: an AI Task explainer with a token logs the entity in use and, when an API key is set, that the key is not used, without its value; with no token it returns the no-op explainer and logs one warning that names `explainer.ai_task_entity` and the add-on (verify: uv run pytest tests/test_explainer.py) (✓ uv run pytest tests/test_explainer.py passed, 33 tests)
- [x] 2.5 [medium] The service passes `SUPERVISOR_TOKEN` to `build_explainer`; with no token and an AI Task entity set, it publishes every verdict, keeps the narrative entity and resolves it to unavailable, and sends no request (verify: uv run pytest tests/test_main.py) (✓ uv run pytest tests/test_main.py passed, 124 tests)

## 3. The add-on form [depends-on: 1]

- [x] 3.1 [easy] The add-on config sets `homeassistant_api: true`, and its schema's `explainer` block is `enabled: bool?`, `ai_task_entity: str?`, `api_key: password?` in that order, with `options.explainer` still `{}` (DD6) (verify: uv run pytest tests/test_ha_addon.py) (✓ uv run pytest tests/test_ha_addon.py passed, 102 tests)
- [x] 3.2 [easy] The English translation labels **Enabled** and **AI Task entity**, each description contains `Optional.`, and the `explainer` description names `explainer.enabled`, `AI Task`, `explainer.model` and `config.yaml` (verify: uv run pytest tests/test_ha_addon.py) (✓ uv run pytest tests/test_ha_addon.py passed, 102 tests)
- [x] 3.3 [medium] The form's `explainer.enabled` of false counts as not set; a form with `enabled` true and an AI Task entity turns the explainer on with no `config.yaml`; `enabled` in both places stops the add-on naming `explainer.enabled`; a form entity combines with the file's `enabled` and `model` (DD6) (verify: uv run pytest tests/test_addon_options.py tests/test_addon_settings.py tests/test_main.py) (✓ uv run pytest tests/test_addon_options.py tests/test_addon_settings.py tests/test_main.py passed, 293 tests)

## 4. The docs [depends-on: 2, 3]

- [x] 4.1 [easy] The "Turn on the explainer" section of `ha-addon/DOCS.md` describes the AI Task way, with `**Enabled**`, `**AI Task entity**` and `AI Task`, beside the API key way; it says the add-on gains administrator access to Home Assistant, that a model slower than the explainer's time bound gives no narrative, and to set `explainer.enabled` in one place only (verify: uv run pytest tests/test_ha_addon.py) (✓ uv run pytest tests/test_ha_addon.py passed, 108 tests)
- [x] 4.2 [easy] `docs/llm-explainer.md` describes `explainer.ai_task_entity`, says it works only in the add-on, and adds the AI Task path to the manual acceptance check (verify: uv run pytest tests/test_explainer_docs.py) (✓ uv run pytest tests/test_explainer_docs.py passed, 12 tests)

## 5. The whole change [depends-on: 4]

- [ ] 5.1 [easy] The CI gate passes on the finished change (verify: mise run check)

## Deviations Ledger

<!-- Dated notes on small departures from the plan, written during apply. Stop and ask the user about a large one. -->

- 2026-11-15: Tasks 3.1 and 3.2 share one commit. The existing check that every
  form field has a label fails as soon as the schema gains `enabled` and
  `ai_task_entity`, so the schema cannot land green without its labels.
