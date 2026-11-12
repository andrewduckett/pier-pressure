"""Loading the bundled astronomical data (story #211).

``skyfield_data.get_skyfield_data_path()`` warns for every bundled file whose
recorded expiry date has passed, including ``finals2000A.all``, which the core
never reads. The core finds ``de421.bsp`` by its package location instead, so
no such warning can appear, whatever today's date.
"""

from __future__ import annotations

import warnings
from collections.abc import Iterator
from datetime import UTC, date, datetime

import pytest
from skyfield.errors import EphemerisRangeError
from skyfield_data import expirations

from pierpressure.core import sky
from pierpressure.core.clock import FixedClock
from pierpressure.core.producer import produce_verdict

from .conftest import make_conditions, make_pier


@pytest.fixture
def fresh_ephemeris() -> Iterator[None]:
    sky._ephemeris.cache_clear()
    yield
    sky._ephemeris.cache_clear()


def test_ephemeris_loads_without_warning_after_every_bundled_file_expires(
    monkeypatch: pytest.MonkeyPatch, fresh_ephemeris: None
) -> None:
    expired = {name: date(2000, 1, 1) for name in expirations.EXPIRATIONS}
    monkeypatch.setattr(expirations, "EXPIRATIONS", expired)

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        eph = sky._ephemeris()

    assert eph["earth"] is not None


def test_verdict_past_the_ephemeris_range_fails_naming_its_end() -> None:
    clock = FixedClock(datetime(2060, 1, 1, 22, 0, tzinfo=UTC))

    with pytest.raises(EphemerisRangeError, match="2053-10-09"):
        produce_verdict(make_pier(), clock, make_conditions())
