"""firms-nearby-fire: parsing and fetching FIRMS fire detections (design DD3, DD8)."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest
from pydantic import SecretStr

from pierpressure import __version__
from pierpressure.conditions.firms import (
    FirmsFetcher,
    UnexpectedResponse,
    firms_box,
    parse_firms,
)
from pierpressure.core.config import PierConfig
from pierpressure.core.fire import FireDetection

_FIXTURE = Path(__file__).parent / "fixtures" / "firms_viirs_noaa20.csv"
_HEADER = (
    "latitude,longitude,bright_ti4,scan,track,acq_date,acq_time,satellite,confidence,"
    "version,bright_ti5,frp,daynight"
)
_ROW = "46.76213,-71.00217,321.85,0.45,0.63,2026-11-13,0554,N20,nominal,2.0NRT,262.35,2.06,N"
_OTHER = "46.7646,-70.99916,304.2,0.52,0.5,2026-11-13,0735,N20,nominal,2.0NRT,263.76,1.68,N"


def _recorded() -> str:
    return _FIXTURE.read_text(encoding="utf-8")


# --------------------------------------------------------------------------- #
# 3.1: a response is read by column name, one detection per readable row
# --------------------------------------------------------------------------- #


def test_parse_a_recorded_row_as_a_fire_detection() -> None:
    assert parse_firms(f"{_HEADER}\n{_ROW}\n") == (
        FireDetection(
            latitude=46.76213,
            longitude=-71.00217,
            detected_at=datetime(2026, 11, 13, 5, 54, tzinfo=UTC),
            confidence="nominal",
        ),
    )


def test_parse_the_recorded_file_keeps_every_row_and_its_confidence() -> None:
    fires = parse_firms(_recorded())
    assert [fire.confidence for fire in fires] == [
        "low",
        "nominal",
        "nominal",
        "nominal",
        "nominal",
    ]
    assert fires[0].detected_at == datetime(2026, 11, 13, 0, 15, tzinfo=UTC)
    assert all(fire.detected_at.tzinfo is UTC for fire in fires)


def test_parse_a_header_only_body_gives_no_detections() -> None:
    assert parse_firms(f"{_HEADER}\n") == ()


def test_parse_ignores_an_extra_column() -> None:
    def with_instrument(line: str) -> str:
        cells = line.split(",")
        cells.insert(8, "instrument" if line == _HEADER else "VIIRS")
        return ",".join(cells)

    plain = parse_firms(f"{_HEADER}\n{_ROW}\n{_OTHER}\n")
    extra = "\n".join(with_instrument(line) for line in (_HEADER, _ROW, _OTHER))
    assert parse_firms(extra) == plain


def test_parse_reads_columns_in_any_order() -> None:
    reordered = (
        "confidence,acq_time,acq_date,longitude,latitude\n"
        "nominal,0554,2026-11-13,-71.00217,46.76213\n"
    )
    assert parse_firms(reordered) == parse_firms(f"{_HEADER}\n{_ROW}\n")


@pytest.mark.parametrize(
    "bad",
    [
        _ROW.replace("46.76213", "", 1),
        _ROW.replace("46.76213", "north", 1),
        _ROW.replace("2026-11-13", "13/11/2026", 1),
        _ROW.replace(",0554,", ",5:54,", 1),
        _ROW.replace(",0554,", ",2554,", 1),
        _ROW.rsplit(",", 5)[0],
    ],
    ids=["empty-latitude", "text-latitude", "bad-date", "bad-time", "hour-25", "short-row"],
)
def test_parse_skips_a_row_it_cannot_read(bad: str) -> None:
    assert parse_firms(f"{_HEADER}\n{bad}\n{_OTHER}\n") == parse_firms(f"{_HEADER}\n{_OTHER}\n")


@pytest.mark.parametrize(
    "body",
    ["Invalid MAP_KEY.", "", "latitude,longitude,acq_date,acq_time\n1,2,2026-11-13,0554\n"],
    ids=["invalid-key", "empty", "no-confidence-column"],
)
def test_parse_a_body_without_the_needed_header_is_unexpected(body: str) -> None:
    with pytest.raises(UnexpectedResponse) as raised:
        parse_firms(body)
    assert raised.value.description == "unexpected response"


# --------------------------------------------------------------------------- #
# 3.2: one GET per pier for the box that holds every point within 50 km
# --------------------------------------------------------------------------- #

_KEY = "abc123secret"


@pytest.mark.parametrize(
    ("latitude", "longitude", "box"),
    [
        (60.0, 10.0, "9.0000,59.5000,11.0000,60.5000"),
        (0.0, 179.8, "179.3000,-0.5000,180.0000,0.5000"),
        (0.0, -179.8, "-180.0000,-0.5000,-179.3000,0.5000"),
        (89.8, 10.0, "-180.0000,89.3000,180.0000,90.0000"),
        (-89.5, 10.0, "-180.0000,-90.0000,180.0000,-89.0000"),
    ],
    ids=["60-north", "antimeridian-east", "antimeridian-west", "north-pole", "south-pole"],
)
def test_firms_box_bounds_the_pier(latitude: float, longitude: float, box: str) -> None:
    assert firms_box(latitude, longitude) == box


def _fetcher(
    handler: Callable[[httpx.Request], httpx.Response], requests: list[httpx.Request] | None = None
) -> FirmsFetcher:
    def record(request: httpx.Request) -> httpx.Response:
        if requests is not None:
            requests.append(request)
        return handler(request)

    client = httpx.Client(transport=httpx.MockTransport(record))
    return FirmsFetcher(map_key=SecretStr(_KEY), client=client)


_PIER = PierConfig(id="north", latitude=60.0, longitude=10.0, elevation_m=0.0)


def test_fetch_sends_one_get_for_the_pier_box() -> None:
    requests: list[httpx.Request] = []
    _fetcher(lambda _: httpx.Response(200, text=f"{_HEADER}\n"), requests).fetch(_PIER)
    (request,) = requests
    assert request.method == "GET"
    assert str(request.url) == (
        "https://firms.modaps.eosdis.nasa.gov/api/area/csv/abc123secret/VIIRS_NOAA20_NRT/"
        "9.0000,59.5000,11.0000,60.5000/2"
    )


def test_fetch_sends_the_fixed_user_agent() -> None:
    requests: list[httpx.Request] = []
    _fetcher(lambda _: httpx.Response(200, text=f"{_HEADER}\n"), requests).fetch(_PIER)
    agent = requests[0].headers["User-Agent"]
    assert "PierPressure" in agent
    assert __version__ in agent


def test_fetch_returns_the_parsed_detections() -> None:
    fires = _fetcher(lambda _: httpx.Response(200, text=_recorded())).fetch(_PIER)
    assert len(fires) == 5


def test_fetch_raises_on_a_rejected_key() -> None:
    with pytest.raises(httpx.HTTPStatusError):
        _fetcher(lambda _: httpx.Response(400, text="Invalid MAP_KEY.")).fetch(_PIER)


def test_fetch_of_a_text_reply_with_a_success_status_is_unexpected() -> None:
    with pytest.raises(UnexpectedResponse):
        _fetcher(lambda _: httpx.Response(200, text="Invalid MAP_KEY.")).fetch(_PIER)


def test_the_fetcher_does_not_show_its_key() -> None:
    assert _KEY not in repr(_fetcher(lambda _: httpx.Response(200)))
