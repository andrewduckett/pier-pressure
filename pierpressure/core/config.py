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
import math
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    PrivateAttr,
    SecretStr,
    ValidationError,
    ValidationInfo,
    field_validator,
    model_validator,
)

from .horizon import Horizon, flat, from_points, open_sky, parse_horizon_text

logger = logging.getLogger(__name__)

# The log line for a skipped pier, from any interface. The add-on's docs tell users
# to search the log for it (addon-form-horizon D2).
SKIP_PIER_MESSAGE = "Skipping invalid pier %r: %s"

_ENV_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")

# The system-wide go-threshold applied when a pier omits its own (design D8, and
# the tuning value locked in task 5.1). A gate-passing night scores GO at or
# above this and MAYBE below it. Chosen so a clearly good night (mostly clear,
# little moon) reads GO while a middling one reads MAYBE.
DEFAULT_GO_THRESHOLD = 65


class ConfigError(Exception):
    """A configuration is missing required fields, malformed, or has no valid pier."""


class MqttConfig(BaseModel):
    # This block holds the broker password, so its errors never show their input
    # (config-secrets-hidden-in-errors D1). Its checks must not quote their input:
    # build_config writes this block's errors from their messages.
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    host: str
    port: int = 1883
    username: str | None = None
    # Masked when printed; read only to log in to the broker (D4).
    password: SecretStr | None = None
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

    ``points`` may also be YAML text holding that list, such as the add-on form's
    ``horizon_points`` (addon-options-core-validates D1). The text is parsed here,
    so a bad value gets an error located at ``horizon.points`` whatever the
    interface.
    """

    model_config = ConfigDict(extra="forbid")

    points: list[tuple[float, float]] | None = None
    min_altitude: float | None = None
    file: str | None = None
    format: str | None = None

    @field_validator("points", mode="before")
    @classmethod
    def _parse_points_text(cls, value: Any) -> Any:
        """Parse text in ``points`` as YAML; pass any other value through (D1).

        Text that holds nothing, such as blank text or only a comment, parses to
        ``None``. It is rejected rather than read as "no points", so a typo never
        silently gives the pier another horizon source or open sky.
        """
        if not isinstance(value, str):
            return value
        try:
            points = yaml.safe_load(value)
        except yaml.YAMLError as exc:
            # The reader's message spans several lines; keep it to one.
            message = " ".join(str(exc).split())
            raise ValueError(f"is not valid YAML: {message}") from exc
        if points is None:
            raise ValueError("text holds no list of points")
        return points


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


class Equipment(BaseModel):
    """A pier's imaging equipment: raw optics, not a pre-computed field of view (design D1).

    A telescope focal length and a camera sensor's width and height (millimetres),
    with an optional focal ``reducer``/barlow factor. Each is strictly positive
    (``Field(gt=0.0)``, the ``max_gust`` precedent), so a non-positive value is a
    configuration error rather than a runtime crash — the effective focal length
    and the derived short-edge field of view are therefore never zero, and the
    ranking's ``r = size / fov_short`` never divides by zero (design D2).
    """

    model_config = ConfigDict(extra="forbid")

    focal_length_mm: float = Field(gt=0.0)
    sensor_width_mm: float = Field(gt=0.0)
    sensor_height_mm: float = Field(gt=0.0)
    reducer: float = Field(default=1.0, gt=0.0)

    def field_of_view_deg(self) -> tuple[float, float]:
        """The equipment's field of view as ``(width, height)`` angles in degrees (design D2).

        The reducer/barlow scales the focal length first —
        ``f_eff = focal_length_mm * reducer`` — so a reducer below 1.0 widens the
        field and a barlow above 1.0 narrows it. Each axis is
        ``2·atan(sensor_axis / (2·f_eff))``. Pure and offline: the same equipment always
        yields the same field of view, so ranking stays deterministic.
        """
        f_eff = self.focal_length_mm * self.reducer
        width = math.degrees(2.0 * math.atan(self.sensor_width_mm / (2.0 * f_eff)))
        height = math.degrees(2.0 * math.atan(self.sensor_height_mm / (2.0 * f_eff)))
        return width, height

    @property
    def fov_short_deg(self) -> float:
        """The short edge of the field of view (degrees) — the true "does it fit" axis.

        An object wider than the short edge is cropped at any rotation, so the
        short edge, not the diagonal, is the framing reference (design D3).
        """
        width, height = self.field_of_view_deg()
        return min(width, height)


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
    # The optional imaging equipment (design D1). Absent -> the field-of-view ranking
    # term does not contribute; the pier still ranks on placement and brightness.
    equipment: Equipment | None = None

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


class ExplainerConfig(BaseModel):
    """The optional LLM explainer edge, disabled by default (design D7).

    The explainer turns a finished verdict into short prose delivered as a separate
    Home Assistant entity; it never feeds the astronomy or scoring math (ADR-0011).
    ``enabled`` gates both the provider and the narrative entity: an absent block or
    ``enabled: false`` leaves the default (no provider constructed, no entity).

    ``model`` is a Pydantic AI model spec (``"provider:model-name"``, e.g.
    ``"anthropic:claude-opus-5"``, ``"openai:gpt-4o"``), so the LLM provider is chosen
    by configuration rather than hard-coded. The optional ``api_key`` supports the same
    ``${ENV}`` expansion as the broker credentials, so the secret need not sit in
    plaintext; a missing key leaves a visible ``${VAR}`` placeholder (never logged) and
    the explainer degrades to no-narrative rather than erroring. When ``api_key`` is
    omitted, credentials are read from the provider's standard environment variable.
    """

    # This block holds the API key, so its errors never show their input
    # (config-secrets-hidden-in-errors D1). Its checks must not quote their input:
    # build_config writes this block's errors from their messages.
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    enabled: bool = False
    model: str = "anthropic:claude-opus-5"
    # Masked when printed; read only to call the LLM provider (D4).
    api_key: SecretStr | None = None


class AppConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mqtt: MqttConfig
    recompute: RecomputeConfig
    piers: list[PierConfig]
    # The optional explainer edge (design D7). Absent -> disabled: no provider is
    # constructed and no narrative entity is published.
    explainer: ExplainerConfig | None = None


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


@dataclass(frozen=True)
class BrokerSettings:
    """A broker's connection settings from outside the config file (ha-addon-mqtt-service D2).

    Plain data: the edge looks these up (the Home Assistant Supervisor's ``mqtt``
    service) and hands them in, so the core never triggers network access.
    """

    host: str
    port: int
    username: str | None = None
    password: str | None = field(default=None, repr=False)


# The ``mqtt`` keys that make up the broker connection. They come from one source
# as a group: the file when it names a host, otherwise the supplied broker.
_CREDENTIAL_KEYS = ("port", "username", "password")
_CONNECTION_KEYS = ("host", *_CREDENTIAL_KEYS)


@dataclass(frozen=True)
class ConfigFile:
    """A config file read and ``${VAR}``-expanded, but not yet validated (D2).

    ``base_dir`` is the folder that holds the file, which anchors relative horizon
    file references. The add-on's form builds one too, in the file's shape.

    Construction enforces the broker connection rule for every source of settings
    (addon-form-broker D3). It raises :class:`ConfigError` if the ``mqtt`` or
    ``explainer`` block is not a mapping, or if ``mqtt`` sets ``port``,
    ``username`` or ``password`` without ``host`` — the connection settings come
    from one source, so a partial set would be silently ignored otherwise. These
    errors hold no value from the block, which can be a secret
    (config-secrets-hidden-in-errors D3).
    """

    # Not printed: it holds the settings as read, secrets included (D4).
    raw: dict[str, Any] = field(repr=False)
    base_dir: Path

    def __post_init__(self) -> None:
        mqtt = self.raw.get("mqtt")
        if mqtt is not None and not isinstance(mqtt, dict):
            raise ConfigError("The mqtt block must be a mapping of settings, such as mqtt.host")
        explainer = self.raw.get("explainer")
        if explainer is not None and not isinstance(explainer, dict):
            raise ConfigError(
                "The explainer block must be a mapping of settings, such as explainer.enabled"
            )
        if mqtt is not None and not self.names_broker_host:
            partial = [f"mqtt.{key}" for key in _CREDENTIAL_KEYS if mqtt.get(key) is not None]
            if partial:
                raise ConfigError(
                    f"{', '.join(partial)} is set without mqtt.host; set mqtt.host too, "
                    "or leave out all of the broker connection settings"
                )

    @property
    def names_broker_host(self) -> bool:
        """Whether the file's ``mqtt`` block sets a broker ``host`` (blank is unset)."""
        mqtt = self.raw.get("mqtt")
        return isinstance(mqtt, dict) and mqtt.get("host") not in (None, "")


def read_config_mapping(path: str | os.PathLike[str]) -> dict[str, Any]:
    """Read the YAML config at ``path`` as a ``${VAR}``-expanded mapping.

    Follows addon-form-horizon-file D4. Reads only the file and the environment,
    and checks no setting: the add-on combines this mapping with its form before
    the broker rule runs. Raises :class:`ConfigError`, naming the file, if the
    file is not valid YAML or its root is not a mapping. A YAML error names only
    the file, lines and columns. It holds no text from the parser, which can
    quote the file, such as a broker password on the broken line.
    """
    config_path = Path(path)
    text = config_path.read_text(encoding="utf-8")
    try:
        raw = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ConfigError(_yaml_error_message(config_path, exc)) from None
    if not isinstance(raw, dict):
        raise ConfigError(f"Configuration root must be a mapping in {config_path}")
    expanded: dict[str, Any] = _expand_env(raw)
    return expanded


def _yaml_error_message(path: Path, exc: yaml.YAMLError) -> str:
    """Where the YAML mistake is, without any of the file's text.

    Names the problem mark first. When the parser also gives a context mark on
    another line, such as the ``[`` an unclosed list starts with, it is named as
    where the broken part starts.
    """
    if not isinstance(exc, yaml.MarkedYAMLError) or exc.problem_mark is None:
        return f"{path} is not valid YAML"
    problem, context = exc.problem_mark, exc.context_mark
    message = f"{path} is not valid YAML at {_place(problem)}"
    if context is not None and context.line != problem.line:
        message += f", in the part that starts at {_place(context)}"
    return message


def _place(mark: yaml.Mark) -> str:
    return f"line {mark.line + 1}, column {mark.column + 1}"


def read_config(path: str | os.PathLike[str]) -> ConfigFile:
    """Read the YAML config at ``path`` and expand ``${VAR}`` (design D2, step 1).

    Reads only the file and the environment, through :func:`read_config_mapping`.
    Raises :class:`ConfigError` as that function does, or if the file's ``mqtt``
    block breaks the broker connection rule that :class:`ConfigFile` enforces.
    """
    config_path = Path(path)
    return ConfigFile(raw=read_config_mapping(config_path), base_dir=config_path.resolve().parent)


def load_config(path: str | os.PathLike[str]) -> AppConfig:
    """Load and validate the YAML config at ``path``.

    Raises :class:`ConfigError` if the file is missing/malformed, if ``mqtt``,
    ``recompute`` or ``explainer`` are invalid, or if no valid pier remains after
    per-pier validation. An ``mqtt`` or ``explainer`` error holds none of the
    block's text (config-secrets-hidden-in-errors D1).
    """
    return build_config(read_config(path))


def build_config(read: ConfigFile, broker: BrokerSettings | None = None) -> AppConfig:
    """Validate a read config file into :class:`AppConfig` (design D2, step 2).

    When the file names no ``mqtt.host`` and ``broker`` is given, the broker
    supplies the host, port, username and password; ``discovery_prefix`` and
    ``base_topic`` still come from the file or their defaults. When the file names
    a host, ``broker`` is ignored. Raises :class:`ConfigError` as
    :func:`load_config` describes.
    """
    raw = read.raw
    raw_mqtt = raw.get("mqtt")
    if broker is not None and not read.names_broker_host:
        topics = raw_mqtt if isinstance(raw_mqtt, dict) else {}
        raw_mqtt = {
            **{k: v for k, v in topics.items() if k not in _CONNECTION_KEYS},
            "host": broker.host,
            "port": broker.port,
            "username": broker.username,
            "password": broker.password,
        }

    try:
        mqtt = MqttConfig.model_validate(raw_mqtt)
    except ValidationError as exc:
        # ``from None``, so a printed traceback cannot show the block's text either.
        raise _block_error("mqtt", MqttConfig, raw_mqtt, exc) from None
    try:
        recompute = RecomputeConfig.model_validate(raw.get("recompute"))
    except ValidationError as exc:
        raise ConfigError(f"Invalid mqtt/recompute configuration: {exc}") from exc

    raw_piers = raw.get("piers")
    if not isinstance(raw_piers, list):
        raise ConfigError("Configuration must contain a 'piers' list")

    # The config file's own directory anchors relative horizon file references, so
    # a horizon file placed beside config.yaml is found regardless of the process
    # working directory (design D3).
    base_dir = read.base_dir
    piers = validate_piers(raw_piers, base_dir)
    if not piers:
        raise ConfigError("No valid pier in configuration; nothing to publish")

    # Assembling ``AppConfig`` re-runs each pier's after-validator, which re-reads
    # any horizon file, so the same ``base_dir`` context is threaded through here —
    # otherwise a relative horizon path would re-resolve against the process cwd.
    # ``explainer`` is optional (absent or empty -> disabled). It is validated here,
    # on its own, so its error shows none of its text; ``AppConfig`` does not
    # validate the built model again (config-secrets-hidden-in-errors D2).
    assembled: dict[str, Any] = {"mqtt": mqtt, "recompute": recompute, "piers": piers}
    raw_explainer = raw.get("explainer")
    if raw_explainer is not None:
        try:
            assembled["explainer"] = ExplainerConfig.model_validate(raw_explainer)
        except ValidationError as exc:
            raise _block_error("explainer", ExplainerConfig, raw_explainer, exc) from None
    try:
        # This re-runs each pier's after-validator (a horizon file may be re-read),
        # so keep the label neutral rather than blaming one section.
        return AppConfig.model_validate(assembled, context={"base_dir": base_dir})
    except ValidationError as exc:
        raise ConfigError(f"Invalid configuration: {exc}") from exc


def _block_error(
    block: str, model: type[BaseModel], value: Any, exc: ValidationError
) -> ConfigError:
    """An error about a block that holds a secret, with none of the block's text (D1).

    Built from each error's location and message, never from the error's text,
    which quotes the input. A defined setting is named with the rule it broke. A
    key the block does not define is not named, because a user can type a secret
    where a key name belongs; the error lists the block's settings instead.
    """
    problems: list[str] = []
    unknown = False
    for error in exc.errors(include_url=False, include_input=False):
        location = error["loc"]
        if not location and value is None:
            problems.append(f"the {block} block is missing")
        elif not location:
            problems.append(f"{block} must be a mapping of settings")
        elif location[0] in model.model_fields:
            problems.append(f"{block}.{location[0]}: {error['msg']}")
        else:
            unknown = True
    if unknown:
        settings = ", ".join(model.model_fields)
        problems.append(
            f"the {block} block holds a setting it does not know; its settings are {settings}"
        )
    return ConfigError(f"Invalid {block} configuration: " + "; ".join(problems))


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
            logger.error(SKIP_PIER_MESSAGE, pier_id, exc)
    return valid
