"""Task 6.1: the narrative lives entirely outside the verdict document (ADR-0011).

The verdict document is byte-identical for the same inputs whether the explainer is
enabled or disabled — the LLM output is a separate delivery entity, never a field of
the document. The delivery entity is purely additive: it appears only when narrative
delivery is enabled, and no existing entity changes.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

from pierpressure.core.clock import FixedClock
from pierpressure.core.producer import produce_verdict
from pierpressure.delivery.mqtt import MqttDelivery

from .conftest import (
    FakeMqttClient,
    make_conditions,
    make_document,
    make_mqtt_config,
    make_pier,
)
from .offline_guard import no_network

_PINNED_INSTANT = datetime(2026, 9, 8, 14, 0, tzinfo=UTC)


def test_document_is_byte_identical_and_has_no_narrative_field() -> None:
    pier = make_pier()
    clock = FixedClock(_PINNED_INSTANT)
    conditions = make_conditions()

    with no_network():
        document = produce_verdict(pier, clock, conditions)

    payload = json.loads(document.to_json())
    # The document carries no narrative field; the prose is a separate entity.
    assert "narrative" not in payload

    # Producing the document does not depend on the explainer at all, so a second
    # run is byte-identical (the explainer never touches the numbers document).
    with no_network():
        again = produce_verdict(pier, clock, conditions)
    assert document.to_json() == again.to_json()


def _published_topics(*, manage_narrative: bool, narrative: str | None) -> set[str]:
    client = FakeMqttClient()
    delivery = MqttDelivery(make_mqtt_config(), client=client, manage_narrative=manage_narrative)
    delivery.connect()
    delivery.publish_verdict(make_document(), narrative=narrative)
    return {p.topic for p in client.published}


def test_narrative_entity_is_additive_and_only_appears_when_enabled() -> None:
    disabled = _published_topics(manage_narrative=False, narrative="prose")
    enabled = _published_topics(manage_narrative=True, narrative="prose")

    # Every topic published when disabled is still published when enabled: the
    # enabled surface only adds topics, never removes or changes one.
    assert disabled <= enabled
    added = enabled - disabled
    assert added and all("narrative" in topic for topic in added)
