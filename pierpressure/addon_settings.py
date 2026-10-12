"""The add-on's Configuration form combined with its ``config.yaml``.

Follows addon-form-horizon-file D1-D3 and D5, and ADR-0021.

Inside an add-on, the form lists the piers, and ``config.yaml`` adds the settings
the form leaves unset. :func:`combine_settings` builds one config-shaped mapping
from the two, so the core checks it exactly as it checks a file on its own.

A setting given in both is an error. These groups count as one setting each: a
pier's horizon, a pier's equipment, the broker connection, and the recompute
interval. Conflicts are found on the raw form values, before the translation
skips any pier, so a file entry for a skipped pier still matches it (D2).

Every problem goes into one :class:`ConfigError`, on one line. A problem names
settings by their ``config.yaml`` names and piers by their ids, escaped so a line
break cannot split the log line. It never holds a setting's value (D5).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pierpressure.addon_options import is_set, pier_settings, translate_form
from pierpressure.core.config import AppConfig, ConfigError

# The ``mqtt`` keys that make up the broker connection, one setting as a group.
CONNECTION_KEYS = ("host", "port", "username", "password")

_BOTH = "is set on the Configuration tab and in config.yaml"


@dataclass(frozen=True)
class CombinedSettings:
    """The combined config-shaped mapping, and whether the file added a setting (D8)."""

    raw: dict[str, Any]
    file_adds: bool


def combine_settings(options: dict[str, Any], file: dict[str, Any] | None) -> CombinedSettings:
    """Combine the raw saved form values with the mapping read from ``config.yaml``.

    ``file`` is ``None`` when there is no ``config.yaml``. Each form pier gets
    the settings of the file pier with the same ``id``; the form's piers keep
    their order, and the file cannot add a pier. The ``mqtt`` block and the top
    level get the file's other keys. Raises one :class:`ConfigError` that lists
    every problem: a setting given in both, a file pier the form does not list or
    lists twice, or a file whose ``piers`` or ``mqtt`` has the wrong shape.
    """
    translated = translate_form(options) or {"piers": []}
    file = file or {}
    problems: list[str] = []

    file_piers = _file_piers(file, problems)
    form_piers = [pier for pier in options.get("piers", []) if isinstance(pier, dict)]
    _check_piers(form_piers, file_piers, problems)
    _check_broker(translated.get("mqtt"), file.get("mqtt"), problems)
    if is_set(options.get("interval_seconds")) and _sets_interval(file.get("recompute")):
        problems.append(f"the recompute interval (recompute.interval_seconds) {_BOTH}")

    if problems:
        raise ConfigError(
            "The Configuration tab and config.yaml do not combine: " + "; ".join(problems)
        )

    combined = _merge(translated, file, file_piers)
    return CombinedSettings(raw=combined, file_adds=_known(combined) != _known(translated))


def file_pier_ids(file: dict[str, Any]) -> list[str]:
    """The text ids of the file's piers, once each, in the file's order (D6)."""
    return list(_file_piers(file, []))


def _file_piers(file: dict[str, Any], problems: list[str]) -> dict[str, dict[str, Any]]:
    """The file's piers by ``id``, after the structure check (D2).

    An entry that is not a mapping, or whose ``id`` is missing or not text, is
    reported by its position. Only entries with a text ``id`` are returned, so no
    other value is ever used as a key. A repeated ``id`` keeps its first entry.
    """
    if "piers" not in file:
        return {}
    raw_piers = file["piers"]
    if not isinstance(raw_piers, list):
        problems.append("piers in config.yaml must be a list")
        return {}

    by_id: dict[str, dict[str, Any]] = {}
    for position, entry in enumerate(raw_piers, start=1):
        where = f"entry {position} in the piers list of config.yaml"
        if not isinstance(entry, dict):
            problems.append(f"{where} is not a mapping of pier settings")
        elif not isinstance(entry.get("id"), str):
            problems.append(f"{where} has no id, or its id is not text")
        elif entry["id"] not in by_id:
            by_id[entry["id"]] = entry
        else:
            repeated = f"pier {entry['id']!r} is listed more than once in config.yaml"
            if repeated not in problems:
                problems.append(repeated)
    return by_id


def _check_piers(
    form_piers: list[dict[str, Any]],
    file_piers: dict[str, dict[str, Any]],
    problems: list[str],
) -> None:
    """Report file piers the form does not list, and pier settings given in both."""
    listed = {pier["id"] for pier in form_piers if isinstance(pier.get("id"), str)}
    for pier_id in file_piers:
        if pier_id not in listed:
            problems.append(f"pier {pier_id!r} in config.yaml is not on the Configuration tab")

    # A form that lists an id twice gets the file entry on both piers (D3), so
    # each is checked; the message is given once.
    for form_pier in form_piers:
        form_id = form_pier.get("id")
        if not isinstance(form_id, str) or form_id not in file_piers:
            continue
        both = pier_settings(form_pier) & pier_settings(file_piers[form_id])
        for setting in sorted(both, key=str):
            problem = f"{_name(setting)} of pier {form_id!r} {_BOTH}"
            if problem not in problems:
                problems.append(problem)


def _check_broker(form_mqtt: Any, file_mqtt: Any, problems: list[str]) -> None:
    """Report a broker connection or another ``mqtt`` key given in both (D3)."""
    if file_mqtt is None:
        return
    if not isinstance(file_mqtt, dict):
        problems.append("mqtt in config.yaml must be a mapping of settings, such as mqtt.host")
        return
    if not isinstance(form_mqtt, dict):
        return
    form_keys = {key for key, value in form_mqtt.items() if is_set(value)}
    file_keys = {key for key, value in file_mqtt.items() if is_set(value)}
    connection = set(CONNECTION_KEYS)
    if form_keys & connection and file_keys & connection:
        names = ", ".join(f"mqtt.{key}" for key in CONNECTION_KEYS)
        problems.append(f"the broker connection ({names}) {_BOTH}")
    for key in sorted((form_keys & file_keys) - connection, key=str):
        problems.append(f"mqtt.{_name(key)} {_BOTH}")


def _sets_interval(recompute: Any) -> bool:
    """Whether the file's ``recompute`` block sets anything; an empty block does not."""
    if isinstance(recompute, dict):
        return any(is_set(value) for value in recompute.values())
    return is_set(recompute)


def _known(mapping: dict[str, Any]) -> dict[str, Any]:
    """The top-level keys the core reads; it drops any other (D3)."""
    return {key: value for key, value in mapping.items() if key in AppConfig.model_fields}


def _merge(
    translated: dict[str, Any],
    file: dict[str, Any],
    file_piers: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """The plain union of the two sources, once no setting is given in both (D3).

    A file entry whose form pier the translation skipped is dropped, because that
    pier is not published.
    """
    combined = {key: value for key, value in translated.items() if key != "piers"}
    combined["piers"] = [_merge_pier(pier, file_piers) for pier in translated["piers"]]

    file_mqtt = file.get("mqtt")
    if isinstance(file_mqtt, dict):
        form_mqtt = translated.get("mqtt")
        if form_mqtt is None:
            form_mqtt = {}
        if isinstance(form_mqtt, dict):
            mqtt = {**form_mqtt, **_set_values(file_mqtt)}
            if mqtt:
                combined["mqtt"] = mqtt

    for key, value in file.items():
        if key in ("piers", "mqtt") or not is_set(value):
            continue
        if key == "recompute" and not _sets_interval(value):
            continue
        combined[key] = value
    return combined


def _merge_pier(pier: Any, file_piers: dict[str, dict[str, Any]]) -> Any:
    if not isinstance(pier, dict):
        return pier
    pier_id = pier.get("id")
    entry = file_piers.get(pier_id) if isinstance(pier_id, str) else None
    if entry is None:
        return pier
    added = {key: value for key, value in _set_values(entry).items() if key != "id"}
    return {**pier, **added}


def _set_values(mapping: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in mapping.items() if is_set(value)}


def _name(key: Any) -> str:
    """A key name for an error, with any line break or control character escaped."""
    if isinstance(key, str):
        return repr(key)[1:-1]
    return repr(key)
