"""firms-nearby-fire: parsing and fetching FIRMS fire detections (design DD3, DD8)."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from pierpressure.conditions.firms import UnexpectedResponse, parse_firms
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
