"""The provider declarations in the core (provider-order design D2)."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from pierpressure.core.conditions import SEEING_COLUMN, Variable
from pierpressure.core.providers import (
    CATALOG,
    COMPUTED,
    NWS,
    OPEN_METEO,
    OPEN_METEO_AIR_QUALITY,
    OPEN_METEO_GFS,
    OPEN_METEO_HRDPS,
    OPEN_METEO_HRRR,
    OPEN_METEO_ICON,
    OPEN_METEO_RDPS,
    SEVEN_TIMER,
    ProviderSpec,
)

_CLOUD_BUNDLE = frozenset({"cloud_cover", "cloud_low", "cloud_mid", "cloud_high"})
_SEEING_BUNDLE = frozenset(SEEING_COLUMN)


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
        "column_water_vapour",
        *SEEING_COLUMN,
    )
    assert OPEN_METEO.bundles == (_CLOUD_BUNDLE, _SEEING_BUNDLE)
    assert not OPEN_METEO.needs_key


def test_nws_declares_total_cloud_and_the_weather_variables_with_no_bundle() -> None:
    assert NWS.key == "nws"
    assert NWS.name == "NWS"
    assert NWS.variables == (
        "cloud_cover",
        "wind_gust",
        "wind_speed",
        "wind_direction",
        "temperature",
        "dew_point",
        "humidity",
        "precipitation_probability",
    )
    assert NWS.bundles == ()
    assert not NWS.needs_key


def test_seven_timer_declares_seeing_and_transparency_and_no_bundle() -> None:
    assert SEVEN_TIMER.key == "seven_timer"
    assert SEVEN_TIMER.name == "7Timer!"
    assert SEVEN_TIMER.variables == ("seeing", "transparency")
    assert SEVEN_TIMER.bundles == ()
    assert not SEVEN_TIMER.needs_key


def test_the_air_quality_provider_declares_aerosol_then_pm2_5_and_no_bundle() -> None:
    assert OPEN_METEO_AIR_QUALITY.key == "open_meteo_air_quality"
    assert OPEN_METEO_AIR_QUALITY.name == "Open-Meteo air quality"
    assert OPEN_METEO_AIR_QUALITY.variables == ("aerosol_optical_depth", "pm2_5")
    assert OPEN_METEO_AIR_QUALITY.bundles == ()
    assert not OPEN_METEO_AIR_QUALITY.needs_key


def test_computed_declares_transparency_then_seeing_needing_no_key() -> None:
    assert COMPUTED.key == "computed"
    assert COMPUTED.name == "Computed"
    assert COMPUTED.variables == ("transparency", "seeing")
    assert COMPUTED.bundles == ()
    assert not COMPUTED.needs_key


_NO_WATER_VAPOUR = tuple(
    v for v in OPEN_METEO.variables if v != "column_water_vapour" and v not in SEEING_COLUMN
)
_NO_PRECIPITATION = tuple(v for v in _NO_WATER_VAPOUR if v != "precipitation_probability")
_BOTH = (_CLOUD_BUNDLE, _SEEING_BUNDLE)
_CLOUD = (_CLOUD_BUNDLE,)


@pytest.mark.parametrize(
    ("spec", "key", "name", "variables", "bundles"),
    [
        (OPEN_METEO_HRRR, "open_meteo_hrrr", "Open-Meteo HRRR", OPEN_METEO.variables, _BOTH),
        (OPEN_METEO_HRDPS, "open_meteo_hrdps", "Open-Meteo HRDPS", _NO_PRECIPITATION, _CLOUD),
        (OPEN_METEO_RDPS, "open_meteo_rdps", "Open-Meteo RDPS", _NO_PRECIPITATION, _CLOUD),
        (OPEN_METEO_ICON, "open_meteo_icon", "Open-Meteo ICON", _NO_WATER_VAPOUR, _CLOUD),
        (OPEN_METEO_GFS, "open_meteo_gfs", "Open-Meteo GFS", OPEN_METEO.variables, _BOTH),
    ],
)
def test_each_open_meteo_model_declares_what_its_model_returns(
    spec: ProviderSpec,
    key: str,
    name: str,
    variables: tuple[Variable, ...],
    bundles: tuple[frozenset[Variable], ...],
) -> None:
    assert spec.key == key
    assert spec.name == name
    assert spec.variables == variables
    assert spec.bundles == bundles
    assert not spec.needs_key


@pytest.mark.parametrize("spec", [OPEN_METEO_HRDPS, OPEN_METEO_RDPS, OPEN_METEO_ICON])
def test_hrdps_rdps_and_icon_declare_no_seeing_column_variable(spec: ProviderSpec) -> None:
    assert not set(SEEING_COLUMN) & set(spec.variables)


def test_hrdps_declares_no_precipitation_probability() -> None:
    assert "precipitation_probability" not in OPEN_METEO_HRDPS.variables
    assert "precipitation_probability" in OPEN_METEO_HRRR.variables


def test_hrdps_declares_no_column_water_vapour() -> None:
    assert "column_water_vapour" not in OPEN_METEO_HRDPS.variables


def test_icon_declares_precipitation_but_no_column_water_vapour() -> None:
    assert "precipitation_probability" in OPEN_METEO_ICON.variables
    assert "column_water_vapour" not in OPEN_METEO_ICON.variables


@pytest.mark.parametrize("spec", [OPEN_METEO_HRRR, OPEN_METEO_GFS])
def test_hrrr_and_gfs_declare_column_water_vapour_then_the_seeing_column(
    spec: ProviderSpec,
) -> None:
    assert spec.variables[-len(SEEING_COLUMN) - 1 :] == ("column_water_vapour", *SEEING_COLUMN)


def test_catalog_maps_each_key_to_its_spec_in_order() -> None:
    assert list(CATALOG.items()) == [
        ("open_meteo", OPEN_METEO),
        ("open_meteo_hrrr", OPEN_METEO_HRRR),
        ("open_meteo_hrdps", OPEN_METEO_HRDPS),
        ("open_meteo_rdps", OPEN_METEO_RDPS),
        ("open_meteo_icon", OPEN_METEO_ICON),
        ("open_meteo_gfs", OPEN_METEO_GFS),
        ("open_meteo_air_quality", OPEN_METEO_AIR_QUALITY),
        ("nws", NWS),
        ("seven_timer", SEVEN_TIMER),
        ("computed", COMPUTED),
    ]


def test_bundle_of_gives_a_variables_bundle_or_the_variable_alone() -> None:
    assert OPEN_METEO.bundle_of("cloud_low") == _CLOUD_BUNDLE
    assert OPEN_METEO.bundle_of("wind_gust") == frozenset({"wind_gust"})


def test_a_spec_is_frozen() -> None:
    spec = ProviderSpec(key="k", name="K", needs_key=False, variables=("seeing",))
    assert spec.bundles == ()
    with pytest.raises(FrozenInstanceError):
        spec.key = "other"  # type: ignore[misc]
