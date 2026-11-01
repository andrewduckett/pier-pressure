"""Task 7.1: the end-user target-ranking documentation exists and covers its points.

A light guard that the plain-language doc stays present and keeps covering each
field, the four ranking factors, the three reasons an object can be absent, and how
target ranking surfaces in Home Assistant.
"""

from __future__ import annotations

import ast
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


# --------------------------------------------------------------------------- #
# provider-order 4.1: the README and module docstrings describe the provider order
# --------------------------------------------------------------------------- #

_ROOT = Path(__file__).resolve().parent.parent
_README = _ROOT / "README.md"


def _section(text: str, heading: str) -> str:
    start = text.index(heading)
    end = text.find("\n#", start + len(heading))
    return text[start:] if end < 0 else text[start:end]


def test_the_configuration_table_documents_the_provider_list() -> None:
    table = _section(_README.read_text(encoding="utf-8"), "## ⚙️ Configuration")
    [row] = [line for line in table.splitlines() if line.startswith("| `conditions`")]
    assert "open_meteo" in row and "seven_timer" in row
    for case in ("empty", "unknown", "more than once", "no key"):
        assert case in row


def test_the_health_section_describes_variables_not_roles() -> None:
    health = _section(_README.read_text(encoding="utf-8"), "### Watching provider health")
    assert "| `variables` |" in health
    assert "`role`" not in health
    for word in ("base source", "secondary source"):
        assert word not in health


def test_how_it_is_built_says_providers_sit_in_an_ordered_list() -> None:
    built = _section(_README.read_text(encoding="utf-8"), "## 🏗️ How it is built")
    assert "ordered list" in built


@pytest.mark.parametrize(
    "module",
    [
        "pierpressure/conditions/__init__.py",
        "pierpressure/conditions/provider.py",
        "pierpressure/core/conditions.py",
    ],
)
def test_the_conditions_docstrings_describe_the_series_model(module: str) -> None:
    docstring = ast.get_docstring(ast.parse((_ROOT / module).read_text(encoding="utf-8")))
    assert docstring is not None
    text = docstring.lower()
    assert "series" in text
    for stale in ("base source", "secondary source", "group"):
        assert stale not in text
