"""Task 1.2: the optional ``explainer`` config block on ``AppConfig``.

The explainer is disabled by default: an absent block or ``enabled: false`` yields
a disabled explainer. The API key resolves through the same ``${ENV}`` expansion as
the broker credentials, and a missing key leaves a visible ``${VAR}`` placeholder
rather than a blank secret.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from pierpressure.core.config import ExplainerConfig, load_config

_CONFIG_HEAD = """
mqtt:
  host: 192.168.1.10
recompute:
  interval_seconds: 900
piers:
  - id: backyard
    latitude: 51.50
    longitude: -0.12
    elevation_m: 30
"""


def _write(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "config.yaml"
    path.write_text(text, encoding="utf-8")
    return path


def test_absent_block_yields_a_disabled_explainer(tmp_path: Path) -> None:
    config = load_config(_write(tmp_path, _CONFIG_HEAD))
    assert config.explainer is None


def test_default_explainer_config_is_disabled() -> None:
    explainer = ExplainerConfig()
    assert explainer.enabled is False


def test_enabled_false_block_is_parsed_but_disabled(tmp_path: Path) -> None:
    text = (
        _CONFIG_HEAD
        + """
explainer:
  enabled: false
  model: claude-opus-5
"""
    )
    config = load_config(_write(tmp_path, text))
    assert config.explainer is not None
    assert config.explainer.enabled is False


def test_enabled_block_carries_model_and_api_key(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PIERPRESSURE_LLM_KEY", "sk-test-123")
    text = (
        _CONFIG_HEAD
        + """
explainer:
  enabled: true
  model: claude-opus-5
  api_key: ${PIERPRESSURE_LLM_KEY}
"""
    )
    config = load_config(_write(tmp_path, text))
    assert config.explainer is not None
    assert config.explainer.enabled is True
    assert config.explainer.model == "claude-opus-5"
    assert config.explainer.api_key == "sk-test-123"


def test_missing_api_key_env_leaves_a_visible_placeholder(tmp_path: Path) -> None:
    text = (
        _CONFIG_HEAD
        + """
explainer:
  enabled: true
  api_key: ${PIERPRESSURE_LLM_KEY_UNSET}
"""
    )
    config = load_config(_write(tmp_path, text))
    assert config.explainer is not None
    # A missing secret stays a visible placeholder rather than an empty string.
    assert config.explainer.api_key == "${PIERPRESSURE_LLM_KEY_UNSET}"


def test_unknown_explainer_field_is_rejected() -> None:
    with pytest.raises(ValidationError):
        ExplainerConfig(enabled=True, unexpected="x")  # type: ignore[call-arg]
