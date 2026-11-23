"""The Night 2 to Night 4 sensors (spec ha-delivery; later-night-dark-windows DD5).

Each sensor shows one entry of the document's ``later_nights``: its state is
that night's dusk, and its attributes hold the entry. A night the forecast does
not reach makes its sensor unavailable.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

import jsonschema
import pytest

from pierpressure.core.model import (
    DarkWindow,
    LaterNight,
    Moon,
    MoonPhase,
    Target,
    TargetWindow,
    VerdictDocument,
)
from pierpressure.core.sky import MAX_LATER_NIGHTS
from pierpressure.delivery.ha_schema import SENSOR_SCHEMA
from pierpressure.delivery.mqtt import (
    NIGHTS,
    PAYLOAD_OFFLINE,
    PAYLOAD_ONLINE,
    TIMELINE_SENSORS,
    MqttDelivery,
    availability_topic,
    build_night_discovery,
    discovery_topic,
    night_attributes,
    night_attributes_topic,
    night_state,
    night_state_topic,
    timeline_attributes_topic,
)

from .conftest import (
    FakeMqttClient,
    Published,
    make_document,
    make_later_nights,
    make_mqtt_config,
)

BASE = "pierpressure"
PREFIX = "homeassistant"


def _connected() -> tuple[MqttDelivery, FakeMqttClient]:
    client = FakeMqttClient()
    delivery = MqttDelivery(make_mqtt_config(), client=client)
    delivery.connect()
    delivery.go_online()
    return delivery, client


def _config_topic(night: int) -> str:
    return discovery_topic(PREFIX, "sensor", "backyard", f"night_{night}")


# --------------------------------------------------------------------------- #
# Discovery
# --------------------------------------------------------------------------- #


def test_the_nights_run_from_night_2_to_one_past_the_cores_maximum() -> None:
    assert list(NIGHTS) == list(range(2, MAX_LATER_NIGHTS + 2))
    assert list(NIGHTS) == [2, 3, 4]


@pytest.mark.parametrize("night", NIGHTS)
def test_night_topics_derive_from_the_pier_and_the_night(night: int) -> None:
    assert (
        night_state_topic(BASE, "backyard", night) == f"pierpressure/backyard/night_{night}/state"
    )
    assert (
        night_attributes_topic(BASE, "backyard", night)
        == f"pierpressure/backyard/night_{night}/attributes"
    )
    assert _config_topic(night) == (
        f"homeassistant/sensor/pierpressure_backyard/night_{night}/config"
    )


@pytest.mark.parametrize("night", NIGHTS)
def test_a_night_discovery_is_a_timestamp_sensor_on_the_pier_device(night: int) -> None:
    config = build_night_discovery("backyard", BASE, night)
    assert config["name"] == f"Night {night}"
    assert config["has_entity_name"] is True
    assert config["unique_id"] == f"pierpressure_backyard_night_{night}"
    assert config["device_class"] == "timestamp"
    assert config["state_topic"] == night_state_topic(BASE, "backyard", night)
    assert config["json_attributes_topic"] == night_attributes_topic(BASE, "backyard", night)
    assert config["icon"] == "mdi:weather-night"
    assert config["device"]["identifiers"] == ["pierpressure_backyard"]
    # Enabled by default: Home Assistant would hide a sensor announced as disabled.
    assert "enabled_by_default" not in config


@pytest.mark.parametrize("night", NIGHTS)
def test_a_night_needs_both_online_and_its_available_flag(night: int) -> None:
    config = build_night_discovery("backyard", BASE, night)
    assert config["availability_mode"] == "all"
    assert config["availability"] == [
        {
            "topic": availability_topic(BASE),
            "payload_available": PAYLOAD_ONLINE,
            "payload_not_available": PAYLOAD_OFFLINE,
        },
        {
            "topic": night_attributes_topic(BASE, "backyard", night),
            "value_template": "{{ 'online' if value_json.available else 'offline' }}",
        },
    ]


@pytest.mark.parametrize("night", NIGHTS)
def test_a_night_discovery_validates_against_the_sensor_schema(night: int) -> None:
    strict = {**SENSOR_SCHEMA, "additionalProperties": False}
    jsonschema.validate(build_night_discovery("backyard", BASE, night), strict)


@pytest.mark.parametrize("night", NIGHTS)
def test_each_publish_announces_the_night_retained(night: int) -> None:
    delivery, client = _connected()
    delivery.publish_verdict(make_document(later_nights=make_later_nights(1)))

    [config] = client.publishes_to(_config_topic(night))
    assert config.retain is True
    assert json.loads(config.payload) == build_night_discovery("backyard", BASE, night)


@pytest.mark.parametrize("night", NIGHTS)
def test_republishing_introduces_no_new_night_identity(night: int) -> None:
    delivery, client = _connected()
    delivery.publish_verdict(make_document(later_nights=make_later_nights(3)))
    delivery.publish_verdict(make_document())

    configs = client.publishes_to(_config_topic(night))
    assert len(configs) == 2
    assert {json.loads(p.payload)["unique_id"] for p in configs} == {
        f"pierpressure_backyard_night_{night}"
    }


# --------------------------------------------------------------------------- #
# State and attributes
# --------------------------------------------------------------------------- #

_NEXT_DUSK = datetime(2026, 9, 9, 20, 27, 57, tzinfo=UTC)
_NEXT_DAWN = datetime(2026, 9, 10, 3, 28, 2, tzinfo=UTC)
_MOON = Moon(illumination=0.0, phase=MoonPhase.NEW)
_MOON_JSON = {
    "illumination": 0.0,
    "phase": "new",
    "up_during_dark": None,
    "rise": None,
    "set": None,
}
_NEXT_NIGHT = LaterNight(dark_window=DarkWindow(start=_NEXT_DUSK, end=_NEXT_DAWN), moon=_MOON)
_NO_DARKNESS = LaterNight(dark_window=DarkWindow(start=None, end=None), moon=_MOON)


def _published(*documents: VerdictDocument) -> FakeMqttClient:
    delivery, client = _connected()
    for document in documents:
        delivery.publish_verdict(document)
    return client


def _last(client: FakeMqttClient, topic: str) -> Published:
    published = client.publishes_to(topic)
    assert published
    return published[-1]


def test_night_2_shows_the_next_dusk() -> None:
    client = _published(make_document(later_nights=[_NEXT_NIGHT]))
    state = _last(client, night_state_topic(BASE, "backyard", 2))
    assert (state.payload, state.retain) == ("2026-09-09T20:27:57+00:00", True)


def test_a_night_with_no_darkness_shows_unknown() -> None:
    client = _published(make_document(later_nights=[_NEXT_NIGHT, _NO_DARKNESS]))
    state = _last(client, night_state_topic(BASE, "backyard", 3))
    assert (state.payload, state.retain) == ("None", True)


def test_a_night_with_no_darkness_stays_available() -> None:
    client = _published(make_document(later_nights=[_NEXT_NIGHT, _NO_DARKNESS]))
    attributes = _last(client, night_attributes_topic(BASE, "backyard", 3))
    assert json.loads(attributes.payload) == {
        "available": True,
        "night": 3,
        "dark_window": {"start": None, "end": None},
        "moon": _MOON_JSON,
        "targets": [],
    }


def test_a_filled_night_carries_its_entry() -> None:
    client = _published(make_document(later_nights=[_NEXT_NIGHT]))
    attributes = _last(client, night_attributes_topic(BASE, "backyard", 2))
    assert attributes.retain is True
    assert attributes.payload == (
        '{"available": true, "night": 2, "dark_window": '
        '{"start": "2026-09-09T20:27:57Z", "end": "2026-09-10T03:28:02Z"}, '
        '"moon": {"illumination": 0.0, "phase": "new", "up_during_dark": null, '
        '"rise": null, "set": null}, "targets": []}'
    )


def _target(id_: str, name: str | None, score: int) -> Target:
    window = TargetWindow(start=_NEXT_DUSK, end=_NEXT_DAWN)
    return Target(
        id=id_,
        name=name,
        type="G",
        score=score,
        window=window,
        remaining_window=window,
        max_altitude=61.0,
        transit_time=datetime(2026, 9, 9, 23, 30, tzinfo=UTC),
        moon_separation=100.0,
    )


_RANKED_NIGHT = LaterNight(
    dark_window=DarkWindow(start=_NEXT_DUSK, end=_NEXT_DAWN),
    moon=Moon(
        illumination=0.02,
        phase=MoonPhase.NEW,
        up_during_dark=False,
    ),
    targets=[_target("NGC7394", None, 99), _target("NGC0224", "Andromeda Galaxy", 91)],
)


def test_a_filled_nights_attributes_hold_its_entry_in_order() -> None:
    document = make_document(later_nights=[_RANKED_NIGHT])
    client = _published(document)
    attributes = json.loads(_last(client, night_attributes_topic(BASE, "backyard", 2)).payload)
    entry = json.loads(document.to_json())["later_nights"][0]
    assert list(attributes) == ["available", "night", "dark_window", "moon", "targets"]
    assert attributes == {"available": True, "night": 2, **entry}
    assert [target["id"] for target in attributes["targets"]] == ["NGC7394", "NGC0224"]


def test_later_nights_targets_add_no_discovery_configuration() -> None:
    def configs(document: VerdictDocument) -> list[str]:
        client = _published(document)
        return [p.topic for p in client.published if p.topic.startswith(f"{PREFIX}/")]

    plain = make_document(later_nights=[_NEXT_NIGHT])
    ranked = make_document(later_nights=[_RANKED_NIGHT])
    assert configs(ranked) == configs(plain)


def test_a_ranked_nights_state_is_still_its_dusk() -> None:
    client = _published(make_document(later_nights=[_RANKED_NIGHT]))
    state = _last(client, night_state_topic(BASE, "backyard", 2))
    assert state.payload == "2026-09-09T20:27:57+00:00"


def test_a_night_the_forecast_does_not_reach_is_unavailable() -> None:
    client = _published(make_document(later_nights=[_NEXT_NIGHT]))
    for night in (3, 4):
        attributes = _last(client, night_attributes_topic(BASE, "backyard", night))
        assert attributes.retain is True
        assert json.loads(attributes.payload) == {"available": False, "night": night}


def test_a_night_the_forecast_does_not_reach_shows_unknown() -> None:
    client = _published(make_document(later_nights=[_NEXT_NIGHT]))
    for night in (3, 4):
        assert _last(client, night_state_topic(BASE, "backyard", night)).payload == "None"


def test_an_empty_list_makes_every_night_unavailable() -> None:
    client = _published(make_document())
    for night in NIGHTS:
        attributes = _last(client, night_attributes_topic(BASE, "backyard", night))
        assert json.loads(attributes.payload)["available"] is False


def test_a_shrinking_list_clears_the_later_nights() -> None:
    client = _published(
        make_document(later_nights=make_later_nights(3)),
        make_document(later_nights=make_later_nights(1)),
    )
    for night in (3, 4):
        state = _last(client, night_state_topic(BASE, "backyard", night))
        attributes = _last(client, night_attributes_topic(BASE, "backyard", night))
        assert (state.payload, state.retain) == ("None", True)
        assert attributes.retain is True
        assert json.loads(attributes.payload) == {"available": False, "night": night}


def test_the_nights_follow_the_timeline_sensors_in_order() -> None:
    delivery, client = _connected()
    delivery.publish_verdict(make_document(later_nights=make_later_nights(2)))
    topics = [p.topic for p in client.published]

    cloud_cover_max = topics.index(
        timeline_attributes_topic(BASE, "backyard", TIMELINE_SENSORS[-1].key)
    )
    expected = [
        topic
        for night in NIGHTS
        for topic in (
            _config_topic(night),
            night_state_topic(BASE, "backyard", night),
            night_attributes_topic(BASE, "backyard", night),
        )
    ]
    assert TIMELINE_SENSORS[-1].key == "cloud_cover_max"
    assert topics[cloud_cover_max + 1 : cloud_cover_max + 1 + len(expected)] == expected


def test_the_nights_come_before_the_narrative() -> None:
    client = FakeMqttClient()
    delivery = MqttDelivery(make_mqtt_config(), client=client, manage_narrative=True)
    delivery.connect()
    delivery.go_online()
    delivery.publish_verdict(make_document(), narrative="Clear tonight.")
    topics = [p.topic for p in client.published]

    narrative = topics.index(discovery_topic(PREFIX, "sensor", "backyard", "narrative"))
    assert topics.index(night_attributes_topic(BASE, "backyard", NIGHTS[-1])) < narrative


@pytest.mark.parametrize("night", [0, 1, MAX_LATER_NIGHTS + 2])
def test_a_night_outside_the_night_sensors_has_no_entry(night: int) -> None:
    document = make_document(later_nights=make_later_nights(MAX_LATER_NIGHTS))
    assert night_state(document, night) == "None"
    assert night_attributes(document, night) == {"available": False, "night": night}
