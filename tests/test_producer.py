"""Tasks 4.1 and 4.2: the stub producer and its determinism."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from pierpressure.core.clock import FixedClock
from pierpressure.core.conditions import Conditions, Series
from pierpressure.core.config import PierConfig
from pierpressure.core.model import Agreement, AgreementBand, MoonPhase, Verdict, VerdictDocument
from pierpressure.core.observation import CloudLayer, Observation
from pierpressure.core.producer import produce_verdict
from pierpressure.core.providers import OPEN_METEO, OPEN_METEO_HRRR
from pierpressure.delivery.mqtt import DeliveryError

from .conftest import make_pier, provider_series
from .offline_guard import no_network


def test_decision_fields_are_real_and_degrade_honestly_without_conditions() -> None:
    # With no conditions snapshot, cloud is entirely absent: the verdict degrades
    # honestly to MAYBE (never a false GO/NO-GO) rather than the old M1 stub.
    clock = FixedClock(datetime(2026, 9, 8, 14, 0, tzinfo=UTC))
    with no_network():
        doc = produce_verdict(make_pier(), clock, Conditions())
    assert doc.verdict is Verdict.MAYBE
    assert doc.score == 0
    assert doc.confidence.value == 0
    assert len(doc.reasons) >= 1 and all(r.strip() for r in doc.reasons)
    # Targets come from astronomy, not conditions: the London night still yields a
    # ranked list even with no conditions snapshot (M5 fills the once-empty stub).
    assert doc.targets
    assert all(0 <= t.score <= 100 for t in doc.targets)


def test_dark_window_and_moon_are_real_for_a_pinned_site_and_instant() -> None:
    # make_pier() is London; a daytime instant selects that evening's night.
    clock = FixedClock(datetime(2026, 9, 8, 14, 0, tzinfo=UTC))
    with no_network():
        doc = produce_verdict(make_pier(), clock, Conditions())

    # Real astronomical-night window, not the M1 null stub.
    assert doc.dark_window.start is not None and doc.dark_window.end is not None
    assert doc.dark_window.start < doc.dark_window.end

    # Real moon object across that window.
    assert 0.0 <= doc.moon.illumination <= 1.0
    assert isinstance(doc.moon.phase, MoonPhase)
    assert doc.moon.up_during_dark is True  # the moon rises during this night
    assert doc.moon.rise is not None
    assert doc.dark_window.start <= doc.moon.rise <= doc.dark_window.end


def test_determinism_is_byte_identical_and_pins_the_instant() -> None:
    instant = datetime(2026, 9, 7, 21, 30, tzinfo=UTC)
    clock = FixedClock(instant)
    pier = make_pier()

    first = produce_verdict(pier, clock, Conditions())
    second = produce_verdict(pier, clock, Conditions())

    assert first.to_json() == second.to_json()
    assert first.generated_at == instant


def test_invalid_pier_is_rejected_as_a_config_error_not_delivery() -> None:
    # An invalid site is rejected at PierConfig construction (a producer/config
    # domain error), so no document is ever produced.
    with pytest.raises(ValidationError):
        PierConfig(id="bad", latitude=200.0, longitude=-0.12, elevation_m=30.0)

    # Producer/config errors are a distinct type from delivery errors (design D9).
    assert not issubclass(ValidationError, DeliveryError)
    assert not issubclass(DeliveryError, ValidationError)


def test_scored_window_equals_the_dark_window_before_dusk() -> None:
    clock = FixedClock(datetime(2026, 9, 8, 14, 0, tzinfo=UTC))
    with no_network():
        doc = produce_verdict(make_pier(), clock, Conditions())
    assert doc.dark_window.start is not None
    assert doc.scored_window == doc.dark_window


def test_scored_window_starts_at_generated_at_mid_session() -> None:
    clock = FixedClock(datetime(2026, 9, 8, 23, 30, 0, 400_000, tzinfo=UTC))
    with no_network():
        doc = produce_verdict(make_pier(), clock, Conditions())
    assert doc.dark_window.start is not None and doc.dark_window.start < doc.generated_at
    assert doc.scored_window.start == doc.generated_at
    assert doc.scored_window.end == doc.dark_window.end


def test_scored_window_is_null_without_a_dark_window() -> None:
    # Tromso at midsummer: the sun never drops below -18 degrees.
    pier = PierConfig(id="tromso", latitude=69.65, longitude=18.96, elevation_m=10.0)
    clock = FixedClock(datetime(2026, 6, 21, 12, 0, tzinfo=UTC))
    with no_network():
        doc = produce_verdict(pier, clock, Conditions())
    assert doc.scored_window.start is None
    assert doc.scored_window.end is None


# --------------------------------------------------------------------------- #
# The document carries cloud agreement (cloud-agreement DD6)
# --------------------------------------------------------------------------- #

_BEFORE_DUSK = datetime(2026, 9, 8, 14, 0, tzinfo=UTC)
_ISSUED = datetime(2026, 9, 8, 13, 0, tzinfo=UTC)
_NIGHT = [datetime(2026, 9, 8, 12, tzinfo=UTC) + timedelta(hours=h) for h in range(24)]


def _two_providers(
    filled: float, alternate: float, *, alternate_issued: datetime = _ISSUED
) -> Conditions:
    series = provider_series(OPEN_METEO, _NIGHT, issued_at=_ISSUED, cloud_cover=filled)
    hrrr = provider_series(
        OPEN_METEO_HRRR, _NIGHT, issued_at=alternate_issued, cloud_cover=alternate
    )
    return Conditions(series=series, alternates={"cloud_cover": (hrrr["cloud_cover"],)})


def _produce(conditions: Conditions, pier: PierConfig | None = None) -> VerdictDocument:
    with no_network():
        return produce_verdict(pier or make_pier(), FixedClock(_BEFORE_DUSK), conditions)


def test_the_document_carries_the_agreement_of_two_providers_that_nearly_agree() -> None:
    doc = _produce(_two_providers(20.0, 28.0))
    assert doc.agreement == {
        "cloud_cover": Agreement(
            band=AgreementBand.AGREE, spread=8, providers=["open_meteo", "open_meteo_hrrr"]
        )
    }


def test_the_document_agreement_is_empty_from_one_provider() -> None:
    series = provider_series(OPEN_METEO, _NIGHT, issued_at=_ISSUED, cloud_cover=20.0)
    assert _produce(Conditions(series=series)).agreement == {}


def test_the_document_agreement_is_empty_without_a_dark_window() -> None:
    midsummer = datetime(2026, 6, 21, 12, tzinfo=UTC)
    hours = [midsummer + timedelta(hours=h) for h in range(24)]
    series = provider_series(OPEN_METEO, hours, issued_at=midsummer, cloud_cover=20.0)
    hrrr = provider_series(OPEN_METEO_HRRR, hours, issued_at=midsummer, cloud_cover=80.0)
    conditions = Conditions(series=series, alternates={"cloud_cover": (hrrr["cloud_cover"],)})
    pier = PierConfig(id="north", latitude=60.0, longitude=10.0, elevation_m=0.0)
    with no_network():
        doc = produce_verdict(pier, FixedClock(midsummer), conditions)
    assert doc.dark_window.start is None
    assert doc.agreement == {}


def test_mixed_agreement_lowers_confidence_without_changing_the_verdict() -> None:
    agree, mixed = _produce(_two_providers(20.0, 28.0)), _produce(_two_providers(20.0, 45.0))
    assert mixed.agreement["cloud_cover"].band is AgreementBand.MIXED
    assert mixed.confidence.value < agree.confidence.value
    assert (mixed.verdict, mixed.score) == (agree.verdict, agree.score)


def test_disagreement_lowers_confidence_below_mixed() -> None:
    mixed, disagree = _produce(_two_providers(20.0, 45.0)), _produce(_two_providers(20.0, 65.0))
    assert disagree.agreement["cloud_cover"].band is AgreementBand.DISAGREE
    assert disagree.confidence.value < mixed.confidence.value


def test_a_stale_alternate_leaves_the_document_byte_identical() -> None:
    fresh = _produce(_two_providers(20.0, 28.0))
    stale = _produce(_two_providers(20.0, 28.0, alternate_issued=_ISSUED - timedelta(days=3)))
    assert stale.to_json() == fresh.to_json()


def test_alternates_do_not_change_the_cloud_reading() -> None:
    alone = _produce(Conditions(series=_two_providers(20.0, 80.0).series))
    paired = _produce(_two_providers(20.0, 80.0))
    assert (paired.verdict, paired.score, paired.scored_window) == (
        alone.verdict,
        alone.score,
        alone.scored_window,
    )
    assert [e.cloud_cover for e in paired.timeline] == [e.cloud_cover for e in alone.timeline]


def test_the_agreement_reason_precedes_the_equipment_notes() -> None:
    doc = _produce(_two_providers(20.0, 28.0))
    line = "Cloud agreement agree: 2 providers, spread 8 points."
    assert doc.reasons.count(line) == 1
    assert doc.reasons.index(line) > doc.reasons.index(f"Score {doc.score}/100.")


# --------------------------------------------------------------------------- #
# The document carries the pier's latest usable observation (metar-reason DD1)
# --------------------------------------------------------------------------- #

_EVENING = datetime(2026, 11, 14, 21, 30, tzinfo=UTC)
_OBSERVED_AT = datetime(2026, 11, 14, 20, 54, tzinfo=UTC)
_NOVEMBER_NIGHT = [datetime(2026, 11, 14, 12, tzinfo=UTC) + timedelta(hours=h) for h in range(24)]


def _observation(observed_at: datetime = _OBSERVED_AT) -> Observation:
    return Observation(
        station="KBOS",
        observed_at=observed_at,
        cover="BKN",
        clouds=(CloudLayer("FEW", 3000), CloudLayer("BKN", 4200)),
    )


def _november_conditions(cloud: float = 20.0) -> Conditions:
    series = provider_series(
        OPEN_METEO,
        _NOVEMBER_NIGHT,
        issued_at=datetime(2026, 11, 14, 18, tzinfo=UTC),
        cloud_cover=cloud,
        wind_gust=10.0,
        temperature=8.0,
        dew_point=6.0,
    )
    return Conditions(series=series)


def _produce_at(
    instant: datetime,
    observation: Observation | None,
    *,
    conditions: Conditions | None = None,
    pier: PierConfig | None = None,
) -> VerdictDocument:
    with no_network():
        return produce_verdict(
            pier or make_pier(),
            FixedClock(instant),
            conditions or _november_conditions(),
            observation=observation,
        )


def test_a_usable_observation_fills_the_document_as_its_last_key() -> None:
    payload = json.loads(_produce_at(_EVENING, _observation()).to_json())
    assert payload["observation"] == {
        "station": "KBOS",
        "observed_at": "2026-11-14T20:54:00Z",
        "cover": "BKN",
        "clouds": [{"cover": "FEW", "base_ft": 3000}, {"cover": "BKN", "base_ft": 4200}],
    }
    assert list(payload)[-1] == "observation"


def test_no_observation_gives_a_null_observation() -> None:
    assert _produce_at(_EVENING, None).observation is None


def test_an_observation_exactly_90_minutes_old_is_in_the_document() -> None:
    doc = _produce_at(_OBSERVED_AT + timedelta(minutes=90), _observation())
    assert doc.observation is not None
    assert doc.observation.observed_at == _OBSERVED_AT


def test_an_observation_91_minutes_old_gives_a_null_observation() -> None:
    assert _produce_at(_OBSERVED_AT + timedelta(minutes=91), _observation()).observation is None


def test_an_observation_measured_after_the_instant_gives_a_null_observation() -> None:
    instant = datetime(2026, 11, 14, 20, 50, tzinfo=UTC)
    assert _produce_at(instant, _observation()).observation is None


def test_an_observation_changes_no_decision_field() -> None:
    plain = _produce_at(_EVENING, None)
    observed = _produce_at(_EVENING, _observation())
    assert observed.observation is not None
    assert (
        observed.verdict,
        observed.score,
        observed.confidence,
        observed.agreement,
        observed.timeline,
    ) == (plain.verdict, plain.score, plain.confidence, plain.agreement, plain.timeline)


_OBSERVATION_LINE = (
    "At 2026-11-14T20:54:00Z, KBOS reported few cloud at 3,000 ft and broken cloud at 4,200 ft."
)


def test_an_observation_adds_only_its_reason_line() -> None:
    plain = _produce_at(_EVENING, None)
    observed = _produce_at(_EVENING, _observation())
    assert observed.reasons == [*plain.reasons, _OBSERVATION_LINE]


def test_an_unusable_observation_adds_no_reason_line() -> None:
    doc = _produce_at(_OBSERVED_AT + timedelta(minutes=91), _observation())
    assert not any(line.startswith("At 2026-11-14T20:54:00Z") for line in doc.reasons)


def test_the_observation_line_follows_the_dew_line() -> None:
    doc = _produce_at(_EVENING, _observation())
    assert doc.verdict is Verdict.GO
    assert doc.reasons[-2].startswith("Dew likely from")
    assert doc.reasons[-1] == _OBSERVATION_LINE


def test_the_observation_line_precedes_the_equipment_notes() -> None:
    # The Cave Nebula tops the September night and frames well at 600 mm.
    instant = datetime(2026, 9, 8, 18, tzinfo=UTC)
    pier = PierConfig(
        id="backyard",
        latitude=51.5,
        longitude=-0.12,
        elevation_m=30.0,
        equipment={"focal_length_mm": 600.0, "sensor_width_mm": 23.5, "sensor_height_mm": 15.7},  # type: ignore[arg-type]
    )
    conditions = Conditions(
        series=provider_series(OPEN_METEO, _NIGHT, issued_at=_ISSUED, cloud_cover=20.0)
    )
    doc = _produce_at(
        instant,
        _observation(observed_at=instant - timedelta(minutes=20)),
        conditions=conditions,
        pier=pier,
    )
    line = next(i for i, r in enumerate(doc.reasons) if r.startswith("At "))
    notes = [i for i, r in enumerate(doc.reasons) if r.startswith("Top pick")]
    assert notes
    assert line < min(notes)


def test_a_gated_no_go_ends_with_the_observation_line() -> None:
    before_dusk = datetime(2026, 11, 14, 15, tzinfo=UTC)
    doc = _produce_at(
        before_dusk,
        _observation(observed_at=before_dusk - timedelta(minutes=30)),
        conditions=_november_conditions(cloud=100.0),
    )
    assert doc.verdict is Verdict.NO_GO
    assert doc.reasons[0].startswith("Overcast")
    assert doc.reasons[-1].startswith("At 2026-11-14T14:30:00Z, KBOS reported")


def test_a_night_with_no_dark_window_ends_with_the_observation_line() -> None:
    midsummer = datetime(2026, 6, 21, 22, tzinfo=UTC)
    pier = PierConfig(id="north", latitude=60.0, longitude=10.0, elevation_m=0.0)
    observation = _observation(observed_at=midsummer - timedelta(minutes=20))
    doc = _produce_at(midsummer, observation, conditions=Conditions(), pier=pier)
    assert doc.dark_window.start is None
    assert doc.reasons[-1].startswith("At 2026-06-21T21:40:00Z, KBOS reported")


# --------------------------------------------------------------------------- #
# Confidence falls when the observed cloud is above this hour's forecast
# (metar-confidence DD5)
# --------------------------------------------------------------------------- #

_FRESH = _EVENING - timedelta(minutes=30)


def _sky(
    low: float | None,
    mid: float | None,
    *,
    high: float | None = None,
    wind: float = 10.0,
    hours: list[datetime] = _NOVEMBER_NIGHT,
) -> Conditions:
    """A fresh, complete forecast that gives full confidence at the evening instant."""
    series = provider_series(
        OPEN_METEO,
        hours,
        issued_at=_FRESH,
        cloud_cover=20.0,
        cloud_low=low,
        cloud_mid=mid,
        cloud_high=high,
        wind_gust=wind,
    )
    for variable in ("seeing", "transparency"):
        series[variable] = Series(  # type: ignore[index]
            provider="computed", issued_at=_FRESH, values=dict.fromkeys(hours, 0.7)
        )
    return Conditions(series=series)


def _report(
    *clouds: CloudLayer, cover: str = "BKN", observed_at: datetime = _OBSERVED_AT
) -> Observation:
    return Observation(station="KBOS", observed_at=observed_at, cover=cover, clouds=clouds)


_BROKEN = _report(CloudLayer("BKN", 4200))
_OVERCAST = _report(CloudLayer("OVC", 1500), cover="OVC")


def test_an_observed_report_22_points_above_the_forecast_lowers_confidence_to_90() -> None:
    conditions = _sky(40.0, 0.0)
    assert _produce_at(_EVENING, None, conditions=conditions).confidence.value == 100
    assert _produce_at(_EVENING, _BROKEN, conditions=conditions).confidence.value == 90


def test_an_observed_report_lowers_a_wind_no_go_to_67() -> None:
    pier = PierConfig(
        id="backyard", latitude=51.5, longitude=-0.12, elevation_m=30.0, max_gust=30.0
    )
    conditions = _sky(0.0, 0.0, wind=50.0)
    plain = _produce_at(_EVENING, None, conditions=conditions, pier=pier)
    observed = _produce_at(_EVENING, _BROKEN, conditions=conditions, pier=pier)
    assert (plain.verdict, plain.confidence.value) == (Verdict.NO_GO, 100)
    assert observed.confidence.value == 67


_MIDSUMMER = datetime(2026, 6, 21, 22, tzinfo=UTC)


@pytest.mark.parametrize(
    ("instant", "observation", "conditions", "pier"),
    [
        pytest.param(
            _EVENING,
            _report(CloudLayer("SCT", 3000), cover="SCT"),
            _sky(25.0, 0.0),
            None,
            id="gap-under-15",
        ),
        pytest.param(_EVENING, _report(cover="CLR"), _sky(80.0, 0.0), None, id="clear"),
        pytest.param(_EVENING, _report(cover="CAVOK"), _sky(80.0, 0.0), None, id="cavok"),
        pytest.param(
            datetime(2026, 11, 14, 22, 25, tzinfo=UTC), _OVERCAST, _sky(0.0, 0.0), None, id="stale"
        ),
        pytest.param(_EVENING, _OVERCAST, _sky(80.0, None), None, id="no-mid-cloud"),
        pytest.param(
            _MIDSUMMER,
            _report(
                CloudLayer("OVC", 1500), cover="OVC", observed_at=_MIDSUMMER - timedelta(minutes=20)
            ),
            _sky(0.0, 0.0, hours=[_MIDSUMMER + timedelta(hours=h) for h in range(-2, 4)]),
            PierConfig(id="north", latitude=60.0, longitude=10.0, elevation_m=0.0),
            id="no-dark-window",
        ),
    ],
)
def test_an_observed_report_that_does_not_contradict_leaves_confidence_unchanged(
    instant: datetime, observation: Observation, conditions: Conditions, pier: PierConfig | None
) -> None:
    plain = _produce_at(instant, None, conditions=conditions, pier=pier)
    observed = _produce_at(instant, observation, conditions=conditions, pier=pier)
    assert observed.confidence == plain.confidence


def test_high_cloud_does_not_change_the_observed_confidence() -> None:
    clear_aloft = _produce_at(_EVENING, _BROKEN, conditions=_sky(20.0, 0.0, high=0.0))
    cirrus = _produce_at(_EVENING, _BROKEN, conditions=_sky(20.0, 0.0, high=100.0))
    assert cirrus.confidence == clear_aloft.confidence


def test_an_observed_report_changes_no_verdict_score_agreement_or_timeline() -> None:
    conditions = _sky(0.0, 0.0)
    plain = _produce_at(_EVENING, None, conditions=conditions)
    observed = _produce_at(_EVENING, _OVERCAST, conditions=conditions)
    assert observed.confidence != plain.confidence
    assert (observed.verdict, observed.score, observed.agreement, observed.timeline) == (
        plain.verdict,
        plain.score,
        plain.agreement,
        plain.timeline,
    )
