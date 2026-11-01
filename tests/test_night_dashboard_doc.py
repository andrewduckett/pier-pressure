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
from dashboard_check import PLOTLY_GRAPH_CARD_VERSION, dashboard_yaml

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

# The core cards the dashboard uses, plus the one custom card it allows.
_ALLOWED_CARD_TYPES = frozenset(
    {"grid", "heading", "markdown", "entities", "vertical-stack", "custom:plotly-graph"}
)


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


# Keys Home Assistant's MQTT integration drops from a JSON attributes payload
# (MQTT_ATTRIBUTES_BLOCKED in homeassistant/components/mqtt/entity.py, 2026.10).
# The Target sensors publish ``available``, but a dashboard never sees it.
_HA_BLOCKED_ATTRIBUTES = frozenset(
    {
        "available",
        "device_info",
        "entity_category",
        "entity_id",
        "entity_registry_enabled_default",
        "extra_state_attributes",
        "force_update",
        "should_poll",
        "state",
        "unique_id",
        "group_entities",
        "assumed_state",
        "device_class",
        "entity_picture",
        "friendly_name",
        "icon",
        "supported_features",
        "unit_of_measurement",
    }
)


def published_entities(pier: str = "backyard") -> dict[str, frozenset[str]]:
    """Each entity id the adapter announces for ``pier``, with the attribute keys HA keeps.

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
        f"{domain}.{_slug(config['device']['name'] + ' ' + config['name'])}": (
            frozenset(attrs) - _HA_BLOCKED_ATTRIBUTES
        )
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
    with pytest.raises(RuntimeError, match="found 2"):
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


# --------------------------------------------------------------------------- #
# The night strip (design DD1 to DD5)
# --------------------------------------------------------------------------- #

_ROW_LABELS = [
    "Sun altitude",
    "Moon altitude",
    "Cloud cover",
    "Cloud low",
    "Cloud mid",
    "Cloud high",
    "Wind gust",
    "Seeing",
    "Transparency",
]
# The reference rendering's seven blues, lightest to darkest (design DD2).
_RAMP = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
_ROW = re.compile(r'\["([^"]+)", "(sensor\.pierpressure_backyard_[a-z0-9_]+)"')


def strip_card(dashboard: dict[str, Any]) -> dict[str, Any]:
    cards = [c for c in iter_cards(dashboard) if c.get("type") == "custom:plotly-graph"]
    assert len(cards) == 1
    return cards[0]


def _traces(card: dict[str, Any], kind: str) -> list[dict[str, Any]]:
    return [e for e in card["entities"] if e.get("type") == kind]


def _trace_on(card: dict[str, Any], axis: str) -> dict[str, Any]:
    [trace] = [e for e in card["entities"] if e.get("yaxis") == axis]
    return trace


def test_strip_rows_are_the_nine_timeline_sensors_in_order(dashboard: dict[str, Any]) -> None:
    rows = _ROW.findall(strip_card(dashboard)["pier_timeline"])
    assert [label for label, _ in rows] == _ROW_LABELS
    assert [entity for _, entity in rows] == [
        f"sensor.pierpressure_backyard_{_slug(label)}" for label in _ROW_LABELS
    ]


def test_strip_rows_read_forecast_into_one_bar_trace(dashboard: dict[str, Any]) -> None:
    card = strip_card(dashboard)
    assert ".attributes?.forecast" in card["pier_timeline"]
    assert _traces(card, "heatmap") == []
    rows = _trace_on(card, "y")
    assert (rows["entity"], rows["type"], rows["orientation"]) == ("", "bar", "h")
    assert (rows["y"], rows["base"], rows["x"]) == (
        "$ex vars.strip.cells.map((c) => c.y)",
        "$ex vars.strip.cells.map((c) => c.base)",
        "$ex vars.strip.cells.map((c) => c.x)",
    )
    timeline = card["pier_timeline"]
    assert "y: label" in timeline
    assert "base: new Date(Date.parse(h) + trim)" in timeline
    assert "x: hour - 2 * trim" in timeline
    assert card["layout"]["yaxis"]["categoryarray"] == _ROW_LABELS


def test_strip_rows_trim_each_cell_and_leave_a_null_as_a_gap(dashboard: dict[str, Any]) -> None:
    card = strip_card(dashboard)
    timeline = card["pier_timeline"]
    assert "trim = 2 * 60 * 1000" in timeline
    # A null hour is dropped before the trace sees it, so it draws no bar and hover finds nothing.
    assert ".filter((h) => values[i].get(h) != null)" in timeline
    assert "no data" not in timeline
    assert "hoverongaps" not in _trace_on(card, "y")


def test_strip_rows_shade_on_the_seven_step_ramp(dashboard: dict[str, Any]) -> None:
    card = strip_card(dashboard)
    timeline = card["pier_timeline"]
    blues = re.search(r"const blues = \[([^\]]+)\]", timeline)
    assert blues is not None
    assert re.findall(r'"(#[0-9a-f]{6})"', blues.group(1)) == _RAMP
    assert "color: blues[band(v)]" in timeline
    assert _trace_on(card, "y")["marker"]["color"] == "$ex vars.strip.cells.map((c) => c.color)"


def test_strip_axis_spans_tonight_in_home_assistant_time(dashboard: dict[str, Any]) -> None:
    card = strip_card(dashboard)
    night = card["pier_night"]
    assert 'hass.states["sensor.pierpressure_backyard_verdict"]?.attributes?.dark_window' in night
    assert "vars.dusk.getTime() - 4 * hour" in night
    assert "vars.dawn.getTime() + 5 * hour" in night
    assert "vars.now.getTime() - 6 * hour" in night
    assert "vars.now.getTime() + 18 * hour" in night
    assert card["layout"]["xaxis"]["range"] == "$ex vars.range"
    assert card["time_zone"] == "server"
    assert card["refresh_interval"] == 300


def test_strip_axis_falls_back_when_either_end_of_the_dark_window_is_null(
    dashboard: dict[str, Any],
) -> None:
    night = strip_card(dashboard)["pier_night"]
    assert "vars.dusk = night.start && night.end ? new Date(night.start) : null" in night
    assert "vars.dawn = night.start && night.end ? new Date(night.end) : null" in night


def test_strip_lines_mark_dusk_dawn_and_now(dashboard: dict[str, Any]) -> None:
    card = strip_card(dashboard)
    assert "vars.now = new Date()" in card["pier_night"]
    shapes = card["layout"]["shapes"]
    assert "(vars.dusk ? [vars.dusk, vars.dawn] : [])" in shapes
    assert "x0: vars.now, x1: vars.now" in shapes
    annotations = card["layout"]["annotations"]
    for label in ('"dusk"', '"dawn"', '"now"'):
        assert label in annotations


def test_strip_lanes_read_every_rank_in_order(dashboard: dict[str, Any]) -> None:
    targets = strip_card(dashboard)["pier_targets"]
    assert re.findall(r'"(sensor\.pierpressure_backyard_target_\d+)"', targets) == [
        f"sensor.pierpressure_backyard_target_{rank}" for rank in RANKS
    ]
    # An unavailable rank has no attributes in Home Assistant, so no window and no lane.
    assert "t.state?.attributes?.window?.start && t.state?.attributes?.window?.end" in targets
    assert "label: t.state.state" in targets


def test_strip_lanes_put_moon_up_over_hours_above_the_horizon(dashboard: dict[str, Any]) -> None:
    card = strip_card(dashboard)
    assert "moon: hours.map((h) => [new Date(h), values[1].get(h)])" in card["pier_timeline"]
    lanes = card["pier_lanes"]
    assert "if (v == null || v <= 0) return;" in lanes
    assert 'vars.lanes = ["Moon up", ...vars.targets.map((t) => t.lane)];' in lanes


def test_strip_lanes_are_bars_on_their_own_axis(dashboard: dict[str, Any]) -> None:
    card = strip_card(dashboard)
    bars = _trace_on(card, "y2")
    assert (bars["type"], bars["orientation"]) == ("bar", "h")
    assert bars["base"] == "$ex vars.bars.map((b) => b.start)"
    yaxis2 = card["layout"]["yaxis2"]
    assert yaxis2["categoryarray"] == "$ex vars.lanes"
    assert yaxis2["overlaying"] == "free"


def test_strip_lanes_keep_one_height_whatever_their_number(dashboard: dict[str, Any]) -> None:
    card = strip_card(dashboard)
    assert "rowsPx + lanePx * vars.lanes.length" in card["pier_lanes"]
    assert card["layout"]["height"] == "$ex vars.height"
    assert card["layout"]["yaxis2"]["domain"] == "$ex [0, vars.split]"


def test_attribute_home_assistant_blocks_fails_even_when_published() -> None:
    sample = (
        "x: $ex ['sensor.pierpressure_backyard_target_1']"
        ".filter(id => hass.states[id]?.attributes?.available)"
    )
    assert _problems_in(sample) == [
        "sensor.pierpressure_backyard_target_1 does not publish attribute 'available'"
    ]


# --------------------------------------------------------------------------- #
# The cards around the strip (design DD6)
# --------------------------------------------------------------------------- #

_VERDICT = "sensor.pierpressure_backyard_verdict"


def _jinja_reads(card: dict[str, Any]) -> set[tuple[str, str]]:
    return set(_JINJA_ATTR.findall(str(card.get("content", ""))))


def test_view_is_a_sections_view(dashboard: dict[str, Any]) -> None:
    assert [view.get("type") for view in dashboard["views"]] == ["sections"]


def test_cards_include_a_tonight_card(dashboard: dict[str, Any]) -> None:
    wanted = {
        (_VERDICT, key) for key in ("verdict", "score", "confidence", "dark_window", "reasons")
    }
    markdown = [c for c in iter_cards(dashboard) if c.get("type") == "markdown"]
    assert any(wanted <= _jinja_reads(card) for card in markdown)


def test_cards_include_a_moon_card(dashboard: dict[str, Any]) -> None:
    markdown = [c for c in iter_cards(dashboard) if c.get("type") == "markdown"]
    moon = [card for card in markdown if (_VERDICT, "moon") in _jinja_reads(card)]
    assert moon
    content = moon[0]["content"]
    for field in ("moon.illumination", "moon.phase", "moon.rise", "moon.set"):
        assert field in content


def test_cards_include_a_target_table(dashboard: dict[str, Any]) -> None:
    tables = [c for c in iter_cards(dashboard) if c.get("type") == "entities"]
    listed = [
        [row["entity"] if isinstance(row, dict) else row for row in card["entities"]]
        for card in tables
    ]
    assert [f"sensor.pierpressure_backyard_target_{rank}" for rank in RANKS] in listed


def test_cards_include_health_chips(dashboard: dict[str, Any]) -> None:
    headings = [c for c in iter_cards(dashboard) if c.get("type") == "heading"]
    badges = {b.get("entity") for card in headings for b in card.get("badges", [])}
    assert {
        "sensor.pierpressure_backyard_open_meteo_health",
        "sensor.pierpressure_backyard_7timer_health",
    } <= badges


# --------------------------------------------------------------------------- #
# The page around the YAML
# --------------------------------------------------------------------------- #


@pytest.fixture(scope="module")
def page_before_yaml() -> str:
    page = _PAGE.read_text(encoding="utf-8")
    return page[: page.index("```yaml")]


def test_install_steps_come_before_the_yaml(page_before_yaml: str) -> None:
    assert "HACS" in page_before_yaml
    assert "Plotly Graph Card" in page_before_yaml


def test_install_steps_say_to_replace_the_pier_id(page_before_yaml: str) -> None:
    assert "replace `backyard`" in page_before_yaml.lower()


def test_links_from_the_readme_entity_section() -> None:
    readme = (_ROOT / "README.md").read_text(encoding="utf-8")
    start = readme.index("## 🏠 Home Assistant entities")
    section = readme[start : readme.index("\n### ", start)]
    assert "(docs/night-dashboard.md)" in section


def test_links_from_the_night_timeline_page() -> None:
    timeline = (_ROOT / "docs" / "night-timeline.md").read_text(encoding="utf-8")
    assert "(night-dashboard.md)" in timeline


def test_page_shows_a_screenshot_stored_in_docs_images() -> None:
    page = _PAGE.read_text(encoding="utf-8")
    images = re.findall(r"!\[[^\]]+\]\((images/[^)]+\.png)\)", page)
    assert images
    for image in images:
        assert (_PAGE.parent / image).is_file(), image


def test_page_names_the_versions_it_was_checked_against() -> None:
    compose = (_ROOT / "compose.yaml").read_text(encoding="utf-8")
    [ha_version] = re.findall(r"ghcr\.io/home-assistant/home-assistant:(\S+)", compose)
    page = " ".join(_PAGE.read_text(encoding="utf-8").split())
    assert f"Home Assistant {ha_version}" in page
    assert f"Plotly Graph Card {PLOTLY_GRAPH_CARD_VERSION}" in page


def test_install_steps_say_how_home_assistant_writes_the_pier_id(page_before_yaml: str) -> None:
    text = " ".join(page_before_yaml.split())
    assert "sensor.pierpressure_back_yard_verdict" in text


def test_strip_rows_hover_with_the_start_of_the_hour(dashboard: dict[str, Any]) -> None:
    card = strip_card(dashboard)
    [heatmap] = _traces(card, "heatmap")
    # x is the cell's centre, half an hour after the hour the value is for.
    assert "%{x" not in heatmap["hovertemplate"]
    assert "timeZone: hass.config.time_zone" in card["pier_timeline"]
    assert "clock.format(new Date(h))" in card["pier_timeline"]


def test_strip_lanes_are_hidden_without_a_timeline(dashboard: dict[str, Any]) -> None:
    # Offline, Home Assistant drops the forecast, and the strip shows no lane at all.
    yaxis2 = strip_card(dashboard)["layout"]["yaxis2"]
    assert yaxis2["visible"] == "$ex vars.strip.moon.length > 0"
