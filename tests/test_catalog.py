"""Tasks 2.1-2.4: OpenNGC catalog parsing, eligibility filtering, and the loader.

The parser is checked against real rows committed under
``pierpressure/data/openngc`` (including an addendum row), so the tests exercise
the actual vendored bytes rather than a synthetic fixture.
"""

from __future__ import annotations

import pytest

from pierpressure.core.catalog import (
    MAGNITUDE_LIMIT,
    CatalogObject,
    is_eligible,
    load_catalog,
    parse_row,
)

from .offline_guard import no_network

# A real NGC row (M31, the Andromeda Galaxy) as OpenNGC's semicolon CSV records
# it, reduced to the columns the parser reads.
_M31_ROW = {
    "Name": "NGC0224",
    "Type": "G",
    "RA": "00:42:44.35",
    "Dec": "+41:16:08.6",
    "MajAx": "177.83",
    "SurfBr": "13.91",
    "V-Mag": "3.44",
    "B-Mag": "4.29",
    "M": "031",
    "Common names": "Andromeda Galaxy",
}

# A real addendum row (the Horsehead Nebula): a dark nebula with no magnitude and
# a southern (negative) declination whose degree field is single-digit.
_HORSEHEAD_ROW = {
    "Name": "B033",
    "Type": "DrkN",
    "RA": "05:40:59.0",
    "Dec": "-02:27:30",
    "MajAx": "6.00",
    "V-Mag": "",
    "B-Mag": "",
    "M": "",
    "Common names": "Horsehead Nebula",
}


# --------------------------------------------------------------------------- #
# Task 2.1 / 2.2 — parsing
# --------------------------------------------------------------------------- #


def test_parse_ra_sexagesimal_to_hours() -> None:
    obj = parse_row(_M31_ROW)
    # 0h + 42m + 44.35s = 0 + 42/60 + 44.35/3600 hours.
    assert obj.ra_hours == pytest.approx(0 + 42 / 60 + 44.35 / 3600)


def test_parse_dec_sexagesimal_to_degrees() -> None:
    obj = parse_row(_M31_ROW)
    assert obj.dec_degrees == pytest.approx(41 + 16 / 60 + 8.6 / 3600)


def test_parse_negative_declination_applies_sign_to_whole() -> None:
    obj = parse_row(_HORSEHEAD_ROW)
    # A single-digit, negative degree field must sign the whole value.
    assert obj.dec_degrees == pytest.approx(-(2 + 27 / 60 + 30 / 3600))
    assert obj.ra_hours == pytest.approx(5 + 40 / 60 + 59 / 3600)


def test_parse_type_designation_and_name() -> None:
    obj = parse_row(_M31_ROW)
    assert obj.id == "NGC0224"
    assert obj.type == "G"
    assert obj.name == "Andromeda Galaxy"


def test_parse_magnitude_prefers_visual_then_blue() -> None:
    assert parse_row(_M31_ROW).magnitude == pytest.approx(3.44)
    # A row with no V-Mag falls back to B-Mag.
    b_only = {**_M31_ROW, "V-Mag": "", "B-Mag": "4.29"}
    assert parse_row(b_only).magnitude == pytest.approx(4.29)


def test_parse_blank_magnitude_is_none() -> None:
    obj = parse_row(_HORSEHEAD_ROW)
    assert obj.magnitude is None


def test_parse_size_from_major_axis() -> None:
    assert parse_row(_M31_ROW).size_arcmin == pytest.approx(177.83)


def test_parse_blank_size_is_none() -> None:
    no_size = {**_M31_ROW, "MajAx": ""}
    assert parse_row(no_size).size_arcmin is None


def test_parse_surface_brightness() -> None:
    assert parse_row(_M31_ROW).surface_brightness == pytest.approx(13.91)


def test_parse_blank_surface_brightness_is_none() -> None:
    no_sb = {**_M31_ROW, "SurfBr": ""}
    assert parse_row(no_sb).surface_brightness is None
    # The Horsehead addendum row carries no surface brightness at all.
    assert parse_row(_HORSEHEAD_ROW).surface_brightness is None


def test_parse_no_common_name_is_none() -> None:
    anon = {**_M31_ROW, "Common names": ""}
    assert parse_row(anon).name is None


def test_parse_multiple_common_names_takes_first() -> None:
    two = {**_M31_ROW, "Common names": "Triangulum Galaxy,Triangulum Pinwheel"}
    assert parse_row(two).name == "Triangulum Galaxy"


# --------------------------------------------------------------------------- #
# Task 2.3 — eligibility filtering
# --------------------------------------------------------------------------- #


def _obj(type_: str, magnitude: float | None) -> CatalogObject:
    return CatalogObject(
        id="X",
        name=None,
        type=type_,
        ra_hours=0.0,
        dec_degrees=0.0,
        magnitude=magnitude,
        size_arcmin=None,
        surface_brightness=None,
    )


@pytest.mark.parametrize("type_", ["G", "GPair", "OCl", "GCl", "PN", "Neb", "SNR", "Cl+N"])
def test_observable_types_are_eligible(type_: str) -> None:
    assert is_eligible(_obj(type_, magnitude=6.0))


@pytest.mark.parametrize("type_", ["*", "**", "Dup", "NonEx", "*Ass", "Other", "Nova"])
def test_stars_duplicates_and_nonexistent_are_excluded(type_: str) -> None:
    assert not is_eligible(_obj(type_, magnitude=6.0))


def test_faint_object_is_excluded() -> None:
    assert not is_eligible(_obj("G", magnitude=MAGNITUDE_LIMIT + 0.1))


def test_object_at_the_limit_is_kept() -> None:
    assert is_eligible(_obj("G", magnitude=MAGNITUDE_LIMIT))


def test_unknown_magnitude_object_is_kept() -> None:
    assert is_eligible(_obj("G", magnitude=None))


# --------------------------------------------------------------------------- #
# Task 2.4 — the cached, offline, deterministic loader
# --------------------------------------------------------------------------- #


def test_catalog_loads_with_no_network() -> None:
    with no_network():
        catalog = load_catalog()
    assert catalog  # non-empty
    assert all(isinstance(obj, CatalogObject) for obj in catalog)


def test_loader_returns_only_eligible_objects() -> None:
    catalog = load_catalog()
    assert all(is_eligible(obj) for obj in catalog)


def test_catalog_contains_a_known_object() -> None:
    catalog = load_catalog()
    by_id = {obj.id: obj for obj in catalog}
    m31 = by_id["NGC0224"]
    assert m31.name == "Andromeda Galaxy"
    assert m31.type == "G"
    assert m31.ra_hours == pytest.approx(0 + 42 / 60 + 44.35 / 3600)


def test_two_loads_yield_identical_object_set_and_coordinates() -> None:
    first = load_catalog()
    second = load_catalog()
    # Determinism: same objects, same order, same coordinates.
    assert [(o.id, o.type, o.ra_hours, o.dec_degrees, o.magnitude) for o in first] == [
        (o.id, o.type, o.ra_hours, o.dec_degrees, o.magnitude) for o in second
    ]


def test_catalog_order_is_stable_and_sorted_by_id() -> None:
    catalog = load_catalog()
    ids = [obj.id for obj in catalog]
    assert ids == sorted(ids)
