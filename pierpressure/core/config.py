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
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    PrivateAttr,
    ValidationError,
    ValidationInfo,
    model_validator,
)

from .horizon import Horizon, flat, from_points, open_sky, parse_horizon_text

logger = logging.getLogger(__name__)

_ENV_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")

# The system-wide go-threshold applied when a pier omits its own (design D8, and
# the tuning value locked in task 5.1). A gate-passing night scores GO at or
# above this and MAYBE below it. Chosen so a clearly good night (mostly clear,
# little moon) reads GO while a middling one reads MAYBE.
DEFAULT_GO_THRESHOLD = 65


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


class HorizonConfig(BaseModel):
    """A pier's declared horizon source: exactly one of three inputs (design D3).

    ``points`` is an inline ``[[az, alt], ...]`` list; ``min_altitude`` is a flat
    floor; ``file``/``format`` reference an exported horizon. The mutual-exclusivity
    and range rules are enforced when :class:`PierConfig` resolves the block to a
    canonical :class:`~pierpressure.core.horizon.Horizon`.
    """

    model_config = ConfigDict(extra="forbid")

    points: list[tuple[float, float]] | None = None
    min_altitude: float | None = None
    file: str | None = None
    format: str | None = None


def _resolve_horizon(spec: HorizonConfig | None, base_dir: Path | None) -> Horizon:
    """Build the canonical horizon for a pier from its declared source (design D3).

    Absent -> flat 0 open sky. Otherwise exactly one of ``points``, ``min_altitude``,
    or a ``file`` reference may be set; more than one — or a bad range, a malformed
    file, or an unsupported format — raises :class:`ValueError`, which the per-pier
    validation turns into the log-and-skip isolation (design D5). A relative file
    path resolves against ``base_dir`` (the config file's directory), not the
    process working directory.
    """
    if spec is None:
        return open_sky()

    sources = {
        "points": spec.points is not None,
        "min_altitude": spec.min_altitude is not None,
        "file": spec.file is not None,
    }
    chosen = [name for name, present in sources.items() if present]
    if len(chosen) != 1:
        raise ValueError(
            "a horizon must configure exactly one source "
            "(points, min_altitude, or file), got: " + (", ".join(chosen) or "none")
        )

    if spec.points is not None:
        return from_points(spec.points)
    if spec.min_altitude is not None:
        return flat(spec.min_altitude)

    assert spec.file is not None
    if spec.format is None:
        raise ValueError("a horizon file reference requires a 'format'")
    path = Path(spec.file)
    if not path.is_absolute():
        base = base_dir if base_dir is not None else Path.cwd()
        path = base / path
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"cannot read horizon file {spec.file!r}: {exc}") from exc
    return parse_horizon_text(spec.format, text)


class PierConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)
    elevation_m: float
    # The only two tuning knobs (design D8). ``go_threshold`` defaults to the
    # global value when omitted. ``max_gust`` is opt-in: when omitted the wind
    # gate is disabled and no forecast gust can cause a NO-GO. Its unit is the
    # forecast gust unit the provider layer supplies (km/h).
    go_threshold: int = Field(default=DEFAULT_GO_THRESHOLD, ge=0, le=100)
    max_gust: float | None = Field(default=None, gt=0.0)
    # The declared horizon source (design D3). Absent -> flat 0 open sky. It is
    # resolved to canonical samples during validation and exposed as
    # ``horizon_mask``; the raw block is not consumed by the verdict path.
    horizon: HorizonConfig | None = None

    _horizon_mask: Horizon = PrivateAttr()

    @property
    def horizon_mask(self) -> Horizon:
        """The resolved canonical horizon for this pier (open sky when unset)."""
        return self._horizon_mask

    @model_validator(mode="after")
    def _resolve_horizon_mask(self, info: ValidationInfo) -> PierConfig:
        base_dir = None
        if info.context is not None:
            base_dir = info.context.get("base_dir")
        self._horizon_mask = _resolve_horizon(self.horizon, base_dir)
        return self


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
    config_path = Path(path)
    text = config_path.read_text(encoding="utf-8")
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

    # The config file's own directory anchors relative horizon file references, so
    # a horizon file placed beside config.yaml is found regardless of the process
    # working directory (design D3).
    base_dir = config_path.resolve().parent
    piers = validate_piers(raw_piers, base_dir)
    if not piers:
        raise ConfigError("No valid pier in configuration; nothing to publish")

    # Assembling ``AppConfig`` re-runs each pier's after-validator, which re-reads
    # any horizon file, so the same ``base_dir`` context is threaded through here —
    # otherwise a relative horizon path would re-resolve against the process cwd.
    return AppConfig.model_validate(
        {"mqtt": mqtt, "recompute": recompute, "piers": piers},
        context={"base_dir": base_dir},
    )


def validate_piers(raw_piers: list[Any], base_dir: Path | None = None) -> list[PierConfig]:
    """Validate each pier independently; log and skip invalid ones.

    Returns the list of valid piers (possibly empty). This is the per-pier
    validation isolation from the spec: one bad entry — including an invalid or
    unreadable horizon — never disables the rest. ``base_dir`` is passed as
    Pydantic validation context so a relative horizon file path resolves against
    the config file's directory (design D3).
    """
    context = {"base_dir": base_dir}
    valid: list[PierConfig] = []
    for raw_pier in raw_piers:
        try:
            valid.append(PierConfig.model_validate(raw_pier, context=context))
        except ValidationError as exc:
            pier_id = raw_pier.get("id") if isinstance(raw_pier, dict) else None
            logger.error("Skipping invalid pier %r: %s", pier_id, exc)
    return valid
