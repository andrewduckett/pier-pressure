Practice TDD: for each behavior, write the failing test first, then implement.
`just check` (ruff lint + format, mypy strict, pytest) is the CI gate and must be
green before the PR. No test may make a real network call — the LLM provider is
always exercised through a fake or a mocked client.

## 1. Dependency and configuration

- [x] 1.1 Add the Anthropic SDK with `uv add anthropic`, and verify `pyproject.toml` and `uv.lock` update in step and the package imports.
- [x] 1.2 Write failing tests for an optional `explainer` config block on `AppConfig`: `enabled` (default `false`), a provider/model identifier, and an API key resolved through the existing `${ENV}` expansion; an absent block or `enabled: false` yields a disabled explainer. Implement the config and verify the tests pass, including that a missing `${ENV}` key leaves a visible placeholder rather than a blank secret.

## 2. Explainer edge package (`pierpressure/explain/`)

- [x] 2.1 Write a failing test that the package exposes an `Explainer = Callable[[VerdictDocument], str | None]` type and a default no-op explainer that returns `None`. Implement and verify.
- [x] 2.2 Write failing tests for the prompt-input builder: it is derived only from the document's verdict, score, confidence, `reasons`, and the top targets' emitted fields (no astronomy/conditions source), and is stable for identical documents. Implement and verify.
- [x] 2.3 Write failing tests for the provider interface and a fake provider double that returns text with no network. Implement the interface and the fake, and verify a narrative is produced through the double.
- [x] 2.4 Write failing tests for the narrative cache keyed on a hash of the exact prompt input (spec verdict-narrative — "Narratives are cached..."): identical influencing terms reuse the cached prose with one provider call; a changed target field (e.g. a new `transit_time` or `max_altitude`) or a changed `confidence` triggers a fresh call. Implement the cache and verify.
- [x] 2.5 Write failing tests for the graceful-fallback wrapper: a provider that raises, times out, or returns nothing usable makes the explainer return `None`, log the failure, and never raise or block; the call carries a bounded timeout. Implement and verify.
- [x] 2.6 Implement the default Anthropic provider behind the interface, and verify with a mocked SDK client (no network) that it builds a request from the prompt input and returns text, and that a missing/invalid API key degrades to `None` rather than raising.

## 3. Core-purity boundary guard

- [x] 3.1 Extend `tests/test_core_boundary.py`'s `_FORBIDDEN` list with `pierpressure.explain` and `anthropic`, and verify the boundary test passes — the pure core imports neither the explainer package nor the SDK.

## 4. Delivery: the narrative sensor (`pierpressure/delivery/`)

- [x] 4.1 Write a failing test that `publish_verdict` accepts an optional `narrative` and that delivery is told once (from config) whether it manages the narrative entity; when narrative delivery is **disabled**, no narrative discovery or state is published and the verdict, score, top-target, and refresh entities are published exactly as before (spec ha-delivery — "Disabled narrative delivery publishes no entity"). Implement enough to make it pass.
- [x] 4.2 Write failing tests for the **enabled + present** case: a retained narrative-sensor discovery payload validates against Home Assistant's sensor schema, derives its unique identity from the pier id, carries a short state marker, and publishes the full prose in a JSON attributes payload. Implement and verify.
- [x] 4.3 Write failing tests for the **enabled + absent** case: the adapter actively publishes the narrative sensor's unavailable state (not a skipped update), so a previously published retained narrative is not left shown as current, while the other entities still publish (spec ha-delivery — "Enabled but missing narrative renders unavailable", "A prior retained narrative is not shown as current"). Implement and verify.
- [x] 4.4 Verify a test that with narrative delivery disabled the full MQTT discovery/state output is byte-identical to the pre-change output for the same document — the entity is purely additive.

## 5. Service wiring

- [x] 5.1 Write a failing test that the service wires the real provider-backed explainer and a managing delivery when `enabled: true`, and the no-op explainer with a non-managing delivery when disabled; `_publish` computes the narrative from the produced document and passes it to `publish_verdict`. Implement the wiring in `service.py` and the config-to-component construction in `__main__`, and verify.
- [x] 5.2 Verify a test that when the explainer raises or times out, the pier's verdict is still published on time and the narrative entity resolves to unavailable — a failing explainer never blocks or delays delivery (spec verdict-narrative — "The explainer degrades gracefully on failure").

## 6. Determinism and additive-contract guard

- [x] 6.1 Verify a test that the verdict document is byte-identical for the same inputs whether the explainer is enabled or disabled — the narrative lives entirely outside the document (ADR-0011); regenerate any golden delivery fixtures and confirm only the additive narrative entity appears, and only when enabled.

## 7. Cleanup, documentation, and gate

- [x] 7.1 Correct the stale "M6 LLM layer" references now that M6 shipped as equipment ranking and the LLM explainer is M7 — the `Target` docstring in `pierpressure/core/model.py` and the M6 wording in `docs/adr/0009-targets-structured-additive-fill.md`; verify `grep -ri "M6 .*LLM\|M6 (the LLM"` finds no remaining hits.
- [x] 7.2 Add operator documentation and a sample config: how to enable the explainer (model + `${ENV}` API key), the disabled-by-default behavior, and the one-time step to remove an orphaned narrative entity (clear its retained discovery topic) after enabling then disabling; verify the sample config loads. Include the documented manual acceptance check that the generated prose reads as a faithful plain-language summary of a verdict (spec verdict-narrative).
- [x] 7.3 In the landing PR, flip `docs/roadmap.md` M7 status to done.
- [x] 7.4 Run `just check` and verify ruff (lint + format), mypy strict, and pytest are all green before opening the PR.
