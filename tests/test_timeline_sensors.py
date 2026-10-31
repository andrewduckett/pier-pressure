"""The timeline sensors (spec ha-delivery, ADR-0025; timeline-sensors design).

Every timeline variable is a sensor on the pier's device, built by one code path
from a table: its state is the current hour's value, and its attributes carry the
variable's whole forecast so a chart card can draw it. Cloud cover is the first
row, and ``tests/test_cloud_cover.py`` covers it on its own.
"""

from __future__ import annotations

import types
import typing
from typing import Annotated, get_args, get_origin, get_type_hints

import pytest

from pierpressure.core.model import TimelineEntry
from pierpressure.delivery.mqtt import TIMELINE_SENSORS, TimelineSensor

NEW_KEYS = (
    "cloud_low",
    "cloud_mid",
    "cloud_high",
    "wind_gust",
    "seeing",
    "transparency",
    "sun_altitude",
    "moon_altitude",
)


def _unwrap(hint: object) -> object:
    """``hint`` with any ``Annotated`` wrapper removed, inside a union too."""
    if get_origin(hint) is Annotated:
        return get_args(hint)[0]
    if isinstance(hint, types.UnionType) or get_origin(hint) is typing.Union:
        args = tuple(_unwrap(a) for a in get_args(hint))
        return typing.Union[args]  # noqa: UP007 - rebuilt from a runtime tuple
    return hint


# --------------------------------------------------------------------------- #
# The table
# --------------------------------------------------------------------------- #


def test_the_table_lists_cloud_cover_then_the_eight_new_keys() -> None:
    assert tuple(s.key for s in TIMELINE_SENSORS) == ("cloud_cover", *NEW_KEYS)


@pytest.mark.parametrize("sensor", TIMELINE_SENSORS, ids=lambda s: s.key)
def test_every_key_is_a_float_field_of_the_timeline_entry(sensor: TimelineSensor) -> None:
    hints = get_type_hints(TimelineEntry, include_extras=True)
    assert sensor.key in hints
    assert _unwrap(hints[sensor.key]) in (float, float | None)


@pytest.mark.parametrize("sensor", TIMELINE_SENSORS, ids=lambda s: s.key)
def test_every_name_slugs_to_its_key(sensor: TimelineSensor) -> None:
    assert sensor.name.lower().replace(" ", "_") == sensor.key


def test_names_units_and_icons_follow_the_design() -> None:
    assert [(s.key, s.name, s.unit, s.icon) for s in TIMELINE_SENSORS] == [
        ("cloud_cover", "Cloud cover", "%", "mdi:weather-cloudy"),
        ("cloud_low", "Cloud low", "%", "mdi:weather-cloudy"),
        ("cloud_mid", "Cloud mid", "%", "mdi:weather-cloudy"),
        ("cloud_high", "Cloud high", "%", "mdi:weather-cloudy"),
        ("wind_gust", "Wind gust", "km/h", "mdi:weather-windy"),
        ("seeing", "Seeing", None, "mdi:eye"),
        ("transparency", "Transparency", None, "mdi:telescope"),
        ("sun_altitude", "Sun altitude", "°", "mdi:weather-sunny"),
        ("moon_altitude", "Moon altitude", "°", "mdi:weather-night"),
    ]
