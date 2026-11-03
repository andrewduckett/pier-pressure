"""Tasks 4.1 and 4.2: the stub producer and its determinism."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from pierpressure.core.clock import FixedClock
from pierpressure.core.conditions import Conditions
from pierpressure.core.config import PierConfig
from pierpressure.core.model import Agreement, AgreementBand, MoonPhase, Verdict, VerdictDocument
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
