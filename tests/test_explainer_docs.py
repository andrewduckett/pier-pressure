"""Task 7.2: the operator doc and sample config for the LLM explainer.

A light guard that the plain-language doc stays present and keeps covering its points
(enabling with a model + ``${ENV}`` key, disabled-by-default, the orphan-entity
removal step, and the manual acceptance check), and that the sample config loads and
enables the explainer.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from pierpressure.core.config import load_config

_ROOT = Path(__file__).resolve().parent.parent
_DOC = _ROOT / "docs" / "llm-explainer.md"
_SAMPLE = _ROOT / "docs" / "examples" / "config.explainer.yaml"


def test_explainer_doc_exists() -> None:
    assert _DOC.is_file()


@pytest.fixture
def doc_text() -> str:
    return _DOC.read_text(encoding="utf-8").lower()


@pytest.mark.parametrize(
    "topic",
    [
        "disabled by default",
        "model",
        "${anthropic_api_key}",  # the ${ENV} api key form
        "retained discovery topic",  # the orphan-entity removal step
        "unavailable",
        "manual acceptance check",
        "never feeds",  # the LLM never touches the numbers
    ],
)
def test_doc_covers_its_points(doc_text: str, topic: str) -> None:
    assert topic in doc_text


def test_sample_config_loads_and_enables_the_explainer(monkeypatch: pytest.MonkeyPatch) -> None:
    # Ensure the key stays an unexpanded placeholder regardless of the ambient env.
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    config = load_config(_SAMPLE)
    assert config.explainer is not None
    assert config.explainer.enabled is True
    assert config.explainer.model == "claude-opus-5"
    # The unset ${ENV} key stays a visible placeholder rather than a blank secret.
    assert config.explainer.api_key == "${ANTHROPIC_API_KEY}"
