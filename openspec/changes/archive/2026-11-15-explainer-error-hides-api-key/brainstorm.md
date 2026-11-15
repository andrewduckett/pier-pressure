**Why:** When an LLM provider call fails, the explainer logs the error's text, which can quote part of the API key, so a user who shares the log shares part of their key; #89 closed the other paths, and this is the one left.

## Story

#92 explainer-error-hides-api-key — a failed explainer call never logs part of
the API key.
https://github.com/andrewduckett/pier-pressure/issues/92

The issue has no comments.

## Decisions

The user delegated this brainstorm: the brief said to take the recommended
answer to each question, record the alternatives, and go on without asking. So
each row that code or a document did not settle is an `Assumption`, and the
rejected alternatives follow the answer.

| # | Question | Answer | Source |
|---|---|---|---|
| D1 | Does the error text really hold the provider's reply? | Yes. Pydantic AI 2.67's `ModelHTTPError` builds its text as `status_code: <n>, model_name: <m>, body: <reply>`. A 401 built offline with `ModelHTTPError.for_category(ModelAuthenticationError, ...)` and OpenAI's reply prints `Incorrect API key provided: sk-proj-ab12...wxyz` in `str(exc)`. | Evidence: `.venv/.../pydantic_ai/exceptions.py` (`ModelHTTPError.__init__`), reproduced offline |
| D2 | Must the change first record what each LLM provider in `_PROVIDER_KEY_ENV` puts in its reply? | No. D3 drops all error text, whatever the LLM provider, so a list of each provider's reply would not change the fix or the test. D1 is the reproduction. Rejected: record each provider's reply (work with no effect on the plan, and it needs each SDK's error classes). | Assumption |
| D3 | What does the failure log line hold? | The error's class name and, when the error has one, its HTTP status code, for example `explainer provider failed: ModelAuthenticationError (HTTP 401); no narrative`. Nothing else from the error. Rejected: also the provider's error code, such as `invalid_api_key` (provider text, and the class name already tells a rejected key from a missing model); also the model name (the user already knows it from the configuration). | Assumption |
| D4 | Could the key be masked in the text instead of dropping the text? | No. A reply that quotes part of the key, such as its start and last four characters, does not hold the whole key, so `redact.mask_key` cannot find it, and guessing which fragments to mask is fragile. Rejected: mask fragments of the key; log the full text at DEBUG level (a shared DEBUG log leaks it the same way). | Evidence: `pierpressure/redact.py` (`_MaskFilter._mask` replaces the whole key only) |
| D5 | Where does the rule live? | In the explainer wrapper, `NarrativeExplainer._generate`, which catches every provider failure. It then holds for any provider, not only Pydantic AI. The log keeps no traceback, as today, because a traceback prints the error's text. Rejected: clean the error inside `PydanticAIProvider.generate` (each provider would need its own cleaning). | Evidence: `pierpressure/explain/explainer.py` |
| D6 | What is lost, and is that acceptable? | The error's own words: for example Pydantic AI's message that says which key variable to set when no key is supplied. The class name still says what kind of failure it was. Accepted, because a log a user shares must never show any part of a key. | Assumption |
| D7 | How is it tested? | Two `caplog` tests. One gives the wrapper a provider whose error text holds a marker key. The other runs `PydanticAIProvider` with a function model that raises the real 401 error from D1, with a reply that quotes part of a marker key. Each checks that no log line holds the marker or any part of it, and that the line names the class and, for the 401, `HTTP 401`. No network is used. | Evidence: `tests/test_explainer.py` (`_RaisingProvider`, `_function_model`, `no_network`) |
| D8 | Which spec changes? | `verdict-narrative` gains one requirement: a failed explainer call is logged with the error's kind and HTTP status code only, never the error's text or the LLM provider's reply. The existing failure requirements stay as they are. | Evidence: `openspec/specs/verdict-narrative/spec.md` (An explainer failure never blocks the verdict) |
| D9 | Do the timeout and empty-reply paths change? | No. They log no provider text, as the packet says. | Evidence: `pierpressure/explain/explainer.py` |
| D10 | Do the user docs change? | No. No document quotes the failure log line or tells the user to read the error's text. | Evidence: search of `README.md` and `docs/` for the log line |

## Changes from the story

- The packet's first scope item, to record each LLM provider's reply, is cut.
  D1 reproduces the leak offline, and D2 says why a list of each provider's
  reply would not change the fix.

The brief's instruction to proceed on recommendations stands in for the user's
confirmation of this ledger.

Confirmed by user: yes
