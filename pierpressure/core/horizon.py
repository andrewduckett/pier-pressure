"""The canonical horizon representation and its importers (ADR-0007, design D1).

A pier's horizon — the terrain that blocks parts of its sky — is one shape no
matter where it came from: an azimuth-sorted set of ``(azimuth, altitude)``
samples, closed into a ring so the arc from the greatest azimuth back to the
least wraps across the 360/0 boundary. Azimuth is measured from true north at 0
degrees, clockwise; a supplied 360 is the same direction as 0. The altitude at
any azimuth is the linear interpolation of the two bracketing samples.

This module is pure core: it takes horizon **text**, never file paths, so the
config layer reads bytes and hands text here and ``produce_verdict`` never
touches the filesystem (design D4). Altitudes are rounded to a fixed decimal
precision both at construction and in the query, mirroring the ``_round_fraction``
idiom in ``model.py``, so the same samples and azimuth yield the same altitude —
and the same above/below classification at a grazing boundary — across platforms.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

# Fixed decimal precision for altitudes (design D1, ADR-0007). Rounding at both
# construction and query is what keeps the horizon deterministic across
# platforms, consistent with the core's determinism guarantee (ADR-0004).
ALTITUDE_DECIMALS = 3

_AZIMUTH_FULL = 360.0
_AZIMUTH_MAX = 360.0
_ALTITUDE_MIN = 0.0
_ALTITUDE_MAX = 90.0


def _round_altitude(value: float) -> float:
    """Round an altitude to the module's fixed precision (design D1)."""
    return round(float(value), ALTITUDE_DECIMALS)


def _normalize_azimuth(az: float) -> float:
    """Fold an azimuth into the half-open range [0, 360); 360 becomes 0."""
    return float(az) % _AZIMUTH_FULL


@dataclass(frozen=True)
class Horizon:
    """An immutable, azimuth-sorted ring of ``(azimuth, altitude)`` samples.

    Build one with :meth:`from_samples` (or the :func:`flat`, :func:`open_sky`,
    and :func:`from_points` helpers), never by passing ``samples`` directly — the
    class trusts that its samples are already normalized, altitude-rounded,
    azimuth-sorted, and free of duplicate azimuths.
    """

    samples: tuple[tuple[float, float], ...]

    @classmethod
    def from_samples(cls, samples: Iterable[tuple[float, float]]) -> Horizon:
        """Build the canonical horizon from raw ``(az, alt)`` samples.

        Azimuths are normalized (360 -> 0), altitudes are rounded to the fixed
        precision, and the samples are sorted by azimuth. Two samples at the same
        azimuth are deduplicated when their rounded altitudes are equal and raise
        :class:`ValueError` when they differ, because one direction cannot rise to
        two altitudes. At least one sample is required.
        """
        by_azimuth: dict[float, float] = {}
        for az, alt in samples:
            azimuth = _normalize_azimuth(az)
            altitude = _round_altitude(alt)
            existing = by_azimuth.get(azimuth)
            if existing is not None and existing != altitude:
                raise ValueError(
                    f"conflicting altitudes {existing} and {altitude} at azimuth {azimuth}"
                )
            by_azimuth[azimuth] = altitude
        if not by_azimuth:
            raise ValueError("a horizon requires at least one sample")
        ordered = tuple(sorted(by_azimuth.items()))
        return cls(samples=ordered)

    def alt_at(self, az: float) -> float:
        """Return the terrain altitude at azimuth ``az``, rounded to fixed precision.

        A single-sample horizon is that constant altitude everywhere. Otherwise the
        result is the linear interpolation of the two bracketing samples, treating
        the sample set as a closed ring so the wrap arc (greatest azimuth back to
        least, across 360/0) interpolates like any other segment. An input azimuth
        of exactly 360 behaves as 0.
        """
        azimuth = _normalize_azimuth(az)
        samples = self.samples
        if len(samples) == 1:
            return samples[0][1]

        for sample_az, sample_alt in samples:
            if sample_az == azimuth:
                return sample_alt

        first_az = samples[0][0]
        last_az = samples[-1][0]
        if first_az < azimuth < last_az:
            for i in range(len(samples) - 1):
                low_az, low_alt = samples[i]
                high_az, high_alt = samples[i + 1]
                if low_az < azimuth < high_az:
                    return _interpolate(low_az, low_alt, high_az, high_alt, azimuth)

        # Wrap arc: from the greatest azimuth up over 360/0 to the least.
        low_az, low_alt = samples[-1]
        high_az, high_alt = samples[0]
        span = (_AZIMUTH_FULL - low_az) + high_az
        offset = (azimuth - low_az) if azimuth > low_az else (_AZIMUTH_FULL - low_az) + azimuth
        fraction = offset / span
        return _round_altitude(low_alt + fraction * (high_alt - low_alt))

    def is_above(self, az: float, alt: float) -> bool:
        """Classify a point at ``(az, alt)`` as above (visible) the horizon.

        A point is above the horizon when its altitude is greater than or equal to
        the terrain altitude in its direction, so a grazing point on the boundary
        is treated as visible rather than ambiguously excluded (ADR-0007).
        """
        return alt >= self.alt_at(az)


def _interpolate(
    low_az: float, low_alt: float, high_az: float, high_alt: float, azimuth: float
) -> float:
    """Linear interpolation of altitude between two bracketing samples, rounded."""
    fraction = (azimuth - low_az) / (high_az - low_az)
    return _round_altitude(low_alt + fraction * (high_alt - low_alt))


def flat(altitude: float) -> Horizon:
    """A flat horizon at a constant ``altitude`` in every direction.

    This is the degenerate single-sample case of the same representation, so a
    ``min_altitude`` floor and the query share one code path. The altitude must
    lie in 0 to 90 degrees.
    """
    if not _ALTITUDE_MIN <= altitude <= _ALTITUDE_MAX:
        raise ValueError(
            f"flat horizon altitude {altitude} is outside 0 to 90 degrees"
        )
    return Horizon.from_samples([(0.0, altitude)])


def open_sky() -> Horizon:
    """The default horizon: flat 0 degrees — open sky down to the true horizon."""
    return flat(0.0)


def from_points(points: Iterable[tuple[float, float]]) -> Horizon:
    """Build a horizon from inline ``(azimuth, altitude)`` pairs.

    The pairs need not be ordered. Each azimuth must lie in 0 to 360 degrees (360
    normalized to 0) and each altitude in 0 to 90 degrees; a pair outside those
    ranges raises :class:`ValueError`. Duplicate azimuths follow the dedup/conflict
    rule of :meth:`Horizon.from_samples`. At least one pair is required.
    """
    validated: list[tuple[float, float]] = []
    for az, alt in points:
        if not _ALTITUDE_MIN <= az <= _AZIMUTH_MAX:
            raise ValueError(f"azimuth {az} is outside 0 to 360 degrees")
        if not _ALTITUDE_MIN <= alt <= _ALTITUDE_MAX:
            raise ValueError(f"altitude {alt} is outside 0 to 90 degrees")
        validated.append((float(az), float(alt)))
    if not validated:
        raise ValueError("a horizon requires at least one point")
    return Horizon.from_samples(validated)


def parse_nina(text: str) -> Horizon:
    """Parse a NINA ``.hrz`` export's ``azimuth altitude`` pair-per-line text.

    Blank lines and comment lines — those whose first non-whitespace character is
    ``#`` — are ignored. Two file-specific quirks are tolerated rather than
    rejected: an azimuth of exactly 360 is normalized to 0 (and deduplicated), and
    an altitude below 0 (sub-horizon terrain) is clamped to 0. A line that is
    neither blank, a comment, nor a parseable pair raises :class:`ValueError`.
    """
    samples: list[tuple[float, float]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split()
        if len(parts) != 2:
            raise ValueError(f"malformed NINA horizon line: {line!r}")
        try:
            azimuth = float(parts[0])
            altitude = float(parts[1])
        except ValueError as exc:
            raise ValueError(f"malformed NINA horizon line: {line!r}") from exc
        samples.append((azimuth, max(altitude, 0.0)))
    if not samples:
        raise ValueError("NINA horizon export contains no samples")
    return Horizon.from_samples(samples)


# Recognized format names. Supported formats map to a text parser; recognized but
# unsupported formats raise a clear error so an unimplemented importer can never
# silently fall back to open sky (spec: unsupported formats fail clearly).
_PARSERS = {"nina": parse_nina}
_RECOGNIZED_UNSUPPORTED = frozenset({"stellarium", "telescopius"})


def parse_horizon_text(fmt: str, text: str) -> Horizon:
    """Parse horizon ``text`` in the named ``fmt`` into the canonical horizon.

    ``nina`` is supported now. ``stellarium`` and ``telescopius`` are recognized
    names that raise a clear "not yet supported" error until a real export fixture
    lands. Any other name is rejected as unknown.
    """
    key = fmt.lower()
    parser = _PARSERS.get(key)
    if parser is not None:
        return parser(text)
    if key in _RECOGNIZED_UNSUPPORTED:
        raise ValueError(f"horizon format {fmt!r} is recognized but not yet supported")
    raise ValueError(f"unknown horizon format {fmt!r}")
