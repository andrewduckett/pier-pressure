"""Task 1.2: the optional ``explainer`` config block on ``AppConfig``.

The explainer is disabled by default: an absent block or ``enabled: false`` yields
a disabled explainer. The API key resolves through the same ``${ENV}`` expansion as
the broker credentials, and a missing key leaves a visible ``${VAR}`` placeholder
rather than a blank secret.
"""

from __future__ import annotations

import logging
import traceback
from pathlib import Path

import pytest
from pydantic import SecretStr, ValidationError

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
    # A structurally invalid explainer block must surface as a wrapped ConfigError,
    # not a raw pydantic ValidationError.
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


def test_an_explainer_error_names_the_explainer_block(tmp_path: Path) -> None:
    # The explainer block is validated on its own, before the final assembly, so
    # its error names it (config-secrets-hidden-in-errors D2).
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
    assert str(exc_info.value).startswith("Invalid explainer configuration: ")


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
    assert config.explainer.api_key == SecretStr("sk-test-123")


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
    assert config.explainer.api_key == SecretStr("${PIERPRESSURE_LLM_KEY_UNSET}")


def test_unknown_explainer_field_is_rejected() -> None:
    with pytest.raises(ValidationError):
        ExplainerConfig(enabled=True, unexpected="x")  # type: ignore[call-arg]


# --------------------------------------------------------------------------- #
# config-secrets-hidden-in-errors: an explainer error shows none of its text (D1-D3, D6)
# --------------------------------------------------------------------------- #

MARKER = "sk-5e3d91"
EXPLAINER_SETTINGS = ("enabled", "model", "api_key")


def _hidden_error(
    tmp_path: Path, block: str, caplog: pytest.LogCaptureFixture, *hidden: str
) -> str:
    """Load ``block`` after a valid head; no ``hidden`` text is in the error, log or traceback."""
    with caplog.at_level(logging.DEBUG), pytest.raises(ConfigError) as error:
        load_config(_write(tmp_path, _CONFIG_HEAD + block))
    message = str(error.value)
    shown = "".join(traceback.format_exception(error.value))
    for text in hidden:
        assert text not in message
        assert text not in shown
        assert text not in caplog.text
    return message


def test_an_api_key_that_is_a_number_is_named_without_its_value(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    block = "explainer:\n  enabled: true\n  api_key: 12345\n"

    message = _hidden_error(tmp_path, block, caplog, "12345")

    assert "explainer.api_key" in message


@pytest.mark.parametrize(
    ("line", "hidden"),
    [(f"apikey: {MARKER}", ("apikey", MARKER)), (f"{MARKER}:", (MARKER,))],
    ids=["misspelled-key", "bare-key"],
)
def test_an_unknown_explainer_key_is_not_named(
    tmp_path: Path, caplog: pytest.LogCaptureFixture, line: str, hidden: tuple[str, ...]
) -> None:
    block = f"explainer:\n  enabled: true\n  {line}\n"

    message = _hidden_error(tmp_path, block, caplog, *hidden)

    assert "the explainer block holds a setting it does not know" in message
    for setting in EXPLAINER_SETTINGS:
        assert setting in message


@pytest.mark.parametrize("value", [f"[{MARKER}]", MARKER], ids=["list", "text"])
def test_an_explainer_block_that_is_not_a_mapping_does_not_show_its_value(
    tmp_path: Path, caplog: pytest.LogCaptureFixture, value: str
) -> None:
    message = _hidden_error(tmp_path, f"explainer: {value}\n", caplog, MARKER)

    assert "explainer block must be a mapping of settings" in message


@pytest.mark.parametrize("block", ["explainer:\n", "explainer: {}\n"], ids=["no-value", "empty"])
def test_an_empty_explainer_block_disables_the_explainer(tmp_path: Path, block: str) -> None:
    config = load_config(_write(tmp_path, _CONFIG_HEAD + block))

    assert config.explainer is None or not config.explainer.enabled
