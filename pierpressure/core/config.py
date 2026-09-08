"""Configuration loading and validation (design D8).

Config is YAML. ``piers`` is a list (even though M1 runs with one) so the
delivery's per-pier operation and later multi-pier milestones need no config
reshape. Broker secrets support a ``${ENV}`` override so they need not sit in
plaintext.

Per-pier validation is isolated (spec night-verdict): each pier is validated
independently; an invalid pier is logged and skipped while valid piers continue.
Zero valid piers is a hard failure (:class:`ConfigError`) so the process exits
non-zero rather than running with nothing to publish.
"""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

logger = logging.getLogger(__name__)

_ENV_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")


class ConfigError(Exception):
    """A configuration is missing required fields, malformed, or has no valid pier."""


class MqttConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    host: str
    port: int = 1883
    username: str | None = None
    password: str | None = None
    discovery_prefix: str = "homeassistant"
    base_topic: str = "pierpressure"


class RecomputeConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    interval_seconds: int = Field(gt=0)


class PierConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)
    elevation_m: float


class AppConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mqtt: MqttConfig
    recompute: RecomputeConfig
    piers: list[PierConfig]


def _expand_env(value: Any) -> Any:
    """Recursively expand ``${VAR}`` in string values from the environment.

    An unset variable is left as its literal ``${VAR}`` placeholder rather than
    silently blanked, so a missing secret is visible instead of becoming "".
    """
    if isinstance(value, str):
        return _ENV_PATTERN.sub(lambda m: os.environ.get(m.group(1), m.group(0)), value)
    if isinstance(value, dict):
        return {k: _expand_env(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_expand_env(v) for v in value]
    return value


def load_config(path: str | os.PathLike[str]) -> AppConfig:
    """Load and validate the YAML config at ``path``.

    Raises :class:`ConfigError` if the file is missing/malformed, if ``mqtt`` or
    ``recompute`` are invalid, or if no valid pier remains after per-pier
    validation.
    """
    text = Path(path).read_text(encoding="utf-8")
    raw = yaml.safe_load(text)
    if not isinstance(raw, dict):
        raise ConfigError("Configuration root must be a mapping")
    raw = _expand_env(raw)

    try:
        mqtt = MqttConfig.model_validate(raw.get("mqtt"))
        recompute = RecomputeConfig.model_validate(raw.get("recompute"))
    except ValidationError as exc:
        raise ConfigError(f"Invalid mqtt/recompute configuration: {exc}") from exc

    raw_piers = raw.get("piers")
    if not isinstance(raw_piers, list):
        raise ConfigError("Configuration must contain a 'piers' list")

    piers = validate_piers(raw_piers)
    if not piers:
        raise ConfigError("No valid pier in configuration; nothing to publish")

    return AppConfig(mqtt=mqtt, recompute=recompute, piers=piers)


def validate_piers(raw_piers: list[Any]) -> list[PierConfig]:
    """Validate each pier independently; log and skip invalid ones.

    Returns the list of valid piers (possibly empty). This is the per-pier
    validation isolation from the spec: one bad entry never disables the rest.
    """
    valid: list[PierConfig] = []
    for raw_pier in raw_piers:
        try:
            valid.append(PierConfig.model_validate(raw_pier))
        except ValidationError as exc:
            pier_id = raw_pier.get("id") if isinstance(raw_pier, dict) else None
            logger.error("Skipping invalid pier %r: %s", pier_id, exc)
    return valid
