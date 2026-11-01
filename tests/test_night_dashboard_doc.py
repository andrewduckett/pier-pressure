"""The night dashboard on the docs page stays pasteable and in step with the adapter.

Reads the one YAML block in ``docs/night-dashboard.md`` and checks what a test
can see without Home Assistant: it parses, it uses only core cards and
plotly-graph-card, and it names only entities and attributes the MQTT adapter
publishes (night-dashboard design DD7). How Home Assistant draws it is the
Docker check's job.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
import yaml

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
