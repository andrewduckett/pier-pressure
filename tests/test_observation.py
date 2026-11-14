"""metar-reason: the observation value, its staleness rule and its reason line."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from pierpressure.core.observation import CloudLayer, Observation, usable

OBSERVED_AT = datetime(2026, 11, 14, 20, 54, tzinfo=UTC)


def _observation(*clouds: CloudLayer, cover: str = "BKN", station: str = "KBOS") -> Observation:
    return Observation(station=station, observed_at=OBSERVED_AT, cover=cover, clouds=clouds)


def test_an_observation_exactly_90_minutes_old_is_usable() -> None:
    assert usable(_observation(), OBSERVED_AT + timedelta(minutes=90))


def test_an_observation_91_minutes_old_is_not_usable() -> None:
    assert not usable(_observation(), OBSERVED_AT + timedelta(minutes=91))


def test_an_observation_measured_after_the_instant_is_not_usable() -> None:
    assert not usable(_observation(), OBSERVED_AT - timedelta(minutes=4))
