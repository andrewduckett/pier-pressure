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


# --------------------------------------------------------------------------- #
# nws-provider 4.1: the README documents the NWS provider
# --------------------------------------------------------------------------- #


def test_the_configuration_table_names_nws() -> None:
    table = _section(_README.read_text(encoding="utf-8"), "## ⚙️ Configuration")
    [row] = [line for line in table.splitlines() if line.startswith("| `conditions`")]
    assert "`nws`" in row


def test_the_health_topic_list_names_nws() -> None:
    entities = _section(_README.read_text(encoding="utf-8"), "## 🏠 Home Assistant entities")
    health_rows = [line for line in entities.splitlines() if "_health" in line]
    assert health_rows
    assert all("nws" in row for row in health_rows)


@pytest.mark.parametrize(
    "fact",
    [
        "United States only",
        "no low, mid or high split",
        "layers stay unavailable",
        "grid cell",
        "User-Agent",
        "timeline",
    ],
)
def test_the_nws_section_explains_its_limits(fact: str) -> None:
    section = _section(
        _README.read_text(encoding="utf-8"), "### Adding the National Weather Service"
    )
    assert fact in section


# --------------------------------------------------------------------------- #
# air-quality-provider 3.2: the README documents the air-quality provider
# --------------------------------------------------------------------------- #


def _conditions_row() -> str:
    table = _section(_README.read_text(encoding="utf-8"), "## ⚙️ Configuration")
    [row] = [line for line in table.splitlines() if line.startswith("| `conditions`")]
    return row


def test_the_configuration_table_names_the_air_quality_provider() -> None:
    assert "`open_meteo_air_quality`" in _conditions_row()


def test_the_configuration_table_gives_the_new_default_order() -> None:
    assert "`[open_meteo, seven_timer, open_meteo_air_quality, computed]`" in _conditions_row()


def test_the_example_shows_the_new_default_order() -> None:
    config = _section(_README.read_text(encoding="utf-8"), "## ⚙️ Configuration")
    assert "providers: [open_meteo, seven_timer, open_meteo_air_quality, computed]" in config


def test_the_health_topic_list_names_the_air_quality_provider() -> None:
    entities = _section(_README.read_text(encoding="utf-8"), "## 🏠 Home Assistant entities")
    health_rows = [line for line in entities.splitlines() if "_health" in line]
    assert all("open_meteo_air_quality" in row for row in health_rows)


@pytest.mark.parametrize(
    "fact",
    [
        "`aerosol_optical_depth`",
        "no unit",
        "`pm2_5`",
        "µg/m³",
        "The verdict does not read them directly",
        "timeline does not show them",
    ],
)
def test_the_air_quality_section_explains_its_variables(fact: str) -> None:
    section = _section(_README.read_text(encoding="utf-8"), "### Adding the air-quality forecast")
    assert fact in section


# --------------------------------------------------------------------------- #
# computed-transparency 4.1: the README documents the computed source
# --------------------------------------------------------------------------- #


def test_the_configuration_table_names_computed() -> None:
    assert "`computed`" in _conditions_row()


def test_the_health_topic_list_names_computed() -> None:
    entities = _section(_README.read_text(encoding="utf-8"), "## 🏠 Home Assistant entities")
    health_rows = [line for line in entities.splitlines() if "_health" in line]
    assert health_rows
    assert all("computed" in row for row in health_rows)


def test_the_clean_up_list_names_the_computed_health_sensor() -> None:
    removing = _section(_README.read_text(encoding="utf-8"), "### Removing the entities")
    assert "sensor/pierpressure_backyard/computed_health" in removing


@pytest.mark.parametrize(
    "fact",
    [
        "last in the default list",
        "ahead of `seven_timer`",
        "after `seven_timer`",
        "uncalibrated",
        "docs/decisions/0032-computed-transparency-estimates-extinction.md",
        "`column_water_vapour`",
        "`transparency: missing input: aerosol_optical_depth`",
        "`transparency: no hour has every input`",
    ],
)
def test_the_computed_section_explains_where_to_list_it(fact: str) -> None:
    section = _section(_README.read_text(encoding="utf-8"), "### Computing transparency")
    assert fact in section


# --------------------------------------------------------------------------- #
# computed-seeing 4.1: the README documents computed seeing
# --------------------------------------------------------------------------- #


def test_the_configuration_table_says_computed_gives_transparency_and_seeing() -> None:
    assert "computes transparency and seeing" in _conditions_row()


@pytest.mark.parametrize(
    "fact",
    [
        "`open_meteo`, `open_meteo_hrrr` or `open_meteo_gfs`",
        "HRDPS, RDPS and ICON",
        "boundary-layer height",
        "part of the column",
        "`seeing: no hour has every input`",
        "list `open_meteo_hrrr` or `open_meteo_gfs` first",
        "uncalibrated",
        "docs/decisions/0033-computed-seeing-sums-capped-penalties.md",
        "`seeing: missing input: seeing column`",
    ],
)
def test_the_computed_seeing_section_explains_its_models_and_limits(fact: str) -> None:
    section = _section(_README.read_text(encoding="utf-8"), "### Computing seeing")
    assert fact in section


@pytest.mark.parametrize(
    "fact",
    [
        "`transparency: missing input: aerosol_optical_depth`",
        "`seeing: missing input: seeing column`",
        "| `inputs` |",
        '`{"transparency": ["open_meteo", "open_meteo_air_quality"], "seeing": ["open_meteo"]}`',
    ],
)
def test_the_health_section_shows_the_computed_errors_and_inputs(fact: str) -> None:
    health = _section(_README.read_text(encoding="utf-8"), "### Watching provider health")
    assert fact in health
