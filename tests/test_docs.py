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
    [
        "id",
        "name",
        "type",
        "score",
        "window",
        "remaining_window",
        "max_altitude",
        "transit_time",
        "moon_separation",
    ],
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


def test_doc_explains_ranking_judges_the_rest_of_the_night(doc_text: str) -> None:
    # rank-remaining-night: once the night has started, the ranking judges what is left.
    assert "rest of the night" in doc_text
    assert "remaining_window" in doc_text


def test_readme_targets_row_lists_the_remaining_window() -> None:
    readme = (Path(__file__).resolve().parent.parent / "README.md").read_text(encoding="utf-8")
    row = next(line for line in readme.splitlines() if line.startswith("| `targets` |"))
    assert "`remaining_window`" in row
    assert "still judge the whole night" not in readme


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
        "from 4 hours before now to 72 hours ahead",
    ],
)
def test_the_air_quality_section_explains_its_variables(fact: str) -> None:
    section = _section(_README.read_text(encoding="utf-8"), "### Adding the air-quality forecast")
    assert fact in section


def test_the_model_limits_give_the_hours_each_model_is_asked_for() -> None:
    section = _section(_README.read_text(encoding="utf-8"), "### Choosing Open-Meteo models")
    assert "asks every model for the 4 hours before now and the 72 after" in section


@pytest.mark.parametrize("key", ["open_meteo_icon", "open_meteo_gfs", "open_meteo_ecmwf"])
def test_the_model_table_says_the_global_models_reach_past_3_days(key: str) -> None:
    section = _section(_README.read_text(encoding="utf-8"), "### Choosing Open-Meteo models")
    [row] = [line for line in section.splitlines() if line.startswith(f"| `{key}`")]
    assert row.endswith("| More than 3 days |")


# --------------------------------------------------------------------------- #
# open-meteo-ecmwf 1.7: the README lists the ECMWF model provider
# --------------------------------------------------------------------------- #


def test_the_model_table_says_ecmwf_covers_the_whole_world() -> None:
    section = _section(_README.read_text(encoding="utf-8"), "### Choosing Open-Meteo models")
    assert "| `open_meteo_ecmwf` | `ecmwf_ifs` | The whole world | More than 3 days |" in section


def test_the_configuration_table_counts_six_open_meteo_models() -> None:
    assert "the six Open-Meteo models below" in _conditions_row()


def test_the_water_vapour_sources_name_ecmwf() -> None:
    section = _section(_README.read_text(encoding="utf-8"), "### Computing transparency")
    [row] = [line for line in section.splitlines() if line.startswith("| `column_water_vapour`")]
    assert "`open_meteo_ecmwf`" in row


def test_the_seeing_section_says_why_ecmwf_does_not_declare_the_column() -> None:
    section = _section(_README.read_text(encoding="utf-8"), "### Computing seeing")
    assert "ECMWF sends no pressure-level temperatures or heights" in section


def test_the_health_topic_list_names_ecmwf() -> None:
    entities = _section(_README.read_text(encoding="utf-8"), "## 🏠 Home Assistant entities")
    health_rows = [line for line in entities.splitlines() if "_health" in line]
    assert health_rows
    assert all("open_meteo_ecmwf" in row for row in health_rows)


def test_the_clean_up_key_list_names_ecmwf() -> None:
    removing = _section(_README.read_text(encoding="utf-8"), "### Removing the entities")
    assert "`open_meteo_ecmwf`" in removing


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


# --------------------------------------------------------------------------- #
# open-meteo-run-times 2.1: the README says the model providers carry their run
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "fact",
    [
        "**The issue time is the model's latest run.**",
        "metadata",
        "`null`",
        "ICON global",
        "GFS 0.11°",
    ],
)
def test_the_model_section_says_the_issue_time_is_the_latest_run(fact: str) -> None:
    section = _section(_README.read_text(encoding="utf-8"), "### Choosing Open-Meteo models")
    assert fact in section
    assert "The issue time is the fetch time" not in section


def test_the_air_quality_section_no_longer_likens_itself_to_the_models() -> None:
    section = _section(_README.read_text(encoding="utf-8"), "### Adding the air-quality forecast")
    assert "As with the other Open-Meteo providers" not in section


def test_the_health_section_says_only_best_match_and_air_quality_stamp_the_fetch_time() -> None:
    health = _section(_README.read_text(encoding="utf-8"), "### Watching provider health")
    assert "Only `open_meteo` and `open_meteo_air_quality` stamp the fetch time" in health
    assert "This is true for each Open-Meteo model too" not in health
    assert "each Open-Meteo model" in health


# --------------------------------------------------------------------------- #
# open-meteo-ecmwf 1.8: the night-card Cloud range tip names ECMWF
# --------------------------------------------------------------------------- #

_NIGHT_CARD = _ROOT / "docs" / "night-card.md"


def _cloud_range_tip() -> str:
    text = _NIGHT_CARD.read_text(encoding="utf-8")
    start = text.index("- **The strip has no Cloud range row.**")
    return text[start : text.index("\n- **", start + 1)]


@pytest.mark.parametrize("example", ["`open_meteo_ecmwf`", "**Open-Meteo ECMWF health**"])
def test_the_night_card_cloud_range_tip_gives_ecmwf_as_its_example(example: str) -> None:
    assert example in _cloud_range_tip()


# --------------------------------------------------------------------------- #
# metar-reason 4.2: the README documents the METAR station and the observation
# --------------------------------------------------------------------------- #


def test_the_pier_settings_table_documents_metar_station() -> None:
    table = _section(_README.read_text(encoding="utf-8"), "## ⚙️ Configuration")
    [row] = [line for line in table.splitlines() if line.startswith("| `metar_station`")]
    assert "four" in row
    assert "reasons" in row


def test_the_verdict_document_table_documents_observation() -> None:
    document = _section(_README.read_text(encoding="utf-8"), "### The verdict document")
    [row] = [line for line in document.splitlines() if line.startswith("| `observation`")]
    for field in ("station", "observed_at", "cover", "clouds", "base_ft", "90 minutes"):
        assert field in row


# --------------------------------------------------------------------------- #
# metar-confidence 3.1: the README says the observation can lower confidence
# --------------------------------------------------------------------------- #


def _metar_station_row() -> str:
    table = _section(_README.read_text(encoding="utf-8"), "## ⚙️ Configuration")
    [row] = [line for line in table.splitlines() if line.startswith("| `metar_station`")]
    return row


def test_the_metar_station_row_says_a_cloudier_report_lowers_confidence() -> None:
    row = _metar_station_row()
    assert "lowers confidence" in row
    assert "It never changes the verdict, score or confidence." not in row


@pytest.mark.parametrize("fact", ["low and mid", "Open-Meteo", "NWS", "7Timer!"])
def test_the_metar_station_row_says_which_forecasts_the_check_needs(fact: str) -> None:
    assert fact in _metar_station_row()


def test_the_confidence_row_names_disagreement_and_the_airport_report() -> None:
    document = _section(_README.read_text(encoding="utf-8"), "### The verdict document")
    [row] = [line for line in document.splitlines() if line.startswith("| `confidence`")]
    assert "disagree" in row
    assert "airport reports more cloud" in row


# --------------------------------------------------------------------------- #
# met-norway-provider 1.10: the README documents the MET Norway provider
# --------------------------------------------------------------------------- #


def test_the_configuration_table_names_met_norway() -> None:
    assert "`met_norway`" in _conditions_row()


def test_the_health_topic_list_names_met_norway() -> None:
    entities = _section(_README.read_text(encoding="utf-8"), "## 🏠 Home Assistant entities")
    health_rows = [line for line in entities.splitlines() if "_health" in line]
    assert health_rows
    assert all("met_norway" in row for row in health_rows)


def test_the_health_sensor_list_names_met_norway_health() -> None:
    section = _section(_README.read_text(encoding="utf-8"), "### Watching provider health")
    assert "**MET Norway health**" in section


def test_the_clean_up_key_list_names_met_norway() -> None:
    section = _section(_README.read_text(encoding="utf-8"), "### Removing the entities")
    [paragraph] = [p for p in section.split("\n\n") if p.startswith("If you listed")]
    assert "`met_norway`" in paragraph


def test_the_metar_station_row_names_met_norway_among_the_layered_forecasts() -> None:
    row = _metar_station_row()
    assert "the Open-Meteo providers and MET Norway give" in row


@pytest.mark.parametrize(
    "fact",
    [
        "Nordic",
        "m/s",
        "km/h",
        "6-hourly",
        "72 hours",
        "`Expires`",
        "If-Modified-Since",
        "User-Agent",
    ],
)
def test_the_met_norway_section_explains_its_limits(fact: str) -> None:
    section = _section(_README.read_text(encoding="utf-8"), "### Adding MET Norway")
    assert fact in section


# --------------------------------------------------------------------------- #
# firms-nearby-fire 4.2: the README documents the FIRMS key, line and health
# --------------------------------------------------------------------------- #


def _readme() -> str:
    return _README.read_text(encoding="utf-8")


def test_the_configuration_table_documents_firms() -> None:
    table = _section(_readme(), "## ⚙️ Configuration")
    [row] = [line for line in table.splitlines() if line.startswith("| `firms`")]
    for fact in ("map_key", "${", "50 km", "24 hours", "nominal", "high", "every pier"):
        assert fact in row


def test_the_readme_shows_the_fire_line() -> None:
    table = _section(_readme(), "## ⚙️ Configuration")
    assert "A satellite detected a fire" in table


def test_the_entities_table_lists_firms_health() -> None:
    section = _section(_readme(), "## 🏠 Home Assistant entities")
    [row] = [line for line in section.splitlines() if line.startswith("| **FIRMS health**")]
    assert "firms" in row


@pytest.mark.parametrize("purpose", ["| Health discovery configs", "| Provider health state"])
def test_the_topic_lists_name_firms(purpose: str) -> None:
    section = _section(_readme(), "## 🏠 Home Assistant entities")
    [row] = [line for line in section.splitlines() if line.startswith(purpose)]
    assert "\\|metar\\|firms>" in row


def test_watching_provider_health_explains_firms() -> None:
    section = _section(_readme(), "### Watching provider health")
    assert "**FIRMS health**" in section
    assert "unexpected response" in section


# --------------------------------------------------------------------------- #
# later-night-dark-windows 2.4: the README documents the Night sensors
# --------------------------------------------------------------------------- #


def _entities() -> str:
    return _section(_README.read_text(encoding="utf-8"), "## 🏠 Home Assistant entities")


def _row(table: str, starts: str) -> str:
    [row] = [line for line in table.splitlines() if line.startswith(starts)]
    return row


def test_the_entity_table_has_a_night_row() -> None:
    row = _row(_entities(), "| **Night 2** to **Night 4**").lower()
    assert "dusk" in row
    assert "`dark_window`" in row
    assert "unknown" in row and "no astronomical darkness" in row
    assert "unavailable" in row and "does not reach" in row


def test_the_verdict_row_leaves_out_the_timeline_and_the_later_nights() -> None:
    row = _row(_entities(), "| **Verdict** (sensor)")
    assert "except `timeline` and `later_nights`" in row


def test_the_discovery_configs_list_the_nights() -> None:
    row = _row(_entities(), "| Discovery configs |")
    assert "night_<n>" in row


def test_the_topic_table_has_a_night_row() -> None:
    row = _row(_entities(), "| Night `<n>` (2 to 4) state and attributes |")
    assert "`pierpressure/<pier>/night_<n>/state`" in row
    assert "`.../night_<n>/attributes`" in row


def test_the_verdict_attributes_topic_leaves_out_the_later_nights() -> None:
    _row(_entities(), "| Verdict attributes (the document without `timeline` and `later_nights`) |")


def test_the_document_section_says_the_attributes_leave_out_the_later_nights() -> None:
    section = _section(_README.read_text(encoding="utf-8"), "### The verdict document")
    assert "every key except `timeline` and `later_nights`" in " ".join(section.split())


def test_the_document_table_has_a_later_nights_row() -> None:
    section = _section(_README.read_text(encoding="utf-8"), "### The verdict document")
    row = _row(section, "| `later_nights` |")
    assert "`dark_window`" in row and "Night 2" in row


def test_the_night_rows_attributes_hold_the_dark_window_moon_and_targets() -> None:
    row = _row(_entities(), "| **Night 2** to **Night 4**")
    assert "Its attributes hold that night's `dark_window`, `moon` and `targets`" in row


def test_the_later_nights_row_gives_each_entrys_shape() -> None:
    section = _section(_README.read_text(encoding="utf-8"), "### The verdict document")
    row = " ".join(_row(section, "| `later_nights` |").split())
    assert "`{ dark_window, moon, targets }`" in row
    assert "same shapes as the top-level fields" in row


def test_the_later_nights_row_says_when_the_moon_is_taken() -> None:
    section = _section(_README.read_text(encoding="utf-8"), "### The verdict document")
    row = " ".join(_row(section, "| `later_nights` |").split())
    assert "local solar midnight" in row


def test_the_later_nights_row_says_how_the_targets_are_ranked() -> None:
    section = _section(_README.read_text(encoding="utf-8"), "### The verdict document")
    row = " ".join(_row(section, "| `later_nights` |").split())
    assert "ranked over its whole dark window" in row


def test_the_clean_up_loop_lists_the_night_sensors() -> None:
    removing = _section(_README.read_text(encoding="utf-8"), "### Removing the entities")
    assert "sensor/pierpressure_backyard/night_{2..4}" in removing
