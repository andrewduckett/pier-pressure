"""produce_verdict fills later_nights: one dark window per solar day the forecast reaches.

Each test is a night-verdict scenario of the later-night-dark-windows change.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from pierpressure.core import producer, ranking, sky
from pierpressure.core.catalog import load_catalog
from pierpressure.core.clock import FixedClock
from pierpressure.core.conditions import Conditions, Series
from pierpressure.core.config import PierConfig
from pierpressure.core.model import Moon
from pierpressure.core.producer import produce_verdict
from pierpressure.core.providers import OPEN_METEO_GFS

from .offline_guard import no_network

_ISSUED = datetime(2026, 9, 7, 0, 0, tzinfo=UTC)
LONDON = PierConfig(id="london", latitude=51.5, longitude=-0.12, elevation_m=30.0)
LONDON_INSTANT = datetime(2026, 9, 8, 18, 0, tzinfo=UTC)


def _at(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def _hourly(first: str, last: str, value: float, provider: str = "open_meteo") -> Series:
    """A series holding ``value`` in every hour from ``first`` to ``last``, both included."""
    start, end = _at(first), _at(last)
    hours = [start + timedelta(hours=i) for i in range(int((end - start) / timedelta(hours=1)) + 1)]
    return Series(provider=provider, issued_at=_ISSUED, values=dict.fromkeys(hours, value))


def _cloud(first: str, last: str) -> Conditions:
    return Conditions(series={"cloud_cover": _hourly(first, last, 20.0)})


def _payload(pier: PierConfig, instant: datetime, conditions: Conditions) -> dict[str, Any]:
    with no_network():
        document = produce_verdict(pier, FixedClock(instant), conditions)
    payload: dict[str, Any] = json.loads(document.to_json())
    return payload


def _london(conditions: Conditions) -> dict[str, Any]:
    return _payload(LONDON, LONDON_INSTANT, conditions)


def _starts(payload: dict[str, Any]) -> list[str | None]:
    return [entry["dark_window"]["start"] for entry in payload["later_nights"]]


@pytest.mark.usefixtures("empty_catalog")
def test_two_later_nights_carry_their_dark_windows() -> None:
    payload = _london(_cloud("2026-09-08T18:00:00Z", "2026-09-10T18:00:00Z"))
    assert [entry["dark_window"] for entry in payload["later_nights"]] == [
        {"start": "2026-09-09T20:27:57Z", "end": "2026-09-10T03:28:02Z"},
        {"start": "2026-09-10T20:25:07Z", "end": "2026-09-11T03:30:11Z"},
    ]


@pytest.mark.usefixtures("empty_catalog")
def test_later_nights_is_the_last_key_after_observation() -> None:
    payload = _london(_cloud("2026-09-08T18:00:00Z", "2026-09-10T18:00:00Z"))
    assert list(payload)[-2:] == ["observation", "later_nights"]


@pytest.mark.usefixtures("empty_catalog")
def test_the_empty_conditions_give_an_empty_list() -> None:
    assert _london(Conditions())["later_nights"] == []


@pytest.mark.usefixtures("empty_catalog")
def test_the_document_keys_are_in_order() -> None:
    assert list(_london(Conditions())) == [
        "pier",
        "generated_at",
        "verdict",
        "score",
        "confidence",
        "reasons",
        "targets",
        "dark_window",
        "scored_window",
        "moon",
        "timeline",
        "agreement",
        "observation",
        "later_nights",
    ]


@pytest.mark.usefixtures("empty_catalog")
def test_a_six_day_forecast_gives_three_later_nights() -> None:
    payload = _london(_cloud("2026-09-08T18:00:00Z", "2026-09-14T18:00:00Z"))
    assert _starts(payload) == [
        "2026-09-09T20:27:57Z",
        "2026-09-10T20:25:07Z",
        "2026-09-11T20:22:18Z",
    ]


@pytest.mark.usefixtures("empty_catalog")
def test_a_selected_night_with_no_dark_window_still_has_later_nights() -> None:
    pier = PierConfig(id="june", latitude=55.0, longitude=-3.0, elevation_m=0.0)
    payload = _payload(
        pier,
        datetime(2026, 6, 21, 8, 0, tzinfo=UTC),
        _cloud("2026-06-21T08:00:00Z", "2026-06-23T18:00:00Z"),
    )
    assert payload["dark_window"] == {"start": None, "end": None}
    assert [entry["dark_window"] for entry in payload["later_nights"]] == [
        {"start": None, "end": None},
        {"start": None, "end": None},
    ]


@pytest.mark.usefixtures("empty_catalog")
def test_a_last_hour_ending_after_the_solar_noon_counts_its_solar_day() -> None:
    payload = _london(_cloud("2026-09-08T18:00:00Z", "2026-09-10T11:00:00Z"))
    assert len(payload["later_nights"]) == 2


@pytest.mark.usefixtures("empty_catalog")
def test_a_last_hour_ending_before_the_solar_noon_does_not_count_its_solar_day() -> None:
    payload = _london(_cloud("2026-09-08T18:00:00Z", "2026-09-10T10:00:00Z"))
    assert _starts(payload) == ["2026-09-09T20:27:57Z"]


@pytest.mark.usefixtures("empty_catalog")
def test_hours_only_an_alternate_covers_add_no_later_night() -> None:
    conditions = Conditions(
        series={"cloud_cover": _hourly("2026-09-08T18:00:00Z", "2026-09-09T18:00:00Z", 20.0)},
        alternates={
            "cloud_cover": (
                _hourly("2026-09-08T18:00:00Z", "2026-09-11T18:00:00Z", 70.0, OPEN_METEO_GFS.key),
            )
        },
    )
    assert len(_london(conditions)["later_nights"]) == 1


@pytest.mark.usefixtures("empty_catalog")
def test_hours_only_a_hidden_variable_covers_add_no_later_night() -> None:
    conditions = Conditions(
        series={
            "aerosol_optical_depth": _hourly(
                "2026-09-08T18:00:00Z", "2026-09-11T18:00:00Z", 0.14, "open_meteo_air_quality"
            )
        }
    )
    assert _london(conditions)["later_nights"] == []


@pytest.mark.usefixtures("empty_catalog")
def test_a_solar_day_after_darkness_ends_has_a_null_window() -> None:
    pier = PierConfig(id="may", latitude=52.0, longitude=0.0, elevation_m=0.0)
    payload = _payload(
        pier,
        datetime(2026, 5, 19, 15, 0, tzinfo=UTC),
        _cloud("2026-05-19T15:00:00Z", "2026-05-21T18:00:00Z"),
    )
    assert payload["dark_window"] == {
        "start": "2026-05-19T23:42:13Z",
        "end": "2026-05-20T00:10:20Z",
    }
    assert [entry["dark_window"] for entry in payload["later_nights"]] == [
        {"start": None, "end": None},
        {"start": None, "end": None},
    ]


@pytest.mark.usefixtures("empty_catalog")
def test_continuous_polar_night_windows_follow_one_another() -> None:
    pier = PierConfig(id="polar", latitude=88.0, longitude=0.0, elevation_m=0.0)
    payload = _payload(
        pier,
        datetime(2026, 12, 10, 12, 0, tzinfo=UTC),
        _cloud("2026-12-10T12:00:00Z", "2026-12-14T12:00:00Z"),
    )
    windows = [entry["dark_window"] for entry in payload["later_nights"]]
    assert len(windows) == 3
    assert [w["end"] for w in windows[:-1]] == [w["start"] for w in windows[1:]]
    for window in windows:
        span = _at(window["end"]) - _at(window["start"])
        assert abs(span - timedelta(days=1)) < timedelta(minutes=1)


@pytest.mark.usefixtures("empty_catalog")
def test_every_entry_holds_its_dark_window_moon_and_targets() -> None:
    payload = _london(_cloud("2026-09-08T18:00:00Z", "2026-09-14T18:00:00Z"))
    assert [list(entry) for entry in payload["later_nights"]] == [
        ["dark_window", "moon", "targets"]
    ] * 3


@pytest.mark.usefixtures("empty_catalog")
def test_the_next_nights_moon_is_taken_at_its_local_solar_midnight() -> None:
    payload = _london(_cloud("2026-09-08T18:00:00Z", "2026-09-10T18:00:00Z"))
    assert payload["later_nights"][0]["moon"] == {
        "illumination": 0.02,
        "phase": "new",
        "up_during_dark": False,
        "rise": None,
        "set": None,
    }
    assert payload["moon"]["illumination"] == 0.07


@pytest.mark.usefixtures("empty_catalog")
def test_the_moon_instant_is_the_floored_middle_of_the_solar_day(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: list[datetime] = []
    real = sky.moon_info

    def spy(pier: PierConfig, window: Any, instant: datetime) -> Moon:
        seen.append(instant)
        return real(pier, window, instant)

    monkeypatch.setattr(producer, "moon_info", spy)
    _london(_cloud("2026-09-08T18:00:00Z", "2026-09-10T18:00:00Z"))
    assert seen[1] == _at("2026-09-09T23:57:37Z")


@pytest.mark.usefixtures("empty_catalog")
def test_a_moon_up_all_through_a_later_night() -> None:
    payload = _payload(
        LONDON,
        datetime(2026, 11, 21, 12, 0, tzinfo=UTC),
        _cloud("2026-11-21T12:00:00Z", "2026-11-23T18:00:00Z"),
    )
    assert payload["later_nights"][0]["moon"] == {
        "illumination": 0.96,
        "phase": "waxing gibbous",
        "up_during_dark": True,
        "rise": None,
        "set": None,
    }


@pytest.mark.usefixtures("empty_catalog")
def test_a_later_night_with_no_darkness_keeps_its_illumination_and_phase() -> None:
    pier = PierConfig(id="may", latitude=52.0, longitude=0.0, elevation_m=0.0)
    payload = _payload(
        pier,
        datetime(2026, 5, 19, 15, 0, tzinfo=UTC),
        _cloud("2026-05-19T15:00:00Z", "2026-05-21T18:00:00Z"),
    )
    assert payload["later_nights"][0]["moon"] == {
        "illumination": 0.24,
        "phase": "waxing crescent",
        "up_during_dark": None,
        "rise": None,
        "set": None,
    }


# --------------------------------------------------------------------------- #
# Later nights' targets (later-night-targets)
# --------------------------------------------------------------------------- #

_TWO_NIGHTS = ("2026-09-08T18:00:00Z", "2026-09-10T18:00:00Z")


@pytest.fixture(scope="module")
def london_two_nights() -> dict[str, Any]:
    return _london(_cloud(*_TWO_NIGHTS))


@pytest.fixture(scope="module")
def london_full_moon() -> dict[str, Any]:
    return _payload(
        LONDON,
        datetime(2026, 11, 21, 12, 0, tzinfo=UTC),
        _cloud("2026-11-21T12:00:00Z", "2026-11-23T18:00:00Z"),
    )


def test_the_next_nights_top_target_is_ranked_over_its_whole_dark_window(
    london_two_nights: dict[str, Any],
) -> None:
    first = london_two_nights["later_nights"][0]["targets"][0]
    whole = {"start": "2026-09-09T20:27:57Z", "end": "2026-09-10T03:28:02Z"}
    assert (first["id"], first["score"]) == ("NGC7394", 99)
    assert first["window"] == whole
    assert first["remaining_window"] == whole


def test_a_dark_later_night_holds_ten_targets_by_score(
    london_two_nights: dict[str, Any],
) -> None:
    for night in london_two_nights["later_nights"]:
        scores = [target["score"] for target in night["targets"]]
        assert len(scores) == 10
        assert scores == sorted(scores, reverse=True)


def test_every_later_night_targets_remaining_window_is_its_window(
    london_two_nights: dict[str, Any],
) -> None:
    targets = [t for night in london_two_nights["later_nights"] for t in night["targets"]]
    assert targets
    assert all(t["remaining_window"] == t["window"] for t in targets)


def test_a_brighter_moon_changes_the_later_nights_lists(
    london_full_moon: dict[str, Any],
) -> None:
    later = london_full_moon["later_nights"]
    assert london_full_moon["targets"][0]["id"] == "NGC1491"
    assert [night["targets"][0]["id"] for night in later] == ["IC0463", "NGC3690A"]


def test_a_later_night_with_no_darkness_has_no_targets() -> None:
    pier = PierConfig(id="may", latitude=52.0, longitude=0.0, elevation_m=0.0)
    payload = _payload(
        pier,
        datetime(2026, 5, 19, 15, 0, tzinfo=UTC),
        _cloud("2026-05-19T15:00:00Z", "2026-05-21T18:00:00Z"),
    )
    assert [night["targets"] for night in payload["later_nights"]] == [[], []]


def test_later_nights_leave_tonights_fields_as_they_were(
    london_two_nights: dict[str, Any],
) -> None:
    alone = _london(_cloud("2026-09-08T18:00:00Z", "2026-09-09T06:00:00Z"))
    fields = ["verdict", "score", "reasons", "targets", "dark_window", "scored_window", "moon"]
    assert (len(london_two_nights["later_nights"]), alone["later_nights"]) == (2, [])
    assert {f: london_two_nights[f] for f in fields} == {f: alone[f] for f in fields}


def _counting_scans(monkeypatch: pytest.MonkeyPatch) -> list[tuple[datetime, datetime]]:
    scanned: list[tuple[datetime, datetime]] = []
    real = ranking._scan_night

    def counting(pier: PierConfig, window: tuple[datetime, datetime]) -> Any:
        scanned.append(window)
        return real(pier, window, objects=())

    monkeypatch.setattr(ranking, "_scan_night", counting)
    return scanned


@pytest.fixture
def fresh_scan_cache() -> Iterator[None]:
    """Clear the scan cache on both sides, so a failing test leaves no scan behind."""
    ranking._scan_cache.clear()
    yield
    ranking._scan_cache.clear()


@pytest.mark.usefixtures("fresh_scan_cache")
def test_a_recompute_a_day_on_scans_only_the_new_night(monkeypatch: pytest.MonkeyPatch) -> None:
    scanned = _counting_scans(monkeypatch)
    _london(_cloud("2026-09-08T18:00:00Z", "2026-09-14T18:00:00Z"))
    del scanned[:]
    payload = _payload(
        LONDON,
        datetime(2026, 9, 9, 18, 0, tzinfo=UTC),
        _cloud("2026-09-09T18:00:00Z", "2026-09-15T18:00:00Z"),
    )
    assert payload["dark_window"] == {
        "start": "2026-09-09T20:27:57Z",
        "end": "2026-09-10T03:28:02Z",
    }
    assert len(scanned) == 1
    assert scanned[0][0].date().isoformat() == "2026-09-12"


@pytest.mark.usefixtures("fresh_scan_cache")
def test_a_recompute_in_the_same_night_ranks_tonight_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # A slice of the catalog keeps four scans quick and the lists non-empty.
    sample = load_catalog()[::40]
    monkeypatch.setattr(ranking, "load_catalog", lambda: sample)
    week = _cloud("2026-09-08T18:00:00Z", "2026-09-14T18:00:00Z")
    first = _london(week)
    ranks = {"count": 0}
    real = ranking._rank

    def counting(*args: Any, **kwargs: Any) -> Any:
        ranks["count"] += 1
        return real(*args, **kwargs)

    monkeypatch.setattr(ranking, "_rank", counting)
    again = _payload(LONDON, datetime(2026, 9, 8, 19, 0, tzinfo=UTC), week)
    assert ranks["count"] == 1
    assert all(n["targets"] for n in first["later_nights"])
    assert [n["targets"] for n in again["later_nights"]] == [
        n["targets"] for n in first["later_nights"]
    ]
