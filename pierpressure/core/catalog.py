"""The deep-sky object catalog: parse, filter, and load OpenNGC (ADR-0008, design D1).

This is pure core. It reads the version-pinned OpenNGC data files bundled with
the package (``pierpressure/data/openngc``) — never the network — and hands the
ranking engine an immutable table of eligible :class:`CatalogObject` records. The
committed bytes are the version pin, so the same application version always yields
the same objects and coordinates (ADR-0004, ADR-0008), exactly as the ephemeris
loader in ``core/sky.py`` does.

OpenNGC is a semicolon-delimited CSV of NGC/IC objects. Two files are read: the
main catalog and its addendum (Barnard, LDN, and other non-NGC objects). Each row
carries a designation, a type code, sexagesimal J2000 RA/Dec, an optional
magnitude and size, and an optional common name; the parser reads exactly those
columns and ignores the rest. Coordinates are parsed to hours/degrees and left at
full float precision — Skyfield precesses them to the evaluation instant in the
ranking engine, and rounding happens only where the verdict document is emitted.
"""

from __future__ import annotations

import csv
from collections.abc import Mapping
from dataclasses import dataclass
from functools import lru_cache
from importlib import resources

# The bundled data package and its two files (design D1, ADR-0008). Read via
# ``importlib.resources`` so it resolves inside a wheel as well as the source
# tree, mirroring how ``core/sky.py`` loads the pinned ephemeris from local data.
_DATA_PACKAGE = "pierpressure.data.openngc"
_CATALOG_FILES = ("NGC.csv", "addendum.csv")

# The observable deep-sky object types kept as ranking candidates (spec:
# galaxies, nebulae, and clusters). Everything else — stars (``*``, ``**``),
# stellar associations (``*Ass``), novae, duplicate entries (``Dup``),
# non-existent entries (``NonEx``), and OpenNGC's catch-all ``Other`` — is
# dropped. Grouped by family for readability; the parser compares against the
# flat set.
_GALAXY_TYPES = frozenset({"G", "GPair", "GTrpl", "GGroup"})
_NEBULA_TYPES = frozenset({"PN", "Neb", "EmN", "RfN", "SNR", "HII", "DrkN"})
_CLUSTER_TYPES = frozenset({"OCl", "GCl"})
# A cluster embedded in nebulosity is both a cluster and a nebula; kept.
_MIXED_TYPES = frozenset({"Cl+N"})
ELIGIBLE_TYPES = _GALAXY_TYPES | _NEBULA_TYPES | _CLUSTER_TYPES | _MIXED_TYPES

# The faint-object cutoff (design D3/D5; a tuning constant validated in task 8.2).
# Objects fainter than this are excluded as candidates; an object with no recorded
# magnitude is kept, so a real object is never dropped for missing data. At 13.0
# every eligible Messier object survives while the ~14k-row catalog reduces to a
# few thousand candidates the coarse grid scan can afford.
MAGNITUDE_LIMIT = 13.0


@dataclass(frozen=True)
class CatalogObject:
    """One eligible deep-sky object, as parsed from OpenNGC.

    ``ra_hours`` and ``dec_degrees`` are J2000 equatorial coordinates at full
    parsed precision. ``magnitude`` is the visual magnitude when recorded, else
    the blue magnitude, else ``None`` (unknown, kept as a candidate). ``name`` is
    the first recorded common name or ``None``. ``size_arcmin`` is the major-axis
    size when recorded, and ``surface_brightness`` (mag/arcsec²) is recorded for
    many extended objects — both feed the equipment ranking terms (design D3/D4)
    and are ``None`` when the source records none.
    """

    id: str
    name: str | None
    type: str
    ra_hours: float
    dec_degrees: float
    magnitude: float | None
    size_arcmin: float | None
    surface_brightness: float | None


def _parse_ra_hours(text: str) -> float:
    """Parse an OpenNGC ``HH:MM:SS.ss`` right ascension to decimal hours."""
    hours, minutes, seconds = (float(part) for part in text.split(":"))
    return hours + minutes / 60.0 + seconds / 3600.0


def _parse_dec_degrees(text: str) -> float:
    """Parse an OpenNGC ``sDD:MM:SS.s`` declination to signed decimal degrees.

    The leading sign governs the whole value, so a single-digit or ``00`` degree
    field with a ``-`` (for example ``-00:27:30``) still yields a negative result.
    """
    stripped = text.strip()
    sign = -1.0 if stripped.startswith("-") else 1.0
    degrees, minutes, seconds = (abs(float(part)) for part in stripped.lstrip("+-").split(":"))
    return sign * (degrees + minutes / 60.0 + seconds / 3600.0)


def _parse_optional_float(text: str) -> float | None:
    """A blank cell to ``None``, otherwise the parsed float."""
    stripped = text.strip()
    return float(stripped) if stripped else None


def _parse_magnitude(row: Mapping[str, str]) -> float | None:
    """The object's magnitude: visual (``V-Mag``) if recorded, else blue (``B-Mag``).

    OpenNGC records a visual magnitude for most bright objects and only a blue
    magnitude for many fainter ones; taking visual-then-blue keeps a usable
    magnitude for the cutoff wherever the source has one, and yields ``None`` only
    when neither is recorded.
    """
    visual = _parse_optional_float(row.get("V-Mag", ""))
    if visual is not None:
        return visual
    return _parse_optional_float(row.get("B-Mag", ""))


def parse_row(row: Mapping[str, str]) -> CatalogObject:
    """Parse one OpenNGC CSV row into a :class:`CatalogObject`.

    The ``Common names`` cell may hold a comma-separated list; the first entry is
    taken as the object's name, and an empty cell yields ``None``.
    """
    common = row.get("Common names", "").strip()
    name = common.split(",")[0].strip() if common else None
    return CatalogObject(
        id=row["Name"].strip(),
        name=name or None,
        type=row["Type"].strip(),
        ra_hours=_parse_ra_hours(row["RA"]),
        dec_degrees=_parse_dec_degrees(row["Dec"]),
        magnitude=_parse_magnitude(row),
        size_arcmin=_parse_optional_float(row.get("MajAx", "")),
        surface_brightness=_parse_optional_float(row.get("SurfBr", "")),
    )


def is_eligible(obj: CatalogObject) -> bool:
    """Whether ``obj`` is a ranking candidate (spec: eligible type, within the cutoff).

    An object qualifies when its type is one of the observable deep-sky families
    and its magnitude is at or brighter than :data:`MAGNITUDE_LIMIT`. An object
    with no recorded magnitude is kept, so real objects are not dropped for
    missing data.
    """
    if obj.type not in ELIGIBLE_TYPES:
        return False
    if obj.magnitude is None:
        return True
    return obj.magnitude <= MAGNITUDE_LIMIT


@lru_cache(maxsize=1)
def load_catalog() -> tuple[CatalogObject, ...]:
    """Load, filter, and freeze the eligible catalog once (cached; offline).

    Reads the bundled OpenNGC files, parses each row, keeps only the eligible
    objects, and returns them as an immutable tuple sorted by designation. Sorting
    pins the iteration order regardless of file order, so the ranking's ``id``
    tie-break and the whole pipeline are deterministic (design D5). A row whose RA
    or Dec cannot be parsed is skipped rather than aborting the load — OpenNGC's
    non-existent and placeholder entries are not ranking candidates anyway.
    """
    objects: list[CatalogObject] = []
    for filename in _CATALOG_FILES:
        text = resources.files(_DATA_PACKAGE).joinpath(filename).read_text(encoding="utf-8")
        for row in csv.DictReader(text.splitlines(), delimiter=";"):
            # A fast-path of is_eligible's own type test: skip ineligible types
            # before parsing coordinates. is_eligible re-checks the type below, so
            # this only avoids work — it never widens or narrows eligibility.
            if row.get("Type", "").strip() not in ELIGIBLE_TYPES:
                continue
            try:
                obj = parse_row(row)
            except (ValueError, KeyError):
                continue
            if is_eligible(obj):
                objects.append(obj)
    return tuple(sorted(objects, key=lambda obj: obj.id))
