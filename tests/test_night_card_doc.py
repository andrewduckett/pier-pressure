"""The dashboard card's repository files: HACS, the release, and the docs page.

The card's own behaviour is tested in ``card/`` with Vitest (night-card design,
Test Seams). These tests read what HACS and the release workflow read.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
import yaml

_ROOT = Path(__file__).resolve().parent.parent
_CARD_FILE = "pierpressure-card.js"


def test_hacs_json_names_the_card_file() -> None:
    hacs = json.loads((_ROOT / "hacs.json").read_text(encoding="utf-8"))

    assert hacs["name"]
    assert hacs["filename"] == _CARD_FILE


def test_hacs_json_leaves_the_add_on_repository_file_in_place() -> None:
    assert (_ROOT / "repository.yaml").is_file()


_WORKFLOWS = _ROOT / ".github" / "workflows"


def _steps(workflow: str, job: str) -> list[dict[str, Any]]:
    loaded = yaml.safe_load((_WORKFLOWS / workflow).read_text(encoding="utf-8"))
    steps: list[dict[str, Any]] = loaded["jobs"][job]["steps"]
    return steps


def _index(steps: list[dict[str, Any]], match: Callable[[dict[str, Any]], bool]) -> int:
    found = [n for n, step in enumerate(steps) if match(step)]
    assert len(found) == 1, f"expected one matching step, found {len(found)}"
    return found[0]


def _runs(text: str) -> Callable[[dict[str, Any]], bool]:
    return lambda step: text in str(step.get("run", ""))


def _uses(prefix: str) -> Callable[[dict[str, Any]], bool]:
    return lambda step: str(step.get("uses", "")).startswith(prefix)


def _caches(path: str) -> Callable[[dict[str, Any]], bool]:
    return lambda step: _uses("actions/cache@")(step) and step["with"]["path"] == path


def test_release_builds_the_card_with_the_release_version() -> None:
    steps = _steps("release.yml", "release")
    card = steps[_index(steps, _runs("mise run card"))]

    assert card["env"]["PIERPRESSURE_VERSION"] == "${{ steps.version.outputs.version }}"


def test_release_builds_the_card_after_it_computes_the_version() -> None:
    steps = _steps("release.yml", "release")

    assert _index(steps, lambda step: step.get("id") == "version") < _index(
        steps, _runs("mise run card")
    )


def test_release_builds_the_card_with_mise_tools_installed() -> None:
    steps = _steps("release.yml", "release")

    assert _index(steps, _uses("jdx/mise-action@")) < _index(steps, _runs("mise run card"))


def test_release_builds_the_card_before_the_image() -> None:
    steps = _steps("release.yml", "release")

    assert _index(steps, _runs("mise run card")) < _index(steps, _uses("docker/build-push-action@"))


def test_release_attaches_the_card_to_the_github_release() -> None:
    steps = _steps("release.yml", "release")
    create = steps[_index(steps, _runs("gh release create"))]

    assert f"card/dist/{_CARD_FILE}" in create["run"]


@pytest.mark.parametrize(
    ("workflow", "job"), [("ci.yml", "check"), ("release.yml", "check"), ("release.yml", "release")]
)
def test_release_and_ci_jobs_cache_the_npm_packages(workflow: str, job: str) -> None:
    steps = _steps(workflow, job)
    cache = steps[_index(steps, _caches("~/.npm"))]

    assert "hashFiles('card/package-lock.json')" in cache["with"]["key"]


_PAGE = _ROOT / "docs" / "night-card.md"
_YAML_FENCE = re.compile(r"^```yaml\n(.*?)^```", re.MULTILINE | re.DOTALL)


def _page() -> str:
    return _PAGE.read_text(encoding="utf-8")


def test_docs_page_names_the_hacs_route() -> None:
    page = _page()

    assert "HACS" in page
    assert "**Dashboard**" in page
    assert "first release" in page


def test_docs_page_names_the_www_route() -> None:
    page = _page()

    assert "/config/www" in page
    assert "/local/pierpressure-card.js" in page
    assert "JavaScript module" in page


def test_docs_page_yaml_is_a_card_config() -> None:
    blocks = _YAML_FENCE.findall(_page())
    cards = [yaml.safe_load(block) for block in blocks]

    assert {"type": "custom:pierpressure-card", "pier": "backyard"} in cards


def test_docs_page_says_where_to_find_the_entity_id() -> None:
    page = _page()

    assert "sensor.pierpressure_<pier>_verdict" in page
    assert "**Settings** > **Entities**" in page


def test_docs_readme_links_the_page() -> None:
    readme = (_ROOT / "README.md").read_text(encoding="utf-8")

    assert "(docs/night-card.md)" in readme


def test_docs_strip_names_the_cloud_rows() -> None:
    page = _page()

    for row in ("Cloud cover", "Cloud low", "Cloud mid", "Cloud high"):
        assert f"**{row}**" in page
    assert "sensor.pierpressure_<pier>_cloud_cover" in page


def test_docs_strip_gives_the_axis_span() -> None:
    page = _page()

    assert "4 hours before dusk to 5 hours after dawn" in page
    assert "6 hours before now to 18 hours after" in page


@pytest.mark.parametrize("term", ["clear", "overcast", "blank", "hover", "time zone"])
def test_docs_strip_explains_what_it_shows(term: str) -> None:
    assert term in _page().lower()


def test_docs_night_axis_names_the_sun_and_moon_sensors() -> None:
    page = _page()

    assert "**Sun altitude**" in page
    assert "**Moon up**" in page
    assert "sensor.pierpressure_<pier>_sun_altitude" in page
    assert "sensor.pierpressure_<pier>_moon_altitude" in page


@pytest.mark.parametrize(
    "term",
    [
        "civil",
        "nautical",
        "astronomical",
        "start of the hour",
        "dusk",
        "dawn",
        "now",
        "every minute",
        "forecast",
    ],
)
def test_docs_night_axis_explains_what_it_shows(term: str) -> None:
    assert term in _page().lower()


def test_docs_night_axis_no_longer_promises_dusk_and_dawn_later() -> None:
    assert "Later releases add dusk, dawn" not in _page()


_ROWS = (
    "Sun altitude",
    "Moon altitude",
    "Cloud cover",
    "Cloud range",
    "Cloud low",
    "Cloud mid",
    "Cloud high",
    "Wind gust",
    "Seeing",
    "Transparency",
    "Temperature",
    "Dew point",
    "Humidity",
    "Wind speed",
    "Wind direction",
    "Rain chance",
)


@pytest.mark.parametrize("row", _ROWS)
def test_docs_rows_name_every_row(row: str) -> None:
    assert f"**{row}**" in _page()


@pytest.mark.parametrize(
    "sensor",
    [
        "sensor.pierpressure_<pier>_wind_gust",
        "sensor.pierpressure_<pier>_precipitation_probability",
    ],
)
def test_docs_rows_name_the_new_sensors(sensor: str) -> None:
    assert sensor in _page()


@pytest.mark.parametrize("term", ["darker means worse", "same scale", "hour before", "blows to"])
def test_docs_rows_explain_what_they_show(term: str) -> None:
    assert term in _page().lower()


def test_docs_rows_no_longer_promise_the_other_conditions_later() -> None:
    assert "Later releases add the other conditions" not in _page()


@pytest.mark.parametrize(
    "text",
    [
        "sensor.pierpressure_<pier>_target_1",
        "sensor.pierpressure_<pier>_target_10",
        "**Target 1**",
    ],
)
def test_docs_targets_name_the_sensors_and_lanes(text: str) -> None:
    assert text in _page()


@pytest.mark.parametrize("term", ["observable window", "no target tonight", "leaves no lane"])
def test_docs_targets_explain_what_they_show(term: str) -> None:
    assert term in _page().lower()


def test_docs_targets_give_the_hover_text() -> None:
    assert "Andromeda Galaxy from 21:00 to 02:00" in _page()


def test_docs_targets_say_the_lines_cross_them() -> None:
    page = _page()
    lines = page[page.index("Three lines cross the strip") : page.index("Hover over a line")]

    assert "target lanes" in " ".join(lines.split())


def test_docs_targets_named_in_the_opening() -> None:
    opening = _page().split("\n\n")[1]

    assert "ranked targets" in opening


_TROUBLESHOOTING = "## If something looks wrong"


def _before_troubleshooting() -> str:
    page = _page()
    return page[: page.index(_TROUBLESHOOTING)]


@pytest.mark.parametrize(
    "message", ["Not found", "Unavailable", "No forecast", "No astronomical darkness tonight"]
)
def test_docs_missing_strip_section_names_the_message(message: str) -> None:
    assert message in _before_troubleshooting()


@pytest.mark.parametrize(
    "text",
    [
        "sensor.pierpressure_<pier>_cloud_cover_min",
        "sensor.pierpressure_<pier>_cloud_cover_max",
        "No hour on the strip has cloud cover from two or more forecasts",
        "Cloud range, the hour from 21:00: 40% to 70%",
    ],
)
def test_docs_strip_section_covers_the_cloud_range_row(text: str) -> None:
    assert text in _before_troubleshooting()


@pytest.mark.parametrize("term", ["lowest", "highest", "disagree", "0% at the bottom"])
def test_docs_cloud_range_explains_what_it_shows(term: str) -> None:
    assert term in " ".join(_before_troubleshooting().split())


def test_docs_strip_section_says_when_the_cloud_range_row_is_left_out() -> None:
    paragraphs = _before_troubleshooting().split("\n\n")
    hover = "No hour on the strip has cloud cover from two or more forecasts"
    paragraph = " ".join(next(p for p in paragraphs if hover in " ".join(p.split())).split())

    assert "leaves the row out" in paragraph


def test_docs_no_longer_name_the_retired_cloud_range_message() -> None:
    assert "Needs two forecasts" not in _page()


def test_docs_first_verdict_note_says_the_cloud_range_row_is_left_out() -> None:
    paragraphs = _page().split("\n\n")
    note = next(p for p in paragraphs if "Before PierPressure's first verdict" in p)

    assert "no Cloud range row" in " ".join(note.split())


def test_docs_missing_paragraph_names_hover_and_the_moon_up_lane() -> None:
    paragraphs = _before_troubleshooting().split("\n\n")
    paragraph = " ".join(next(p for p in paragraphs if "No forecast" in p).split())

    assert ["hover" in paragraph.lower(), "Moon up" in paragraph] == [True, True]


def test_docs_missing_no_longer_leaves_an_empty_row_unexplained() -> None:
    assert "A row with no cells at all means" not in " ".join(_page().split())


def _troubleshooting() -> str:
    page = _page()
    section = page[page.index(_TROUBLESHOOTING) + len(_TROUBLESHOOTING) :]
    return section.split("\n## ", 1)[0]


@pytest.mark.parametrize(
    "shown",
    [
        "PierPressure is offline",
        "No PierPressure verdict found",
        "Not found",
        "Unavailable",
        "No forecast",
        "No astronomical darkness tonight",
    ],
)
def test_docs_wrong_section_says_what_to_do_for(shown: str) -> None:
    assert shown in _troubleshooting()


@pytest.mark.parametrize("where", ["health", "`providers`"])
def test_docs_wrong_section_says_where_to_look_for_a_missing_forecast(where: str) -> None:
    assert where in _troubleshooting()


def _troubleshooting_item(shown: str) -> str:
    """The list item of the troubleshooting section that starts with ``shown`` in bold."""
    items = re.split(r"\n(?=- \*\*)", _troubleshooting())
    return " ".join(next(item for item in items if item.startswith(f"- **{shown}")).split())


@pytest.mark.parametrize("term", ["`conditions`", "`providers`", "Open-Meteo", "health", "add-on"])
def test_docs_wrong_section_says_how_to_bring_back_the_cloud_range_row(term: str) -> None:
    assert term in _troubleshooting_item("The strip has no Cloud range row")


def _before_the_strip() -> str:
    page = _page()
    return " ".join(page[: page.index("### The night strip")].split())


@pytest.mark.parametrize(
    "text",
    [
        "**Moon**",
        "the Verdict sensor's `moon` attribute",
        "**Phase**",
        "**Illumination**",
        "**Moonrise**",
        "**Moonset**",
        "dark window",
    ],
)
def test_docs_moon_section_names_its_texts(text: str) -> None:
    assert text in _before_the_strip()


def test_docs_moon_section_says_what_a_dash_means() -> None:
    sentences = _before_the_strip().split(". ")

    assert any("dash" in s and "rise or set" in s for s in sentences)


def _moon_drawing_paragraphs() -> str:
    page = _page()
    section = page[page.index("### The Moon section") : page.index("### The night strip")]
    return " ".join(" ".join(p for p in section.split("\n\n") if "drawing" in p).split())


@pytest.mark.parametrize(
    "term",
    ["share", "waxing", "waning", "right", "left", "south", "Home Assistant", "other hemisphere"],
)
def test_docs_moon_section_says_how_to_read_the_drawing(term: str) -> None:
    assert term in _moon_drawing_paragraphs()


@pytest.mark.parametrize("phase", ["new moon", "full moon"])
def test_docs_moon_section_says_how_a_moon_with_no_side_is_drawn(phase: str) -> None:
    assert phase in _moon_drawing_paragraphs().lower()


def test_docs_moon_section_says_when_the_phase_is_for() -> None:
    sentences = _before_the_strip().split(". ")

    assert any("Phase" in s and "computed the verdict" in s for s in sentences)


def test_docs_moon_section_says_a_dash_on_a_night_with_no_darkness() -> None:
    sentences = _before_the_strip().split(". ")

    assert any("dash" in s and "No astronomical darkness tonight" in s for s in sentences)


def _section(heading: str) -> str:
    page = _page()
    section = page[page.index(heading) + len(heading) :]
    return section.split("\n## ", 1)[0]


@pytest.mark.parametrize("term", ["card picker", "**PierPressure**", "**Pier**", "type its id"])
def test_docs_editor_says_how_to_pick_the_pier(term: str) -> None:
    assert term in _section("## Add the card to a dashboard")


def test_docs_editor_keeps_the_yaml_route() -> None:
    assert "```yaml" in _section("## Add the card to a dashboard")


@pytest.mark.parametrize("term", ["**Pier**", "YAML"])
def test_docs_editor_says_the_list_already_uses_the_real_id(term: str) -> None:
    assert term in _section("## Find your pier's entity id")


@pytest.mark.parametrize(
    "term", ["drag", "swipe", "trackpad", "arrow keys", "**Back to tonight**", "scrolls the page"]
)
def test_docs_pan_names_the_inputs(term: str) -> None:
    assert term in _section("#### Panning the strip")


def test_docs_pan_says_the_strip_opens_on_the_judged_night() -> None:
    assert "opens on the judged night" in _section("#### Panning the strip")


def test_docs_pan_says_where_it_stops() -> None:
    assert "first and last forecast hour" in _section("#### Panning the strip")


def test_docs_pan_says_how_far_open_meteo_reaches() -> None:
    assert "Open-Meteo, for example, about three days" in _section("#### Panning the strip")


def test_docs_pan_says_other_nights_have_no_dusk_or_dawn() -> None:
    assert "no dusk line, dawn line or target bar" in _section("#### Panning the strip")


def test_docs_pan_no_forecast_names_a_later_night_as_a_cause() -> None:
    help_text = _section("## If something looks wrong")
    no_forecast = help_text[help_text.index('**A row says "No forecast".**') :]

    assert "later night" in no_forecast.split("\n- **", 1)[0]
