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

from pierpressure.core.config import ConfigError, ExplainerConfig, load_config

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


def test_malformed_explainer_block_raises_a_clean_config_error(tmp_path: Path) -> None:
    # A structurally invalid explainer block fails only at final assembly (per-pier
    # validation does not touch it). It must surface as a wrapped ConfigError, not a
    # raw pydantic ValidationError.
    text = (
        _CONFIG_HEAD
        + """
explainer:
  enabled: true
  extra_unknown_field: nope
"""
    )
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, text))


def test_assembly_error_label_does_not_hard_code_the_explainer(tmp_path: Path) -> None:
    # The assembly-time re-validation covers piers as well as the explainer, so the
    # error label must stay neutral rather than always blaming the explainer.
    text = (
        _CONFIG_HEAD
        + """
explainer:
  enabled: true
  extra_unknown_field: nope
"""
    )
    with pytest.raises(ConfigError) as exc_info:
        load_config(_write(tmp_path, text))
    assert "invalid explainer configuration" not in str(exc_info.value).lower()


def test_default_explainer_config_is_disabled() -> None:
    explainer = ExplainerConfig()
    assert explainer.enabled is False


def test_enabled_false_block_is_parsed_but_disabled(tmp_path: Path) -> None:
    text = (
        _CONFIG_HEAD
        + """
explainer:
  enabled: false
  model: anthropic:claude-opus-5
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
  model: anthropic:claude-opus-5
  api_key: ${PIERPRESSURE_LLM_KEY}
"""
    )
    config = load_config(_write(tmp_path, text))
    assert config.explainer is not None
    assert config.explainer.enabled is True
    assert config.explainer.model == "anthropic:claude-opus-5"
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
