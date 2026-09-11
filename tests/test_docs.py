"""Task 7.1: the end-user target-ranking documentation exists and covers its points.

A light guard that the plain-language doc stays present and keeps covering each
field, the four ranking factors, the three reasons an object can be absent, and how
target ranking surfaces in Home Assistant.
"""

from __future__ import annotations

from pathlib import Path

import pytest

_DOC = Path(__file__).resolve().parent.parent / "docs" / "target-ranking.md"


def test_target_ranking_doc_exists() -> None:
    assert _DOC.is_file()


@pytest.fixture
def doc_text() -> str:
    return _DOC.read_text(encoding="utf-8").lower()


@pytest.mark.parametrize(
    "field",
    ["id", "name", "type", "score", "window", "max_altitude", "transit_time", "moon_separation"],
)
def test_doc_explains_each_target_field(doc_text: str, field: str) -> None:
    assert field.lower() in doc_text


@pytest.mark.parametrize(
    "factor", ["altitude", "window length", "moon separation", "transit timing"]
)
def test_doc_explains_the_four_ranking_factors(doc_text: str, factor: str) -> None:
    assert factor in doc_text


@pytest.mark.parametrize("reason", ["too faint", "never clears your horizon", "up too briefly"])
def test_doc_explains_why_an_object_may_be_absent(doc_text: str, reason: str) -> None:
    assert reason in doc_text


def test_doc_explains_home_assistant_surface(doc_text: str) -> None:
    assert "home assistant" in doc_text
    assert "top target" in doc_text
    assert "unavailable" in doc_text
