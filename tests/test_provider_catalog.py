"""The provider declarations in the core (provider-order design D2)."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from typing import get_args

import pytest

from pierpressure.core.conditions import Variable
from pierpressure.core.model import TimelineEntry
from pierpressure.core.providers import CATALOG, OPEN_METEO, SEVEN_TIMER, ProviderSpec

_CLOUD_BUNDLE = frozenset({"cloud_cover", "cloud_low", "cloud_mid", "cloud_high"})


def test_variables_are_the_timeline_keys_without_time_and_altitudes() -> None:
    computed = {"time", "sun_altitude", "moon_altitude"}
    expected = tuple(name for name in TimelineEntry.model_fields if name not in computed)
    assert get_args(Variable) == expected


def test_open_meteo_declares_the_cloud_bundle_and_the_weather_variables() -> None:
    assert OPEN_METEO.key == "open_meteo"
    assert OPEN_METEO.name == "Open-Meteo"
    assert OPEN_METEO.variables == (
        "cloud_cover",
        "cloud_low",
        "cloud_mid",
        "cloud_high",
        "wind_gust",
        "temperature",
        "dew_point",
        "humidity",
        "wind_speed",
        "wind_direction",
        "precipitation_probability",
    )
    assert OPEN_METEO.bundles == (_CLOUD_BUNDLE,)
    assert not OPEN_METEO.needs_key


def test_seven_timer_declares_seeing_and_transparency_and_no_bundle() -> None:
    assert SEVEN_TIMER.key == "seven_timer"
    assert SEVEN_TIMER.name == "7Timer!"
    assert SEVEN_TIMER.variables == ("seeing", "transparency")
    assert SEVEN_TIMER.bundles == ()
    assert not SEVEN_TIMER.needs_key


def test_catalog_maps_each_key_to_its_spec() -> None:
    assert CATALOG == {"open_meteo": OPEN_METEO, "seven_timer": SEVEN_TIMER}


def test_bundle_of_gives_a_variables_bundle_or_the_variable_alone() -> None:
    assert OPEN_METEO.bundle_of("cloud_low") == _CLOUD_BUNDLE
    assert OPEN_METEO.bundle_of("wind_gust") == frozenset({"wind_gust"})


def test_a_spec_is_frozen() -> None:
    spec = ProviderSpec(key="k", name="K", needs_key=False, variables=("seeing",))
    assert spec.bundles == ()
    with pytest.raises(FrozenInstanceError):
        spec.key = "other"  # type: ignore[misc]
