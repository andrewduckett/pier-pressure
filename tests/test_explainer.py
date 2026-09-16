"""Section 2: the explainer edge package (`pierpressure/explain/`).

Covers the public type and no-op (2.1), the prompt-input builder (2.2), the
provider interface and a network-free double (2.3), the deterministic-terms cache
(2.4), the graceful-fallback wrapper with a bounded timeout (2.5), and the default
Pydantic AI provider driven by an injected test model (2.6). No test makes a real
network call — the provider is always a fake or an injected Pydantic AI test model.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import pytest

from pierpressure.core.model import (
    Band,
    Confidence,
    DarkWindow,
    Moon,
    MoonPhase,
    Target,
    TargetWindow,
    Verdict,
    VerdictDocument,
)
from pierpressure.explain import (
    Explainer,
    FakeProvider,
    NarrativeExplainer,
    PromptInput,
    PydanticAIProvider,
    build_explainer,
    build_prompt_input,
    no_op_explainer,
)

from .offline_guard import no_network


def _target(
    *,
    target_id: str = "M31",
    max_altitude: float = 55.0,
    transit_hour: int = 1,
    moon_separation: float = 120.0,
) -> Target:
    return Target(
        id=target_id,
        name="Andromeda Galaxy",
        type="Galaxy",
        score=80,
        window=TargetWindow(
            start=datetime(2026, 9, 8, 21, 0, tzinfo=UTC),
            end=datetime(2026, 9, 9, 3, 0, tzinfo=UTC),
        ),
        max_altitude=max_altitude,
        transit_time=datetime(2026, 9, 9, transit_hour, 0, tzinfo=UTC),
        moon_separation=moon_separation,
    )


def _document(
    *,
    verdict: Verdict = Verdict.GO,
    score: int | None = 72,
    confidence_value: int = 80,
    confidence_band: Band = Band.HIGH,
    reasons: list[str] | None = None,
    targets: list[Target] | None = None,
    generated_at: datetime | None = None,
) -> VerdictDocument:
    return VerdictDocument(
        pier="backyard",
        generated_at=generated_at or datetime(2026, 9, 8, 20, 0, tzinfo=UTC),
        verdict=verdict,
        score=score,
        confidence=Confidence(band=confidence_band, value=confidence_value),
        reasons=reasons or ["Cloud: 5% (clear)", "Moon: 10% illuminated"],
        targets=targets if targets is not None else [_target()],
        dark_window=DarkWindow(
            start=datetime(2026, 9, 8, 20, 30, tzinfo=UTC),
            end=datetime(2026, 9, 9, 3, 25, tzinfo=UTC),
        ),
        moon=Moon(illumination=0.1, phase=MoonPhase.WAXING_CRESCENT),
    )


# --------------------------------------------------------------------------- #
# 2.1 — the Explainer type and default no-op
# --------------------------------------------------------------------------- #


def test_no_op_explainer_returns_none() -> None:
    explainer: Explainer = no_op_explainer
    assert explainer(_document()) is None


# --------------------------------------------------------------------------- #
# 2.2 — the prompt-input builder
# --------------------------------------------------------------------------- #


def test_prompt_input_is_stable_for_identical_documents() -> None:
    a = build_prompt_input(_document())
    b = build_prompt_input(_document())
    assert isinstance(a, PromptInput)
    assert a.text == b.text
    assert a.key == b.key


def test_prompt_input_ignores_generated_at() -> None:
    # generated_at is not part of the prompt, so two recomputes of the same verdict
    # at different instants build an identical prompt (design D4).
    early = build_prompt_input(_document(generated_at=datetime(2026, 9, 8, 20, 0, tzinfo=UTC)))
    later = build_prompt_input(_document(generated_at=datetime(2026, 9, 8, 22, 0, tzinfo=UTC)))
    assert early.text == later.text


def test_prompt_input_reflects_the_verdict_terms() -> None:
    text = build_prompt_input(_document()).text
    assert "GO" in text
    assert "Cloud: 5% (clear)" in text
    assert "M31" in text


def test_prompt_input_changes_when_a_term_changes() -> None:
    base = build_prompt_input(_document()).text
    assert base != build_prompt_input(_document(verdict=Verdict.MAYBE)).text
    assert base != build_prompt_input(_document(score=50)).text
    assert base != build_prompt_input(_document(confidence_value=40)).text
    assert base != build_prompt_input(_document(reasons=["different"])).text
    assert base != build_prompt_input(_document(targets=[_target(max_altitude=30.0)])).text


# --------------------------------------------------------------------------- #
# 2.3 — the provider interface and a network-free double
# --------------------------------------------------------------------------- #


def test_fake_provider_returns_text_without_network() -> None:
    provider = FakeProvider(text="Tonight is a go.")
    explainer = NarrativeExplainer(provider)
    with no_network():
        narrative = explainer(_document())
    assert narrative == "Tonight is a go."
    assert provider.calls == 1


# --------------------------------------------------------------------------- #
# 2.4 — the deterministic-terms cache
# --------------------------------------------------------------------------- #


def test_identical_terms_reuse_the_cache_with_one_provider_call() -> None:
    provider = FakeProvider(text="Cached prose.")
    explainer = NarrativeExplainer(provider)
    first = explainer(_document())
    # A later recompute at a different instant but identical terms reuses the cache.
    second = explainer(_document(generated_at=datetime(2026, 9, 8, 23, 0, tzinfo=UTC)))
    assert first == second == "Cached prose."
    assert provider.calls == 1


def test_a_changed_target_field_triggers_a_fresh_call() -> None:
    provider = FakeProvider(text="Prose.")
    explainer = NarrativeExplainer(provider)
    explainer(_document(targets=[_target(max_altitude=55.0)]))
    explainer(_document(targets=[_target(max_altitude=40.0)]))  # new max_altitude
    assert provider.calls == 2


def test_a_changed_confidence_triggers_a_fresh_call() -> None:
    provider = FakeProvider(text="Prose.")
    explainer = NarrativeExplainer(provider)
    explainer(_document(confidence_band=Band.HIGH, confidence_value=80))
    explainer(_document(confidence_band=Band.MEDIUM, confidence_value=55))
    assert provider.calls == 2


def test_the_cache_is_bounded_and_evicts_the_oldest_entry() -> None:
    provider = FakeProvider(text="Prose.")
    explainer = NarrativeExplainer(provider, max_cache=2)
    explainer(_document(score=10))
    explainer(_document(score=20))
    explainer(_document(score=30))  # evicts score=10 (least recently used)
    assert len(explainer._cache) == 2
    # score=10 was evicted, so re-requesting it is a fresh provider call.
    calls_before = provider.calls
    explainer(_document(score=10))
    assert provider.calls == calls_before + 1


# --------------------------------------------------------------------------- #
# 2.5 — the graceful-fallback wrapper
# --------------------------------------------------------------------------- #


@dataclass
class _RaisingProvider:
    calls: int = 0

    def generate(self, prompt: PromptInput) -> str:
        self.calls += 1
        raise RuntimeError("provider is down")


@dataclass
class _EmptyProvider:
    calls: int = 0

    def generate(self, prompt: PromptInput) -> str:
        self.calls += 1
        return "   "


@dataclass
class _SleepingProvider:
    delay: float
    calls: int = 0

    def generate(self, prompt: PromptInput) -> str:
        self.calls += 1
        time.sleep(self.delay)
        return "too slow"


def test_a_raising_provider_yields_none() -> None:
    explainer = NarrativeExplainer(_RaisingProvider())
    assert explainer(_document()) is None


def test_an_empty_response_yields_none_and_is_not_cached() -> None:
    provider = _EmptyProvider()
    explainer = NarrativeExplainer(provider)
    assert explainer(_document()) is None
    # A useless empty result is not cached, so a later recompute tries again.
    assert explainer(_document()) is None
    assert provider.calls == 2


def test_a_timeout_yields_none_without_blocking() -> None:
    provider = _SleepingProvider(delay=0.3)
    explainer = NarrativeExplainer(provider, timeout=0.05)
    started = time.monotonic()
    result = explainer(_document())
    elapsed = time.monotonic() - started
    assert result is None
    assert elapsed < 0.25  # returned on the timeout, not after the full sleep


def test_a_failure_never_raises_into_the_caller() -> None:
    explainer = NarrativeExplainer(_RaisingProvider())
    # No exception escapes; the wrapper is the graceful boundary.
    assert explainer(_document(verdict=Verdict.NO_GO, score=None)) is None


# --------------------------------------------------------------------------- #
# 2.6 — the default Pydantic AI provider, driven by an injected test model
# --------------------------------------------------------------------------- #


def _function_model(reply: str, captured: list[str]) -> Any:
    """A Pydantic AI FunctionModel that records the messages and returns fixed text."""
    from pydantic_ai.messages import ModelResponse, TextPart
    from pydantic_ai.models.function import FunctionModel

    def respond(messages: Any, info: Any) -> Any:
        captured.append(str(messages))
        return ModelResponse(parts=[TextPart(content=reply)])

    return FunctionModel(respond)


def test_pydantic_provider_returns_model_text() -> None:
    from pydantic_ai.models.test import TestModel

    provider = PydanticAIProvider(
        model="anthropic:claude-opus-5",
        model_obj=TestModel(custom_output_text="A clear, quiet night — go."),
    )
    with no_network():
        assert provider.generate(build_prompt_input(_document())) == "A clear, quiet night — go."


def test_pydantic_provider_passes_the_prompt_input_to_the_model() -> None:
    captured: list[str] = []
    provider = PydanticAIProvider(
        model="anthropic:claude-opus-5",
        model_obj=_function_model("prose", captured),
    )
    prompt = build_prompt_input(_document())
    with no_network():
        provider.generate(prompt)
    # The request carries the built prompt input, not raw astronomy.
    assert prompt.text in captured[0]


def test_pydantic_provider_with_missing_key_degrades_to_none() -> None:
    # A real model spec with no usable key reaches Pydantic AI, which raises before
    # any network under the offline guard; the wrapper turns that into no narrative.
    provider = PydanticAIProvider(
        model="anthropic:claude-opus-5", api_key="${PIERPRESSURE_LLM_KEY_UNSET}"
    )
    explainer = NarrativeExplainer(provider)
    with no_network():
        assert explainer(_document()) is None


def test_pydantic_provider_scopes_the_key_to_the_call(monkeypatch: pytest.MonkeyPatch) -> None:
    import os

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    seen: dict[str, str | None] = {}

    def respond(messages: Any, info: Any) -> Any:
        from pydantic_ai.messages import ModelResponse, TextPart

        seen["during"] = os.environ.get("OPENAI_API_KEY")
        return ModelResponse(parts=[TextPart(content="ok")])

    from pydantic_ai.models.function import FunctionModel

    provider = PydanticAIProvider(
        model="openai:gpt-4o", api_key="sk-openai-test", model_obj=FunctionModel(respond)
    )
    with no_network():
        provider.generate(build_prompt_input(_document()))

    # The key is visible to the provider during the call, and gone afterwards — it is
    # never left persisting in the process environment.
    assert seen["during"] == "sk-openai-test"
    assert os.environ.get("OPENAI_API_KEY") is None


# --------------------------------------------------------------------------- #
# build_explainer factory
# --------------------------------------------------------------------------- #


def test_build_explainer_returns_no_op_when_config_absent() -> None:
    assert build_explainer(None) is no_op_explainer


def test_build_explainer_returns_no_op_when_disabled() -> None:
    from pierpressure.core.config import ExplainerConfig

    assert build_explainer(ExplainerConfig(enabled=False)) is no_op_explainer


def test_build_explainer_wires_a_real_provider_when_enabled() -> None:
    from pierpressure.core.config import ExplainerConfig

    explainer = build_explainer(
        ExplainerConfig(enabled=True, model="anthropic:claude-opus-5", api_key="k")
    )
    assert isinstance(explainer, NarrativeExplainer)
