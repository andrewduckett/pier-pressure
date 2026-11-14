"""metar-reason: the observation value, its staleness rule and its reason line."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from pierpressure.core.observation import CloudLayer, Observation, observation_reason, usable

OBSERVED_AT = datetime(2026, 11, 14, 20, 54, tzinfo=UTC)


def _observation(*clouds: CloudLayer, cover: str = "BKN", station: str = "KBOS") -> Observation:
    return Observation(station=station, observed_at=OBSERVED_AT, cover=cover, clouds=clouds)


def test_an_observation_exactly_90_minutes_old_is_usable() -> None:
    assert usable(_observation(), OBSERVED_AT + timedelta(minutes=90))


def test_an_observation_91_minutes_old_is_not_usable() -> None:
    assert not usable(_observation(), OBSERVED_AT + timedelta(minutes=91))


def test_an_observation_measured_after_the_instant_is_not_usable() -> None:
    assert not usable(_observation(), OBSERVED_AT - timedelta(minutes=4))


def test_the_reason_joins_two_layers_with_and() -> None:
    observation = _observation(CloudLayer("FEW", 3000), CloudLayer("BKN", 4200))
    assert observation_reason(observation) == (
        "At 2026-11-14T20:54:00Z, KBOS reported few cloud at 3,000 ft and broken cloud at 4,200 ft."
    )


def test_the_reason_joins_three_layers_with_commas() -> None:
    observation = _observation(
        CloudLayer("FEW", 3000), CloudLayer("BKN", 4200), CloudLayer("OVC", 9500)
    )
    assert observation_reason(observation) == (
        "At 2026-11-14T20:54:00Z, KBOS reported few cloud at 3,000 ft, "
        "broken cloud at 4,200 ft and overcast cloud at 9,500 ft."
    )


def test_the_reason_names_layers_in_the_order_reported() -> None:
    observation = _observation(CloudLayer("OVC", 9500), CloudLayer("FEW", 3000))
    assert observation_reason(observation) == (
        "At 2026-11-14T20:54:00Z, KBOS reported overcast cloud at 9,500 ft "
        "and few cloud at 3,000 ft."
    )


def test_the_reason_says_a_layer_with_no_base_is_at_an_unknown_height() -> None:
    observation = _observation(CloudLayer("BKN", None))
    assert observation_reason(observation) == (
        "At 2026-11-14T20:54:00Z, KBOS reported broken cloud at an unknown height."
    )


def test_the_reason_keeps_a_layer_with_no_base_in_its_place() -> None:
    observation = _observation(CloudLayer("FEW", 3000), CloudLayer("BKN", None))
    assert observation_reason(observation) == (
        "At 2026-11-14T20:54:00Z, KBOS reported few cloud at 3,000 ft "
        "and broken cloud at an unknown height."
    )


def test_the_reason_words_scattered_cloud() -> None:
    observation = _observation(CloudLayer("SCT", 25000))
    assert observation_reason(observation) == (
        "At 2026-11-14T20:54:00Z, KBOS reported scattered cloud at 25,000 ft."
    )


def test_the_reason_words_an_obscured_sky() -> None:
    observation = _observation(CloudLayer("OVX", 300))
    assert observation_reason(observation) == (
        "At 2026-11-14T20:54:00Z, KBOS reported an obscured sky at 300 ft."
    )


def test_the_reason_gives_an_unknown_cover_code_as_reported() -> None:
    observation = _observation(CloudLayer("VV", 200))
    assert observation_reason(observation) == (
        "At 2026-11-14T20:54:00Z, KBOS reported VV at 200 ft."
    )


def test_the_reason_for_a_clear_report_says_no_cloud_below_12000_ft() -> None:
    observation = Observation(
        station="EGLL",
        observed_at=datetime(2026, 11, 14, 21, 20, tzinfo=UTC),
        cover="CLR",
        clouds=(),
    )
    assert observation_reason(observation) == (
        "At 2026-11-14T21:20:00Z, EGLL reported no cloud below 12,000 ft."
    )


def test_the_reason_for_a_cavok_report_says_no_cloud_below_5000_ft() -> None:
    observation = Observation(
        station="LFPG",
        observed_at=datetime(2026, 11, 14, 21, 0, tzinfo=UTC),
        cover="CAVOK",
        clouds=(),
    )
    assert observation_reason(observation) == (
        "At 2026-11-14T21:00:00Z, LFPG reported no cloud below 5,000 ft."
    )
