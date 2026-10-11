"""The add-on's Configuration form (addon-options-form D1, D3; addon-form-horizon D1-D3).

When the user saves the form, the Supervisor writes its values to
``/data/options.json``. :func:`read_addon_options` turns them into the mapping a
``config.yaml`` with the same settings would hold, so the core validates a form
pier exactly as it validates a file pier. The core never sees the form's names:
a pier's flat ``min_altitude`` and ``horizon_points`` fields become the file's
``horizon`` block.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

import yaml

from pierpressure.core.config import ConfigError

logger = logging.getLogger(__name__)

OPTIONS_PATH = "/data/options.json"


def read_addon_options(path: str | os.PathLike[str] = OPTIONS_PATH) -> dict[str, Any] | None:
    """Read the saved form values at ``path`` as a config-shaped mapping.

    Returns ``None`` when the form lists no piers, or when the file is missing:
    the service then reads ``config.yaml`` (D3). Each pier's horizon fields
    become its ``horizon`` block; its other keys pass through unchanged, because
    they are the file's keys. A pier whose ``horizon_points`` cannot be parsed is
    logged and left out, so the list may end up empty. Raises
    :class:`ConfigError`, naming the file, when it is not valid JSON, its root is
    not a mapping, or its ``piers`` is not a list.
    """
    options_path = Path(path)
    try:
        text = options_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    try:
        options = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ConfigError(f"{options_path} is not valid JSON: {exc}") from exc
    if not isinstance(options, dict):
        raise ConfigError(f"{options_path} must hold a mapping of settings")

    piers = options.get("piers", [])
    if not isinstance(piers, list):
        raise ConfigError(f"{options_path}: piers must be a list")
    if not piers:
        return None

    config: dict[str, Any] = {"piers": _config_piers(piers)}
    if "interval_seconds" in options:
        config["recompute"] = {"interval_seconds": options["interval_seconds"]}
    return config


def _config_piers(piers: list[Any]) -> list[Any]:
    """Rebuild each form pier's horizon, leaving out piers whose points cannot be read."""
    rebuilt: list[Any] = []
    for pier in piers:
        if not isinstance(pier, dict):
            # The core's per-pier check skips it (addon-form-horizon D3).
            rebuilt.append(pier)
            continue
        try:
            rebuilt.append(_with_horizon_block(pier))
        except ValueError as exc:
            # The core's skip wording, so both read alike in the log (D2).
            logger.error("Skipping invalid pier %r: %s", pier.get("id"), exc)
    return rebuilt


def _with_horizon_block(pier: dict[str, Any]) -> dict[str, Any]:
    """Move ``min_altitude`` and ``horizon_points`` into a ``horizon`` block (D1).

    When both are set, the block holds both, and the core's "exactly one source"
    rule rejects the pier. Raises :class:`ValueError` when ``horizon_points`` is
    not text or not valid YAML.
    """
    rebuilt = {
        key: value for key, value in pier.items() if key not in ("min_altitude", "horizon_points")
    }
    horizon: dict[str, Any] = {}
    if pier.get("min_altitude") is not None:
        horizon["min_altitude"] = pier["min_altitude"]
    points_text = pier.get("horizon_points")
    if points_text is not None:
        if not isinstance(points_text, str):
            raise ValueError("horizon_points must be text")
        if points_text.strip():
            try:
                horizon["points"] = yaml.safe_load(points_text)
            except yaml.YAMLError as exc:
                raise ValueError(f"horizon_points is not valid YAML: {exc}") from exc
    if horizon:
        rebuilt["horizon"] = horizon
    return rebuilt
