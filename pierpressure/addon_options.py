"""The add-on's Configuration form.

Follows addon-options-form D1, D3; addon-form-horizon D1-D3;
addon-form-equipment D1-D3; addon-form-broker D2; and addon-form-gates D1.

When the user saves the form, the Supervisor writes its values to
``/data/options.json``. :func:`translate_form` turns them into the mapping a
``config.yaml`` with the same settings would hold, so the core validates a form
pier exactly as it validates a file pier. The core never sees the form's names:
a pier's flat ``min_altitude`` and ``horizon_points`` fields become the file's
``horizon`` block, and its ``equipment_*`` fields become its ``equipment`` block.
Its ``go_threshold`` and ``max_gust`` keep the file's names. Each passes through
when set and is left out when not, so the core's default applies.
The form's ``mqtt`` block already uses the file's names, so it passes through
without the fields the user left empty.

One rule decides whether a form value is set: :func:`is_set`. The translation
uses it, and so does :func:`pier_settings`, which names the settings a raw form
pier sets so the add-on can find a setting given in both the form and
``config.yaml`` (addon-form-horizon-file D2).
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

from pierpressure.core.config import SKIP_PIER_MESSAGE, ConfigError

logger = logging.getLogger(__name__)

OPTIONS_PATH = "/data/options.json"

# The form fields that become the pier's ``horizon`` block.
HORIZON_FIELDS = ("min_altitude", "horizon_points")

# Each form field and the key it becomes in the pier's ``equipment`` block.
EQUIPMENT_FIELDS = {
    "equipment_focal_length_mm": "focal_length_mm",
    "equipment_sensor_width_mm": "sensor_width_mm",
    "equipment_sensor_height_mm": "sensor_height_mm",
    "equipment_reducer": "reducer",
}

# The flat pier fields that are left out when not set, so the core's default
# applies instead of a null (addon-form-gates D1).
GATE_FIELDS = ("go_threshold", "max_gust")


def is_set(value: Any) -> bool:
    """Whether a saved form value is set: not ``None``, and not empty or blank text.

    A value of 0 is set (addon-form-horizon-file D2).
    """
    return value is not None and not (isinstance(value, str) and not value.strip())


def pier_settings(pier: dict[str, Any]) -> set[str]:
    """The settings a raw form pier sets, by their ``config.yaml`` names (D2).

    The horizon fields name ``horizon``, and the equipment fields or an
    ``equipment`` value name ``equipment``. ``id`` names nothing, because it only
    matches a form pier to its ``config.yaml`` entry. Any other key names itself.
    A value that is not set names nothing.
    """
    settings: set[str] = set()
    for key, value in pier.items():
        if key == "id" or not is_set(value):
            continue
        if key in HORIZON_FIELDS:
            settings.add("horizon")
        elif key in EQUIPMENT_FIELDS:
            settings.add("equipment")
        else:
            settings.add(key)
    return settings


def read_form_values(path: str | os.PathLike[str] = OPTIONS_PATH) -> dict[str, Any] | None:
    """Read the raw saved form values at ``path``, or ``None`` when the file is missing.

    Raises :class:`ConfigError`, naming the file, when it is not valid JSON, its
    root is not a mapping, or its ``piers`` is not a list.
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
    if not isinstance(options.get("piers", []), list):
        raise ConfigError(f"{options_path}: piers must be a list")
    return options


def translate_form(options: dict[str, Any]) -> dict[str, Any] | None:
    """Turn raw saved form values into a config-shaped mapping.

    Returns ``None`` when the form lists no piers. Each pier's horizon fields
    become its ``horizon`` block, and its equipment fields its ``equipment``
    block. Its gate fields, ``go_threshold`` and ``max_gust``, are left out when
    not set (addon-form-gates D1). Its other keys pass through unchanged, because
    they are the file's keys. The ``mqtt`` block passes through without its empty
    fields, and is left out when none is set (addon-form-broker D2). A pier whose
    ``horizon_points`` cannot be parsed, or that holds both an ``equipment`` block
    and equipment fields, is logged and left out, so the list may end up empty.
    """
    piers = options.get("piers", [])
    if not piers:
        return None

    config: dict[str, Any] = {"piers": _config_piers(piers)}
    if "interval_seconds" in options:
        config["recompute"] = {"interval_seconds": options["interval_seconds"]}
    mqtt = _set_broker_fields(options.get("mqtt"))
    if mqtt is not None and mqtt != {}:
        config["mqtt"] = mqtt
    return config


def _set_broker_fields(mqtt: Any) -> Any:
    """The form's ``mqtt`` block without the fields left empty (addon-form-broker D2).

    A field that is ``None``, empty text or blank text is unset, so a cleared
    username neither sets an empty login nor counts as a username without a host.
    A value that is not a mapping passes through, and the core rejects it.
    """
    if not isinstance(mqtt, dict):
        return mqtt
    return {key: value for key, value in mqtt.items() if is_set(value)}


def _config_piers(piers: list[Any]) -> list[Any]:
    """Rebuild each form pier's horizon and equipment, and drop its unset gate fields.

    Leaves out the piers that cannot be rebuilt.
    """
    rebuilt: list[Any] = []
    for pier in piers:
        if not isinstance(pier, dict):
            # The core's per-pier check skips it (addon-form-horizon D3).
            rebuilt.append(pier)
            continue
        try:
            rebuilt.append(_with_equipment_block(_with_horizon_block(_without_unset_gates(pier))))
        except ValueError as exc:
            # The core's skip wording, so both read alike in the log (D2).
            logger.error(SKIP_PIER_MESSAGE, pier.get("id"), exc)
    return rebuilt


def _without_unset_gates(pier: dict[str, Any]) -> dict[str, Any]:
    """The pier without the gate fields that :func:`is_set` counts as unset (addon-form-gates D1).

    A set value, even 0 or one the core will reject, passes through unchanged.
    """
    return {key: value for key, value in pier.items() if key not in GATE_FIELDS or is_set(value)}


def _with_horizon_block(pier: dict[str, Any]) -> dict[str, Any]:
    """Rename ``min_altitude`` and ``horizon_points`` into a ``horizon`` block (D1).

    A field that :func:`is_set` counts as unset is left out, so blank text in
    ``min_altitude`` gives no block (addon-form-horizon-file D2). A set field's
    value passes through unchanged, whatever its type: the core parses and checks
    it (addon-options-core-validates D2). When both are set, the block holds both,
    and the core's "exactly one source" rule rejects the pier. When the pier also
    holds a set ``horizon`` value, the set fields stay where they are, and the
    core rejects each one by name.
    """
    rebuilt = {
        key: value for key, value in pier.items() if key not in HORIZON_FIELDS or is_set(value)
    }
    if is_set(pier.get("horizon")):
        return rebuilt
    horizon: dict[str, Any] = {}
    if "min_altitude" in rebuilt:
        horizon["min_altitude"] = rebuilt.pop("min_altitude")
    if "horizon_points" in rebuilt:
        horizon["points"] = rebuilt.pop("horizon_points")
    if horizon:
        rebuilt["horizon"] = horizon
    return rebuilt


def _with_equipment_block(pier: dict[str, Any]) -> dict[str, Any]:
    """Move the set ``equipment_*`` fields into an ``equipment`` block (addon-form-equipment D1).

    A field that :func:`is_set` counts as unset is left out: absent, ``None``,
    or empty or blank text (D3, addon-form-horizon-file D2). The block holds only the
    fields that are set; the core rejects an incomplete one (D2). Raises
    :class:`ValueError` when the pier also holds an ``equipment`` value, rather
    than merging the two.
    """
    rebuilt = {key: value for key, value in pier.items() if key not in EQUIPMENT_FIELDS}
    equipment = {
        key: pier[field] for field, key in EQUIPMENT_FIELDS.items() if is_set(pier.get(field))
    }
    if equipment:
        if pier.get("equipment") is not None:
            raise ValueError("equipment and the equipment_* fields cannot both be set")
        rebuilt["equipment"] = equipment
    return rebuilt
