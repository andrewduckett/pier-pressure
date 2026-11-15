## 1. The failure log line

- [x] 1.1 [easy] When a provider raises `RuntimeError("connection refused for key sk-marker")`, the explainer still yields no narrative and logs exactly one WARNING that names `RuntimeError`, and no captured record's message, `msg` or `args` contains `sk-marker` or `connection refused` (brainstorm D3, D5) (verify: uv run pytest tests/test_explainer.py -k failure_log) (✓ uv run pytest tests/test_explainer.py -k failure_log passed)
- [ ] 1.2 [easy] That WARNING carries no traceback: its `exc_info` and `exc_text` are empty, and `caplog.text` contains neither `sk-marker` nor `connection refused` (brainstorm D5) (verify: uv run pytest tests/test_explainer.py -k failure_log)
- [ ] 1.3 [medium] `PydanticAIProvider` with a function model that raises `ModelHTTPError.for_category(ModelAuthenticationError, status_code=401, ...)`, whose body says `Incorrect API key provided: sk-proj-ab12...wxyz` for the key `sk-proj-ab12marker90wxyz`, logs one WARNING naming `ModelAuthenticationError` and `HTTP 401`, and no log text contains `sk-proj-ab12`, `wxyz` or `Incorrect API key provided`, with no network (brainstorm D1, D7) (verify: uv run pytest tests/test_explainer.py -k rejected_key)
- [ ] 1.4 [easy] A provider error whose `status_code` attribute is not an integer, such as the text `401 for sk-marker`, is logged by its class name alone, with no `HTTP` part and no `sk-marker` (brainstorm D3) (verify: uv run pytest tests/test_explainer.py -k failure_log)
- [ ] 1.5 [easy] The whole change passes the CI gate (verify: mise run check)

## Deviations Ledger

<!-- Dated notes on small departures from the plan, written during apply. Stop and ask the user about a large one. -->
