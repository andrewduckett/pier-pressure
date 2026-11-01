"""The night dashboard on the docs page stays pasteable and in step with the adapter.

Reads the one YAML block in ``docs/night-dashboard.md`` and checks what a test
can see without Home Assistant: it parses, it uses only core cards and
plotly-graph-card, and it names only entities and attributes the MQTT adapter
publishes (night-dashboard design DD7). How Home Assistant draws it is the
Docker check's job.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
import yaml

from pierpressure.conditions.open_meteo import OpenMeteoProvider
from pierpressure.conditions.seven_timer import SevenTimerProvider
from pierpressure.core.model import Target, TargetWindow
from pierpressure.delivery.mqtt import (
    RANKS,
    TIMELINE_SENSORS,
    build_health_discovery,
    build_narrative_discovery,
    build_rank_target_discovery,
    build_refresh_discovery,
    build_score_discovery,
    build_timeline_discovery,
    build_top_target_discovery,
    build_verdict_discovery,
    health_attributes,
    narrative_attributes,
    rank_target_attributes,
    timeline_attributes,
    top_target_attributes,
)
from pierpressure.health import ProviderHealth

from .conftest import make_document

_ROOT = Path(__file__).resolve().parent.parent
_PAGE = _ROOT / "docs" / "night-dashboard.md"

_YAML_FENCE = re.compile(r"^```yaml\n(.*?)^```", re.MULTILINE | re.DOTALL)

# The core cards the dashboard uses, plus the one custom card it allows.
_ALLOWED_CARD_TYPES = frozenset(
    {"grid", "heading", "markdown", "entities", "vertical-stack", "custom:plotly-graph"}
)


def dashboard_yaml(page: str) -> str:
    blocks = _YAML_FENCE.findall(page)
    assert len(blocks) == 1, f"expected one ```yaml block, found {len(blocks)}"
    return str(blocks[0])


def iter_cards(dashboard: dict[str, Any]) -> Iterator[dict[str, Any]]:
    """Every card in the dashboard, including those nested in stacks and grids."""

    def walk(cards: list[dict[str, Any]]) -> Iterator[dict[str, Any]]:
        for card in cards:
            yield card
            yield from walk(card.get("cards", []))
            if "card" in card:
                yield from walk([card["card"]])

    for view in dashboard["views"]:
        yield from walk(view.get("cards", []))
        for section in view.get("sections", []):
            yield from walk(section.get("cards", []))


def _slug(name: str) -> str:
    """Home Assistant's entity id slug for the ASCII names PierPressure uses."""
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def _ranked_target(rank: int) -> Target:
    return Target(
        id=f"NGC{rank}",
        name=None,
        type="G",
        score=50,
        window=TargetWindow(
            start=datetime(2026, 9, 7, 21, tzinfo=UTC), end=datetime(2026, 9, 8, 2, tzinfo=UTC)
        ),
        max_altitude=60.0,
        transit_time=datetime(2026, 9, 7, 23, tzinfo=UTC),
        moon_separation=90.0,
    )


def published_entities(pier: str = "backyard") -> dict[str, frozenset[str]]:
    """Each entity id the adapter announces for ``pier``, with its attribute keys.

    Every rank holds a target, so the rank payloads carry ``window``. The Verdict
    has no attributes builder: the adapter publishes the document without
    ``timeline`` inline, so its keys come from the same call.
    """
    base = "pierpressure"
    document = make_document(pier=pier).model_copy(
        update={"targets": [_ranked_target(rank) for rank in RANKS]}
    )
    tracking = datetime(2026, 9, 7, 18, tzinfo=UTC)
    entries: list[tuple[str, dict[str, Any], dict[str, Any]]] = [
        (
            "sensor",
            build_verdict_discovery(pier, base),
            json.loads(document.model_dump_json(exclude={"timeline"})),
        ),
        ("sensor", build_score_discovery(pier, base), {}),
        ("button", build_refresh_discovery(pier, base), {}),
        ("sensor", build_top_target_discovery(pier, base), top_target_attributes(document)),
        ("sensor", build_narrative_discovery(pier, base), narrative_attributes("text")),
    ]
    entries += [
        (
            "sensor",
            build_rank_target_discovery(pier, base, rank),
            rank_target_attributes(document, rank),
        )
        for rank in RANKS
    ]
    entries += [
        (
            "sensor",
            build_timeline_discovery(pier, base, sensor),
            timeline_attributes(document, sensor.key),
        )
        for sensor in TIMELINE_SENSORS
    ]
    entries += [
        (
            "sensor",
            build_health_discovery(pier, base, provider.key, provider.name),
            health_attributes(
                ProviderHealth.empty(
                    key=provider.key, name=provider.name, role="base", tracking_since=tracking
                )
            ),
        )
        for provider in (OpenMeteoProvider, SevenTimerProvider)
    ]
    return {
        f"{domain}.{_slug(config['device']['name'] + ' ' + config['name'])}": frozenset(attrs)
        for domain, config, attrs in entries
    }


_ENTITY_ID = re.compile(r"\bsensor\.pierpressure_backyard_[a-z0-9_]*")
_JINJA_ATTR = re.compile(r"state_attr\(\s*['\"]([^'\"]+)['\"]\s*,\s*['\"]([^'\"]+)['\"]\s*\)")
_JS_ATTR = re.compile(r"\.attributes(?:\?\.|\.)([A-Za-z_]\w*)")


def _iter_nodes(node: Any) -> Iterator[Any]:
    yield node
    if isinstance(node, dict):
        for value in node.values():
            yield from _iter_nodes(value)
    elif isinstance(node, list):
        for item in node:
            yield from _iter_nodes(item)


def _strings(tree: Any) -> Iterator[str]:
    return (node for node in _iter_nodes(tree) if isinstance(node, str))


def entity_problems(tree: Any) -> list[str]:
    """A message for each ``sensor.pierpressure_backyard_*`` id the adapter does not announce."""
    known = published_entities()
    named = {match for text in _strings(tree) for match in _ENTITY_ID.findall(text)}
    return [
        f"{entity} is not an entity the adapter announces"
        for entity in sorted(named - known.keys())
    ]


def attribute_problems(tree: Any) -> list[str]:
    """A message for each attribute read that the entity read from does not publish.

    Jinja ``state_attr`` and an ``entities`` row with ``type: attribute`` name
    their entity. A JavaScript ``.attributes`` read is paired with every
    PierPressure entity named in the same string, so each must publish the key,
    and a read with no such entity beside it is a problem in itself.
    """
    known = published_entities()
    reads: list[tuple[str, str]] = []
    problems: list[str] = []
    for node in _iter_nodes(tree):
        if isinstance(node, dict) and node.get("type") == "attribute" and "entity" in node:
            reads.append((str(node["entity"]), str(node["attribute"])))
        if not isinstance(node, str):
            continue
        reads += _JINJA_ATTR.findall(node)
        js_keys = _JS_ATTR.findall(node)
        entities = sorted(set(_ENTITY_ID.findall(node)))
        for key in js_keys:
            if not entities:
                problems.append(
                    f"attribute '{key}' is read with no PierPressure entity in the same expression"
                )
            reads += [(entity, key) for entity in entities]
    for entity, key in dict.fromkeys(reads):
        if entity in known and key not in known[entity]:
            problems.append(f"{entity} does not publish attribute '{key}'")
    return problems


@pytest.fixture(scope="module")
def dashboard() -> dict[str, Any]:
    parsed = yaml.safe_load(dashboard_yaml(_PAGE.read_text(encoding="utf-8")))
    assert isinstance(parsed, dict)
    return parsed


def test_page_yaml_parses_into_a_dashboard_with_a_view(dashboard: dict[str, Any]) -> None:
    assert isinstance(dashboard.get("views"), list) and dashboard["views"]


def test_page_with_two_yaml_blocks_is_rejected() -> None:
    page = "```yaml\na: 1\n```\n\n```yaml\nb: 2\n```\n"
    with pytest.raises(AssertionError, match="found 2"):
        dashboard_yaml(page)


def test_card_types_are_core_cards_or_plotly_graph(dashboard: dict[str, Any]) -> None:
    types = [card.get("type") for card in iter_cards(dashboard)]
    assert types
    assert [t for t in types if t not in _ALLOWED_CARD_TYPES] == []


def test_card_types_include_nested_cards() -> None:
    sample = {
        "views": [
            {
                "sections": [
                    {
                        "type": "grid",
                        "cards": [
                            {
                                "type": "vertical-stack",
                                "cards": [{"type": "custom:apexcharts-card"}],
                            }
                        ],
                    }
                ]
            }
        ]
    }
    assert [c["type"] for c in iter_cards(sample)] == ["vertical-stack", "custom:apexcharts-card"]


# --------------------------------------------------------------------------- #
# Entity ids and attribute reads (design DD7)
# --------------------------------------------------------------------------- #


def _problems_in(sample: str) -> list[str]:
    return entity_problems(yaml.safe_load(sample)) + attribute_problems(yaml.safe_load(sample))


def test_every_entity_id_is_announced(dashboard: dict[str, Any]) -> None:
    assert entity_problems(dashboard) == []


def test_every_attribute_read_is_published(dashboard: dict[str, Any]) -> None:
    assert attribute_problems(dashboard) == []


def test_published_entities_include_each_kind() -> None:
    entities = published_entities()
    assert "forecast" in entities["sensor.pierpressure_backyard_seeing"]
    assert "window" in entities["sensor.pierpressure_backyard_target_10"]
    assert "dark_window" in entities["sensor.pierpressure_backyard_verdict"]
    assert "timeline" not in entities["sensor.pierpressure_backyard_verdict"]
    assert "status" in entities["sensor.pierpressure_backyard_7timer_health"]
    assert "sensor.pierpressure_backyard_open_meteo_health" in entities


def test_unknown_entity_id_fails_naming_it() -> None:
    problems = _problems_in("content: \"{{ states('sensor.pierpressure_backyard_sky') }}\"")
    assert problems == ["sensor.pierpressure_backyard_sky is not an entity the adapter announces"]


def test_unpublished_jinja_attribute_fails_naming_entity_and_key() -> None:
    sample = "content: \"{{ state_attr('sensor.pierpressure_backyard_verdict', 'darkness') }}\""
    assert _problems_in(sample) == [
        "sensor.pierpressure_backyard_verdict does not publish attribute 'darkness'"
    ]


def test_published_jinja_attribute_passes() -> None:
    sample = "content: \"{{ state_attr('sensor.pierpressure_backyard_verdict', 'moon') }}\""
    assert _problems_in(sample) == []


def test_unpublished_entities_row_attribute_fails() -> None:
    sample = """
type: entities
entities:
  - type: attribute
    entity: sensor.pierpressure_backyard_target_1
    attribute: altitude
"""
    assert _problems_in(sample) == [
        "sensor.pierpressure_backyard_target_1 does not publish attribute 'altitude'"
    ]


def test_js_attribute_published_by_every_entity_passes() -> None:
    sample = (
        "z: $ex ['sensor.pierpressure_backyard_seeing', 'sensor.pierpressure_backyard_wind_gust']"
        ".map(id => hass.states[id]?.attributes?.forecast ?? [])"
    )
    assert _problems_in(sample) == []


def test_js_attribute_missing_from_one_entity_fails_naming_it() -> None:
    sample = (
        "x: $ex ['sensor.pierpressure_backyard_seeing', 'sensor.pierpressure_backyard_verdict']"
        ".map(id => hass.states[id].attributes.forecast)"
    )
    assert _problems_in(sample) == [
        "sensor.pierpressure_backyard_verdict does not publish attribute 'forecast'"
    ]


def test_js_attribute_with_no_entity_in_the_expression_fails() -> None:
    sample = "x: $ex vars.state.attributes?.forecast"
    assert _problems_in(sample) == [
        "attribute 'forecast' is read with no PierPressure entity in the same expression"
    ]
