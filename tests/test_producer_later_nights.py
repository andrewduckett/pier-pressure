"""produce_verdict fills later_nights: one dark window per solar day the forecast reaches.

Each test is a night-verdict scenario of the later-night-dark-windows change.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import Any

from pierpressure.core.clock import FixedClock
from pierpressure.core.conditions import Conditions, Series
from pierpressure.core.config import PierConfig
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


def test_two_later_nights_carry_their_dark_windows() -> None:
    payload = _london(_cloud("2026-09-08T18:00:00Z", "2026-09-10T18:00:00Z"))
    assert payload["later_nights"] == [
        {"dark_window": {"start": "2026-09-09T20:27:57Z", "end": "2026-09-10T03:28:02Z"}},
        {"dark_window": {"start": "2026-09-10T20:25:07Z", "end": "2026-09-11T03:30:11Z"}},
    ]


def test_later_nights_is_the_last_key_after_observation() -> None:
    payload = _london(_cloud("2026-09-08T18:00:00Z", "2026-09-10T18:00:00Z"))
    assert list(payload)[-2:] == ["observation", "later_nights"]


def test_the_empty_conditions_give_an_empty_list() -> None:
    assert _london(Conditions())["later_nights"] == []


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


def test_a_six_day_forecast_gives_three_later_nights() -> None:
    payload = _london(_cloud("2026-09-08T18:00:00Z", "2026-09-14T18:00:00Z"))
    assert _starts(payload) == [
        "2026-09-09T20:27:57Z",
        "2026-09-10T20:25:07Z",
        "2026-09-11T20:22:18Z",
    ]


def test_a_selected_night_with_no_dark_window_still_has_later_nights() -> None:
    pier = PierConfig(id="june", latitude=55.0, longitude=-3.0, elevation_m=0.0)
    payload = _payload(
        pier,
        datetime(2026, 6, 21, 8, 0, tzinfo=UTC),
        _cloud("2026-06-21T08:00:00Z", "2026-06-23T18:00:00Z"),
    )
    assert payload["dark_window"] == {"start": None, "end": None}
    assert payload["later_nights"] == [
        {"dark_window": {"start": None, "end": None}},
        {"dark_window": {"start": None, "end": None}},
    ]


def test_a_last_hour_ending_after_the_solar_noon_counts_its_solar_day() -> None:
    payload = _london(_cloud("2026-09-08T18:00:00Z", "2026-09-10T11:00:00Z"))
    assert len(payload["later_nights"]) == 2


def test_a_last_hour_ending_before_the_solar_noon_does_not_count_its_solar_day() -> None:
    payload = _london(_cloud("2026-09-08T18:00:00Z", "2026-09-10T10:00:00Z"))
    assert _starts(payload) == ["2026-09-09T20:27:57Z"]


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


def test_hours_only_a_hidden_variable_covers_add_no_later_night() -> None:
    conditions = Conditions(
        series={
            "aerosol_optical_depth": _hourly(
                "2026-09-08T18:00:00Z", "2026-09-11T18:00:00Z", 0.14, "open_meteo_air_quality"
            )
        }
    )
    assert _london(conditions)["later_nights"] == []


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
    assert payload["later_nights"] == [
        {"dark_window": {"start": None, "end": None}},
        {"dark_window": {"start": None, "end": None}},
    ]


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


def test_every_entry_holds_only_its_dark_window() -> None:
    payload = _london(_cloud("2026-09-08T18:00:00Z", "2026-09-14T18:00:00Z"))
    assert [list(entry) for entry in payload["later_nights"]] == [["dark_window"]] * 3
