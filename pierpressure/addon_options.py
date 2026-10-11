"""The add-on's Configuration form (addon-options-form D1, D3).

When the user saves the form, the Supervisor writes its values to
``/data/options.json``. :func:`read_addon_options` turns them into the mapping a
``config.yaml`` with the same settings would hold, so the core validates a form
pier exactly as it validates a file pier. The core never sees the form's names.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from pierpressure.core.config import ConfigError

OPTIONS_PATH = "/data/options.json"


def read_addon_options(path: str | os.PathLike[str] = OPTIONS_PATH) -> dict[str, Any] | None:
    """Read the saved form values at ``path`` as a config-shaped mapping.

    Returns ``None`` when the form lists no piers, or when the file is missing:
    the service then reads ``config.yaml`` (D3). Pier entries pass through
    unchanged, because the form's pier keys are the file's keys. Raises
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

    config: dict[str, Any] = {"piers": piers}
    if "interval_seconds" in options:
        config["recompute"] = {"interval_seconds": options["interval_seconds"]}
    return config
