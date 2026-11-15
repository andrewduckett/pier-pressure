"""Fire detections near a pier from NASA FIRMS (firms-nearby-fire DD3).

A fire detection is a measurement of the ground, not a forecast: it never fills
a variable, so this module is not a provider and has no place in the provider
order. It turns the FIRMS area API's CSV into the core's
:class:`~pierpressure.core.fire.FireDetection`. Parsing is separated from
fetching so it can be tested against a recorded fixture with no network.
"""

from __future__ import annotations

import csv
import io
from collections.abc import Iterable
from datetime import UTC, datetime
from typing import ClassVar

from pierpressure.core.fire import FireDetection
from pierpressure.health import UNEXPECTED_RESPONSE, ProviderInfo

# Who reports FIRMS health. It is not a ProviderSpec and not in the catalog, so
# ``firms`` in the provider order stays an unknown key. It fills no variable.
FIRMS = ProviderInfo(key="firms", name="FIRMS", variables=())

_NEEDED = ("latitude", "longitude", "acq_date", "acq_time", "confidence")


class UnexpectedResponse(Exception):
    """The body has no CSV header with the columns a detection needs.

    FIRMS answers some errors as plain text, sometimes with a success status.
    """

    description: ClassVar[str] = UNEXPECTED_RESPONSE


def parse_firms(text: str) -> tuple[FireDetection, ...]:
    """The fire detections in a FIRMS CSV body, in the order given.

    Columns are found by name, so an extra column or a new order changes
    nothing. A row that cannot be read is left out, and the rest kept.
    """
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None or not set(_NEEDED) <= set(reader.fieldnames):
        raise UnexpectedResponse
    return tuple(_readable(reader))


def _readable(rows: Iterable[dict[str, str | None]]) -> Iterable[FireDetection]:
    for row in rows:
        try:
            yield _detection(row)
        except ValueError:
            continue


def _detection(row: dict[str, str | None]) -> FireDetection:
    """One row as a detection; ``acq_time`` is the pass's UTC hours and minutes, ``HHMM``."""
    time = _cell(row, "acq_time")
    if len(time) != 4:
        raise ValueError("acq_time is not HHMM")
    detected_at = datetime.strptime(f"{_cell(row, 'acq_date')} {time}", "%Y-%m-%d %H%M")
    return FireDetection(
        latitude=float(_cell(row, "latitude")),
        longitude=float(_cell(row, "longitude")),
        detected_at=detected_at.replace(tzinfo=UTC),
        confidence=_cell(row, "confidence"),
    )


def _cell(row: dict[str, str | None], column: str) -> str:
    """The row's text in ``column``; a short row leaves it ``None``."""
    value = row.get(column)
    if not value:
        raise ValueError(f"{column} is empty")
    return value
