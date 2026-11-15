"""Tasks 6.1-6.4: the persistent loop, no-starvation, dedupe, on-demand refresh."""

from __future__ import annotations

import queue
from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from pierpressure.conditions import FetchResult
from pierpressure.conditions.firms import FIRMS
from pierpressure.conditions.metar import METAR
from pierpressure.core.clock import FixedClock
from pierpressure.core.config import AppConfig, PierConfig, RecomputeConfig
from pierpressure.core.fire import FireDetection
from pierpressure.core.observation import Observation
from pierpressure.core.providers import OPEN_METEO, SEVEN_TIMER
from pierpressure.delivery.mqtt import MqttDelivery, refresh_command_topic
from pierpressure.health import FetchOutcome, ProviderHealth, ProviderInfo
from pierpressure.service import Service

from .conftest import (
    FakeMessage,
    FakeMqttClient,
    RecordingDelivery,
    ScriptedMonotonic,
    ScriptedQueue,
    StepClock,
    fixed_conditions,
    make_conditions,
    make_mqtt_config,
    make_pier,
)


def _app_config(interval: int = 10, pier_ids: tuple[str, ...] = ("backyard",)) -> AppConfig:
    return AppConfig(
        mqtt=make_mqtt_config(),
        recompute=RecomputeConfig(interval_seconds=interval),
        piers=[make_pier(pid) for pid in pier_ids],
    )


def test_full_recompute_with_a_provider_publishes_a_real_verdict() -> None:
    # A stub provider supplies a clear-sky snapshot; a full recompute must publish
    # a real, gate-passing verdict (non-null integer score, itemised reasons) —
    # not the empty-snapshot "conditions unavailable" degradation.
    delivery = RecordingDelivery()
    clock = FixedClock(datetime(2026, 9, 8, 14, 0, tzinfo=UTC))  # London daytime -> that night
    provider = fixed_conditions(make_conditions(cloud=5.0))
    service = Service(_app_config(), delivery, clock, conditions_provider=provider)  # type: ignore[arg-type]
    service.run(monotonic=ScriptedMonotonic([0.0]), max_iterations=0)

    doc = delivery.documents[0]
    assert doc.verdict.value in {"GO", "MAYBE"}
    assert isinstance(doc.score, int)
    assert any("Cloud:" in reason for reason in doc.reasons)


def test_startup_publishes_all_piers() -> None:
    delivery = RecordingDelivery()
    service = Service(_app_config(pier_ids=("a", "b")), delivery, StepClock())  # type: ignore[arg-type]
    service.run(monotonic=ScriptedMonotonic([0.0]), max_iterations=0)
    assert {doc.pier for doc in delivery.documents} == {"a", "b"}


def test_frequent_refreshes_do_not_starve_the_interval_recompute() -> None:
    # Two refreshes are dequeued while now < deadline (deadline untouched); then
    # monotonic passes the deadline and the periodic all-pier recompute fires.
    calls: list[str | tuple[str, str]] = []
    service = Service(
        _app_config(interval=10),
        RecordingDelivery(),  # type: ignore[arg-type]
        FixedClock(datetime(2026, 9, 7, 21, 30, tzinfo=UTC)),
        refresh_queue=ScriptedQueue(["backyard", "backyard"]),  # type: ignore[arg-type]
    )
    service.publish_all = lambda: calls.append("all")  # type: ignore[method-assign]
    service.publish_pier = lambda pid: calls.append(("pier", pid))  # type: ignore[method-assign]

    # readings: startup deadline(0), iter1 now(1), iter2 now(2), iter3 now(11), reset(12)
    service.run(monotonic=ScriptedMonotonic([0.0, 1.0, 2.0, 11.0, 12.0]), max_iterations=3)

    assert calls.count("all") == 2  # startup + periodic (not starved)
    assert calls.count(("pier", "backyard")) == 2


def test_interval_recompute_republishes_all_with_later_generated_at() -> None:
    delivery = RecordingDelivery()
    service = Service(_app_config(interval=10, pier_ids=("a", "b")), delivery, StepClock())  # type: ignore[arg-type]
    # startup deadline(0); iter1 now(20) -> deadline passed -> publish_all; reset(30)
    service.run(monotonic=ScriptedMonotonic([0.0, 20.0, 30.0]), max_iterations=1)

    a_docs = [doc for doc in delivery.documents if doc.pier == "a"]
    assert len(a_docs) == 2  # startup + interval
    assert a_docs[1].generated_at > a_docs[0].generated_at


def test_refresh_republishes_exactly_the_target_pier() -> None:
    delivery = RecordingDelivery()
    service = Service(
        _app_config(interval=10, pier_ids=("a", "b")),
        delivery,  # type: ignore[arg-type]
        StepClock(),
        refresh_queue=ScriptedQueue(["a"]),  # type: ignore[arg-type]
    )
    # startup deadline(0); iter1 now(1) < deadline -> dequeue "a" -> publish pier a
    service.run(monotonic=ScriptedMonotonic([0.0, 1.0]), max_iterations=1)

    published_after_startup = delivery.documents[2:]  # first two are startup a,b
    assert [doc.pier for doc in published_after_startup] == ["a"]


def test_duplicate_refreshes_collapse_to_one_recompute() -> None:
    delivery = RecordingDelivery()
    real_queue: queue.Queue[str] = queue.Queue()
    for _ in range(5):
        real_queue.put("backyard")
    service = Service(_app_config(interval=10), delivery, StepClock(), refresh_queue=real_queue)  # type: ignore[arg-type]
    # startup deadline(0); iter1 now(1) -> dequeue one + drain the other 4 into a set
    service.run(monotonic=ScriptedMonotonic([0.0, 1.0]), max_iterations=1)

    after_startup = delivery.documents[1:]  # first is startup
    assert [doc.pier for doc in after_startup] == ["backyard"]  # one, not five


def test_command_on_refresh_topic_republishes_with_current_timestamp() -> None:
    from pierpressure.core.clock import SystemClock

    client = FakeMqttClient()
    delivery = MqttDelivery(make_mqtt_config(), client=client)
    config = _app_config(interval=10)
    service = Service(config, delivery, SystemClock())
    delivery.subscribe_refresh(["backyard"], service.enqueue_refresh)

    # Document timestamps are floored to whole seconds (design D3), so compare
    # against a likewise-floored capture of the command instant.
    command_time = datetime.now(UTC).replace(microsecond=0)
    # Simulate the broker delivering a refresh command to the callback.
    client.on_message(client, None, FakeMessage(refresh_command_topic("pierpressure", "backyard")))

    # Process the queued refresh (now < deadline so it is dequeued as a refresh).
    service.run(monotonic=ScriptedMonotonic([0.0, 1.0]), max_iterations=1)

    import json

    from pierpressure.delivery.mqtt import attributes_topic

    attrs = client.publishes_to(attributes_topic("pierpressure", "backyard"))
    generated_at = datetime.fromisoformat(json.loads(attrs[-1].payload)["generated_at"])
    assert generated_at >= command_time


# --------------------------------------------------------------------------- #
# Provider health (provider-health-entities D3, D4)
# --------------------------------------------------------------------------- #

_PROVIDERS = (
    ProviderInfo(key="open_meteo", name="Open-Meteo", variables=OPEN_METEO.variables),
    ProviderInfo(key="seven_timer", name="7Timer!", variables=SEVEN_TIMER.variables),
)
_START = datetime(2026, 9, 8, 14, 0, tzinfo=UTC)


class _ScriptedFetch:
    """Answer each pier's fetches with scripted (base ok, secondary ok) pairs.

    Each fetch is stamped at the next whole hour after ``_START``, and every call
    is logged to ``events`` so tests can see when fetching started.
    """

    def __init__(self, events: list[tuple[str, ...]], script: dict[str, list[bool]]) -> None:
        self._events = events
        self._script = {pier: list(oks) for pier, oks in script.items()}
        self._calls = 0

    def __call__(self, pier: PierConfig) -> FetchResult:
        self._events.append(("fetch", pier.id))
        self._calls += 1
        ok = self._script[pier.id].pop(0)
        fetched_at = _START + timedelta(hours=self._calls)
        outcomes = tuple(
            FetchOutcome(
                key=info.key,
                name=info.name,
                variables=info.variables,
                fetched_at=fetched_at,
                ok=ok,
                error=None if ok else "ConnectError",
                issued_at=_START if ok else None,
            )
            for info in _PROVIDERS
        )
        return FetchResult(make_conditions(), outcomes)


def _health_service(
    delivery: RecordingDelivery,
    script: dict[str, list[bool]],
    pier_ids: tuple[str, ...] = ("backyard",),
) -> Service:
    return Service(
        _app_config(pier_ids=pier_ids),
        delivery,  # type: ignore[arg-type]
        FixedClock(_START),
        conditions_provider=_ScriptedFetch(delivery.events, script),
        providers=_PROVIDERS,
    )


def test_startup_resets_health_before_going_online_and_before_fetching() -> None:
    delivery = RecordingDelivery()
    service = _health_service(delivery, {"a": [True], "b": [True]}, pier_ids=("a", "b"))
    service.run(monotonic=ScriptedMonotonic([0.0]), max_iterations=0)

    assert delivery.events[:3] == [("health", "a"), ("health", "b"), ("online",)]
    assert delivery.events[3] == ("fetch", "a")
    for pier_id, healths in delivery.healths[:2]:
        assert healths == tuple(
            ProviderHealth.empty(
                key=info.key, name=info.name, variables=info.variables, tracking_since=_START
            )
            for info in _PROVIDERS
        ), pier_id


def test_each_publish_sends_the_piers_health_right_after_its_verdict() -> None:
    delivery = RecordingDelivery()
    service = _health_service(delivery, {"backyard": [True]})
    service.run(monotonic=ScriptedMonotonic([0.0]), max_iterations=0)

    assert delivery.events[-3:] == [
        ("fetch", "backyard"),
        ("verdict", "backyard"),
        ("health", "backyard"),
    ]
    _, healths = delivery.healths[-1]
    assert [h.status for h in healths] == ["ok", "ok"]
    assert all(h.last_success == _START + timedelta(hours=1) for h in healths)


def test_a_failure_after_a_success_publishes_the_earlier_success() -> None:
    delivery = RecordingDelivery()
    service = _health_service(delivery, {"backyard": [True, False]})
    service.run(monotonic=ScriptedMonotonic([0.0]), max_iterations=0)
    service.publish_pier("backyard")

    _, healths = delivery.healths[-1]
    for health in healths:
        assert health.status == "failed"
        assert health.last_error == "ConnectError"
        assert health.last_fetch == _START + timedelta(hours=2)
        assert health.last_success == _START + timedelta(hours=1)
        assert health.issued_at == _START


def test_health_is_kept_per_pier() -> None:
    delivery = RecordingDelivery()
    service = _health_service(delivery, {"a": [True], "b": [False]}, pier_ids=("a", "b"))
    service.run(monotonic=ScriptedMonotonic([0.0]), max_iterations=0)

    latest = dict(delivery.healths)
    assert all(h.status == "ok" for h in latest["a"])
    assert all(h.status == "failed" and h.last_success is None for h in latest["b"])


def test_with_no_providers_no_health_is_published_and_it_goes_online_first() -> None:
    delivery = RecordingDelivery()
    service = Service(_app_config(), delivery, FixedClock(_START))  # type: ignore[arg-type]
    service.run(monotonic=ScriptedMonotonic([0.0]), max_iterations=0)

    assert delivery.events == [("online",), ("verdict", "backyard")]
    assert delivery.healths == []


def test_fetch_outcomes_do_not_change_the_verdict_document() -> None:
    # Same pier, instant, and snapshot; one run's fetches all succeed and the
    # other's all fail. The verdict documents must be byte-identical.
    documents = []
    for ok in (True, False):
        delivery = RecordingDelivery()
        _health_service(delivery, {"backyard": [ok]}).run(
            monotonic=ScriptedMonotonic([0.0]), max_iterations=0
        )
        assert [h.status for h in delivery.healths[-1][1]] == ["ok" if ok else "failed"] * 2
        documents.append(delivery.documents[0].to_json())
    assert documents[0] == documents[1]


def test_an_outcome_from_an_unconfigured_provider_is_logged(
    caplog: pytest.LogCaptureFixture,
) -> None:
    delivery = RecordingDelivery()
    service = Service(
        _app_config(),
        delivery,  # type: ignore[arg-type]
        FixedClock(_START),
        conditions_provider=_ScriptedFetch(delivery.events, {"backyard": [True]}),
        providers=_PROVIDERS[:1],  # seven_timer outcomes are not configured
    )
    service.run(monotonic=ScriptedMonotonic([0.0]), max_iterations=0)

    assert "seven_timer" in caplog.text
    _, healths = delivery.healths[-1]
    assert [h.key for h in healths] == ["open_meteo"]


# --------------------------------------------------------------------------- #
# METAR health and the observation (metar-reason DD8)
# --------------------------------------------------------------------------- #

_OBSERVED_AT = _START - timedelta(minutes=36)


def _metar_outcome(fetched_at: datetime, *, ok: bool = True) -> FetchOutcome:
    return FetchOutcome(
        key=METAR.key,
        name=METAR.name,
        variables=METAR.variables,
        fetched_at=fetched_at,
        ok=ok,
        error=None if ok else "no report returned",
        issued_at=_OBSERVED_AT if ok else None,
    )


class _MetarFetch:
    """Answer each fetch with an observation and a METAR outcome for a pier with a station."""

    def __init__(self, events: list[tuple[str, ...]], observed_at: datetime = _OBSERVED_AT) -> None:
        self._events = events
        self._observed_at = observed_at

    def __call__(self, pier: PierConfig) -> FetchResult:
        self._events.append(("fetch", pier.id))
        if pier.metar_station is None:
            return FetchResult(make_conditions())
        observation = Observation(
            station=pier.metar_station, observed_at=self._observed_at, cover="CLR", clouds=()
        )
        outcome = replace(_metar_outcome(_START), issued_at=self._observed_at)
        return FetchResult(make_conditions(), (outcome,), observation)


def _metar_service(
    delivery: RecordingDelivery, *, clock: datetime = _START, observed_at: datetime = _OBSERVED_AT
) -> Service:
    config = AppConfig(
        mqtt=make_mqtt_config(),
        recompute=RecomputeConfig(interval_seconds=10),
        piers=[
            make_pier("a").model_copy(update={"metar_station": "KBOS"}),
            make_pier("b"),
        ],
    )
    return Service(
        config,
        delivery,  # type: ignore[arg-type]
        FixedClock(clock),
        conditions_provider=_MetarFetch(delivery.events, observed_at),
        providers=_PROVIDERS,
    )


def test_startup_seeds_metar_health_only_for_a_pier_with_a_station() -> None:
    delivery = RecordingDelivery()
    _metar_service(delivery).run(monotonic=ScriptedMonotonic([0.0]), max_iterations=0)

    assert delivery.events[:3] == [("health", "a"), ("health", "b"), ("online",)]
    seeded = dict(delivery.healths[:2])
    assert seeded["a"][-1] == ProviderHealth.empty(
        key="metar", name="METAR", variables=(), tracking_since=_START
    )
    assert [h.key for h in seeded["b"]] == ["open_meteo", "seven_timer"]


def test_a_metar_outcome_folds_with_the_observation_time_as_its_issue_time() -> None:
    delivery = RecordingDelivery()
    _metar_service(delivery).run(monotonic=ScriptedMonotonic([0.0]), max_iterations=0)

    latest = dict(delivery.healths)
    metar = latest["a"][-1]
    assert (metar.key, metar.status, metar.last_success, metar.issued_at) == (
        "metar",
        "ok",
        _START,
        _OBSERVED_AT,
    )


def test_the_service_passes_the_observation_to_the_verdict() -> None:
    delivery = RecordingDelivery()
    _metar_service(delivery).run(monotonic=ScriptedMonotonic([0.0]), max_iterations=0)

    documents = {doc.pier: doc for doc in delivery.documents}
    assert documents["a"].observation is not None
    assert documents["a"].observation.observed_at == _OBSERVED_AT
    assert documents["b"].observation is None


def test_an_old_metar_report_is_ok_in_health_and_null_in_the_verdict() -> None:
    delivery = RecordingDelivery()
    old = _START - timedelta(hours=3)
    _metar_service(delivery, observed_at=old).run(
        monotonic=ScriptedMonotonic([0.0]), max_iterations=0
    )

    metar = dict(delivery.healths)["a"][-1]
    assert (metar.status, metar.issued_at) == ("ok", old)
    assert {doc.pier: doc for doc in delivery.documents}["a"].observation is None


def test_with_no_providers_a_pier_with_a_station_publishes_no_metar_health() -> None:
    delivery = RecordingDelivery()
    config = AppConfig(
        mqtt=make_mqtt_config(),
        recompute=RecomputeConfig(interval_seconds=10),
        piers=[make_pier("a").model_copy(update={"metar_station": "KBOS"})],
    )
    service = Service(
        config,
        delivery,  # type: ignore[arg-type]
        FixedClock(_START),
        conditions_provider=_MetarFetch(delivery.events),
    )
    service.run(monotonic=ScriptedMonotonic([0.0]), max_iterations=0)

    assert delivery.healths == []


# --------------------------------------------------------------------------- #
# FIRMS health and the fire detections (firms-nearby-fire DD7)
# --------------------------------------------------------------------------- #

_DETECTED_AT = _START - timedelta(hours=3)


class _FirmsFetch:
    """Answer each fetch with one fire detection near the pier and a FIRMS outcome."""

    def __init__(self, events: list[tuple[str, ...]]) -> None:
        self._events = events

    def __call__(self, pier: PierConfig) -> FetchResult:
        self._events.append(("fetch", pier.id))
        fire = FireDetection(
            latitude=pier.latitude + 0.1,
            longitude=pier.longitude,
            detected_at=_DETECTED_AT,
            confidence="nominal",
        )
        outcome = FetchOutcome(
            key=FIRMS.key,
            name=FIRMS.name,
            variables=FIRMS.variables,
            fetched_at=_START,
            ok=True,
            issued_at=_DETECTED_AT,
        )
        return FetchResult(make_conditions(), (outcome,), fires=(fire,))


def _firms_service(
    delivery: RecordingDelivery,
    *,
    firms: dict[str, str] | None,
    providers: tuple[ProviderInfo, ...] = _PROVIDERS,
) -> Service:
    config = AppConfig.model_validate(
        {
            "mqtt": make_mqtt_config(),
            "recompute": RecomputeConfig(interval_seconds=10),
            "piers": [
                make_pier("a").model_copy(update={"metar_station": "KBOS"}),
                make_pier("b"),
            ],
            "firms": firms,
        }
    )
    return Service(
        config,
        delivery,  # type: ignore[arg-type]
        FixedClock(_START),
        conditions_provider=_FirmsFetch(delivery.events),
        providers=providers,
    )


def test_startup_seeds_firms_health_for_every_pier_after_metar() -> None:
    delivery = RecordingDelivery()
    _firms_service(delivery, firms={"map_key": "abc123secret"}).run(
        monotonic=ScriptedMonotonic([0.0]), max_iterations=0
    )

    assert delivery.events[:3] == [("health", "a"), ("health", "b"), ("online",)]
    seeded = dict(delivery.healths[:2])
    assert [h.key for h in seeded["a"]] == ["open_meteo", "seven_timer", "metar", "firms"]
    assert [h.key for h in seeded["b"]] == ["open_meteo", "seven_timer", "firms"]
    assert seeded["b"][-1] == ProviderHealth.empty(
        key="firms", name="FIRMS", variables=(), tracking_since=_START
    )


@pytest.mark.parametrize(
    "firms",
    [None, {"map_key": "${FIRMS_KEY}"}, {"map_key": ""}],
    ids=["no-block", "unset-variable", "empty-key"],
)
def test_no_usable_key_seeds_no_firms_health(firms: dict[str, str] | None) -> None:
    delivery = RecordingDelivery()
    _firms_service(delivery, firms=firms).run(monotonic=ScriptedMonotonic([0.0]), max_iterations=0)

    for _, healths in delivery.healths:
        assert "firms" not in [h.key for h in healths]


def test_with_no_providers_a_firms_key_publishes_no_health() -> None:
    delivery = RecordingDelivery()
    _firms_service(delivery, firms={"map_key": "abc123secret"}, providers=()).run(
        monotonic=ScriptedMonotonic([0.0]), max_iterations=0
    )

    assert delivery.healths == []


def test_a_firms_outcome_folds_into_firms_health() -> None:
    delivery = RecordingDelivery()
    _firms_service(delivery, firms={"map_key": "abc123secret"}).run(
        monotonic=ScriptedMonotonic([0.0]), max_iterations=0
    )

    firms = dict(delivery.healths)["b"][-1]
    assert (firms.key, firms.status, firms.last_success, firms.issued_at) == (
        "firms",
        "ok",
        _START,
        _DETECTED_AT,
    )


def test_the_service_passes_the_fires_to_the_verdict() -> None:
    delivery = RecordingDelivery()
    _firms_service(delivery, firms={"map_key": "abc123secret"}).run(
        monotonic=ScriptedMonotonic([0.0]), max_iterations=0
    )

    for doc in delivery.documents:
        assert doc.reasons[-1].startswith("A satellite detected a fire 11 km N of the pier")
