"""metar-reason: parsing and fetching the latest METAR (design DD3)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
import pytest

from pierpressure import __version__
from pierpressure.conditions.metar import MetarFetcher, NoReport, parse_metar
from pierpressure.core.observation import CloudLayer, Observation

_FIXTURE = Path(__file__).parent / "fixtures" / "metar.json"


def _recorded() -> list[dict[str, Any]]:
    payload: list[dict[str, Any]] = json.loads(_FIXTURE.read_text(encoding="utf-8"))
    return payload


def _report(station: str = "KBOS", **fields: Any) -> dict[str, Any]:
    report: dict[str, Any] = {
        "icaoId": station,
        "obsTime": 1794693240,
        "reportTime": "2026-11-14T22:00:00.000Z",
        "cover": "BKN",
        "clouds": [],
    }
    report.update(fields)
    return report


def test_parse_the_recorded_report_as_an_observation() -> None:
    assert parse_metar(_recorded(), "KBOS") == Observation(
        station="KBOS",
        observed_at=datetime(2026, 11, 14, 21, 54, tzinfo=UTC),
        cover="OVC",
        clouds=(CloudLayer("BKN", 4000), CloudLayer("BKN", 4900), CloudLayer("OVC", 9500)),
    )


def test_parse_takes_the_report_for_the_station() -> None:
    payload = [_report("KJFK", cover="FEW"), _report("KBOS", cover="OVC")]
    observation = parse_metar(payload, "KBOS")
    assert (observation.station, observation.cover) == ("KBOS", "OVC")


def test_parse_keeps_a_layer_with_no_base() -> None:
    payload = [_report(clouds=[{"cover": "FEW", "base": 3000}, {"cover": "BKN", "base": None}])]
    assert parse_metar(payload, "KBOS").clouds == (CloudLayer("FEW", 3000), CloudLayer("BKN", None))


def test_parse_keeps_a_layer_whose_base_is_missing() -> None:
    payload = [_report(clouds=[{"cover": "BKN"}])]
    assert parse_metar(payload, "KBOS").clouds == (CloudLayer("BKN", None),)


@pytest.mark.parametrize("clear", ["CLR", "SKC", "NCD", "NSC"])
def test_parse_drops_a_layer_that_says_there_is_no_cloud(clear: str) -> None:
    payload = [_report(cover=clear, clouds=[{"cover": clear, "base": None}])]
    observation = parse_metar(payload, "KBOS")
    assert (observation.cover, observation.clouds) == (clear, ())


def test_parse_a_clear_report_with_no_layers() -> None:
    observation = parse_metar([_report(cover="CLR", clouds=[])], "KBOS")
    assert (observation.cover, observation.clouds) == ("CLR", ())


def test_parse_keeps_an_unworded_cover_code() -> None:
    payload = [_report(cover="OVX", clouds=[{"cover": "VV", "base": 200}])]
    assert parse_metar(payload, "KBOS").clouds == (CloudLayer("VV", 200),)


def test_parse_raises_no_report_without_the_station() -> None:
    with pytest.raises(NoReport):
        parse_metar([_report("KJFK")], "KBOS")


def _fetcher(handle: Any, requests: list[httpx.Request] | None = None) -> MetarFetcher:
    def record(request: httpx.Request) -> httpx.Response:
        if requests is not None:
            requests.append(request)
        response: httpx.Response = handle(request)
        return response

    return MetarFetcher(client=httpx.Client(transport=httpx.MockTransport(record)))


def test_fetch_sends_one_get_for_the_station() -> None:
    requests: list[httpx.Request] = []
    _fetcher(lambda _: httpx.Response(200, json=_recorded()), requests).fetch("KBOS")
    (request,) = requests
    assert request.method == "GET"
    assert str(request.url) == "https://aviationweather.gov/api/data/metar?ids=KBOS&format=json"


def test_fetch_sends_the_fixed_user_agent() -> None:
    requests: list[httpx.Request] = []
    _fetcher(lambda _: httpx.Response(200, json=_recorded()), requests).fetch("KBOS")
    agent = requests[0].headers["User-Agent"]
    assert "PierPressure" in agent
    assert __version__ in agent
    assert "https://github.com/andrewduckett/pier-pressure" in agent
    assert "@" not in agent


def test_fetch_returns_the_parsed_observation() -> None:
    observation = _fetcher(lambda _: httpx.Response(200, json=_recorded())).fetch("KBOS")
    assert observation.observed_at == datetime(2026, 11, 14, 21, 54, tzinfo=UTC)


@pytest.mark.parametrize(
    "response",
    [httpx.Response(204, content=b""), httpx.Response(200, json=[])],
    ids=["204-empty-body", "empty-list"],
)
def test_fetch_with_no_report_raises_no_report(response: httpx.Response) -> None:
    with pytest.raises(NoReport) as raised:
        _fetcher(lambda _: response).fetch("KZZZ")
    assert raised.value.description == "no report returned"


def test_fetch_raises_on_a_server_error() -> None:
    with pytest.raises(httpx.HTTPStatusError):
        _fetcher(lambda _: httpx.Response(503)).fetch("KBOS")
