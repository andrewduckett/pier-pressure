"""Section 5: the service wires the explainer and passes the narrative to delivery.

5.1 — the config-to-component construction: an enabled block wires a real
provider-backed explainer and a managing delivery; a disabled or absent block wires
the no-op explainer and a non-managing delivery. ``_publish`` computes the narrative
from the produced document and hands it to ``publish_verdict``.

5.2 — a failing explainer never blocks or delays delivery: the verdict is published
and the narrative entity resolves to unavailable.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime

from pierpressure.__main__ import build_delivery_and_explainer
from pierpressure.core.clock import FixedClock
from pierpressure.core.config import AppConfig, ExplainerConfig, RecomputeConfig
from pierpressure.delivery.mqtt import (
    MqttDelivery,
    narrative_attributes_topic,
    verdict_state_topic,
)
from pierpressure.explain import NarrativeExplainer, PromptInput, no_op_explainer
from pierpressure.service import Service

from .conftest import (
    FakeMqttClient,
    RecordingDelivery,
    ScriptedMonotonic,
    make_conditions,
    make_mqtt_config,
    make_pier,
)


def _app_config(explainer: ExplainerConfig | None = None) -> AppConfig:
    return AppConfig(
        mqtt=make_mqtt_config(),
        recompute=RecomputeConfig(interval_seconds=10),
        piers=[make_pier("backyard")],
        explainer=explainer,
    )


def _clear_sky_provider() -> object:
    return lambda _pier: make_conditions(cloud=5.0)


# --------------------------------------------------------------------------- #
# 5.1 — wiring
# --------------------------------------------------------------------------- #


def test_publish_computes_the_narrative_and_passes_it_to_delivery() -> None:
    delivery = RecordingDelivery()
    clock = FixedClock(datetime(2026, 9, 8, 14, 0, tzinfo=UTC))
    service = Service(
        _app_config(),
        delivery,  # type: ignore[arg-type]
        clock,
        conditions_provider=_clear_sky_provider(),  # type: ignore[arg-type]
        explainer=lambda _doc: "Tonight is a go.",
    )
    service.run(monotonic=ScriptedMonotonic([0.0]), max_iterations=0)

    assert delivery.documents  # a verdict was published
    assert delivery.narratives[0] == "Tonight is a go."


def test_default_service_passes_no_narrative() -> None:
    delivery = RecordingDelivery()
    service = Service(
        _app_config(),
        delivery,  # type: ignore[arg-type]
        FixedClock(datetime(2026, 9, 8, 14, 0, tzinfo=UTC)),
    )
    service.run(monotonic=ScriptedMonotonic([0.0]), max_iterations=0)
    assert delivery.narratives == [None]


def test_enabled_config_wires_a_real_explainer_and_managing_delivery() -> None:
    config = _app_config(
        ExplainerConfig(enabled=True, model="anthropic:claude-opus-5", api_key="k")
    )
    delivery, explainer = build_delivery_and_explainer(config)
    assert isinstance(explainer, NarrativeExplainer)
    assert delivery._manage_narrative is True


def test_disabled_config_wires_the_no_op_and_non_managing_delivery() -> None:
    delivery, explainer = build_delivery_and_explainer(_app_config(ExplainerConfig(enabled=False)))
    assert explainer is no_op_explainer
    assert delivery._manage_narrative is False


def test_absent_block_wires_the_no_op_and_non_managing_delivery() -> None:
    delivery, explainer = build_delivery_and_explainer(_app_config(None))
    assert explainer is no_op_explainer
    assert delivery._manage_narrative is False


# --------------------------------------------------------------------------- #
# 5.2 — a failing explainer never blocks the verdict
# --------------------------------------------------------------------------- #


@dataclass
class _RaisingProvider:
    def generate(self, prompt: PromptInput) -> str:
        raise RuntimeError("provider down")


def test_a_failing_explainer_still_publishes_the_verdict_and_marks_unavailable() -> None:
    client = FakeMqttClient()
    delivery = MqttDelivery(make_mqtt_config(), client=client, manage_narrative=True)
    delivery.connect()
    service = Service(
        _app_config(ExplainerConfig(enabled=True)),
        delivery,
        FixedClock(datetime(2026, 9, 8, 14, 0, tzinfo=UTC)),
        conditions_provider=_clear_sky_provider(),  # type: ignore[arg-type]
        explainer=NarrativeExplainer(_RaisingProvider()),
    )
    service.run(monotonic=ScriptedMonotonic([0.0]), max_iterations=0)

    # The verdict is delivered despite the explainer failure.
    assert client.publishes_to(verdict_state_topic("pierpressure", "backyard"))
    # The narrative entity resolves to unavailable (active unavailable publish).
    attrs = client.publishes_to(narrative_attributes_topic("pierpressure", "backyard"))
    assert attrs and json.loads(attrs[-1].payload)["available"] is False
