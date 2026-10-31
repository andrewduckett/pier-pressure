"""Tasks 3.1 and 3.2: the timeline and Cloud cover sensor are documented.

A light guard that the night-timeline page and the README keep covering the
points a dashboard author needs.
"""

from __future__ import annotations

from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent
_PAGE = _ROOT / "docs" / "night-timeline.md"
_README = _ROOT / "README.md"

# The timeline sensors besides Cloud cover (timeline-sensors).
_NEW_KEYS = (
    "cloud_low",
    "cloud_mid",
    "cloud_high",
    "wind_gust",
    "seeing",
    "transparency",
    "sun_altitude",
    "moon_altitude",
)
_NEW_NAMES = (
    "Cloud low",
    "Cloud mid",
    "Cloud high",
    "Wind gust",
    "Seeing",
    "Transparency",
    "Sun altitude",
    "Moon altitude",
)


@pytest.fixture
def page_text() -> str:
    return _PAGE.read_text(encoding="utf-8")


def test_page_exists() -> None:
    assert _PAGE.is_file()


@pytest.mark.parametrize(
    "phrase",
    [
        "timeline",
        "Cloud cover",
        "sensor.pierpressure_backyard_cloud_cover",
        "`forecast`",
        "`hour`",
        "interval_seconds",
        "recorder",
    ],
)
def test_page_names_the_sensor_and_its_attributes(page_text: str, phrase: str) -> None:
    assert phrase in page_text


def test_page_explains_why_the_verdict_attributes_leave_the_timeline_out(
    page_text: str,
) -> None:
    lowered = page_text.lower()
    assert "verdict" in lowered and "16 kib" in lowered


def test_page_has_an_apexcharts_example_reading_forecast(page_text: str) -> None:
    assert "custom:apexcharts-card" in page_text
    assert "attributes.forecast" in page_text


@pytest.fixture
def readme_text() -> str:
    return _README.read_text(encoding="utf-8")


def test_readme_lists_the_cloud_cover_entity(readme_text: str) -> None:
    assert "| **Cloud cover** (sensor) |" in readme_text
    assert "docs/night-timeline.md" in readme_text


def test_readme_no_longer_says_the_whole_document_is_in_the_verdict_attributes(
    readme_text: str,
) -> None:
    assert "The full verdict document is in its attributes." not in readme_text
    assert "| Verdict document | `pierpressure/<pier>/verdict/attributes`" not in readme_text


def test_readme_lists_the_cloud_cover_topics(readme_text: str) -> None:
    assert "`pierpressure/<pier>/cloud_cover/state`" in readme_text
    assert "`.../cloud_cover/attributes`" in readme_text
    assert "cloud_cover\\|" in readme_text or "\\|cloud_cover" in readme_text


def test_readme_labels_the_verdict_attributes_topic_without_timeline(readme_text: str) -> None:
    assert (
        "| Verdict attributes (the document without `timeline`) "
        "| `pierpressure/<pier>/verdict/attributes`" in readme_text
    )


def test_readme_documents_the_timeline_field(readme_text: str) -> None:
    assert "| `timeline` | list |" in readme_text
    assert "except `timeline`" in readme_text


def test_readme_removal_loop_clears_the_cloud_cover_entity(readme_text: str) -> None:
    assert "sensor/pierpressure_backyard/cloud_cover" in readme_text


def test_page_says_a_missing_hour_shows_unknown_and_keeps_the_forecast(page_text: str) -> None:
    assert "The sensor is unavailable when the current hour" not in page_text
    assert "`unknown`" in page_text


def test_readme_says_cloud_cover_shows_unknown(readme_text: str) -> None:
    assert "Unavailable when the current hour has no value." not in readme_text
    assert "Unknown when the current hour has no value" in readme_text


def test_page_apexcharts_example_guards_a_missing_forecast(page_text: str) -> None:
    # Home Assistant hides every attribute while the sensor is unavailable.
    assert "(entity.attributes.forecast ?? []).map(" in page_text


def test_page_does_not_document_an_available_attribute(page_text: str) -> None:
    # Home Assistant's MQTT integration strips an attribute named `available`.
    assert "`available` attribute" not in page_text


def test_readme_lists_the_new_timeline_sensors_in_one_row(readme_text: str) -> None:
    [row] = [line for line in readme_text.splitlines() if "**Cloud low**" in line]
    for name in _NEW_NAMES:
        assert f"**{name}**" in row


def test_readme_lists_the_new_timeline_sensor_topics(readme_text: str) -> None:
    [row] = [
        line
        for line in readme_text.splitlines()
        if line.startswith("| Timeline sensor state and forecast")
    ]
    assert "`pierpressure/<pier>/<var>/state`" in row
    assert "`.../<var>/attributes`" in row
    for key in _NEW_KEYS:
        assert f"`{key}`" in row


def test_readme_discovery_pattern_names_every_timeline_key(readme_text: str) -> None:
    [row] = [line for line in readme_text.splitlines() if line.startswith("| Discovery configs |")]
    for key in _NEW_KEYS:
        assert f"\\|{key}\\|" in row


@pytest.mark.parametrize("key", _NEW_KEYS)
def test_readme_removal_loop_clears_each_timeline_sensor(readme_text: str, key: str) -> None:
    assert f"sensor/pierpressure_backyard/{key} " in readme_text


def test_readme_says_the_timeline_rides_on_the_timeline_sensors(readme_text: str) -> None:
    [row] = [line for line in readme_text.splitlines() if line.startswith("| `timeline` | list |")]
    assert "Delivered on the Cloud cover sensor;" not in row
    assert "timeline sensors" in row


def _section(text: str, heading: str) -> str:
    """The body of the section under ``heading``, up to the next heading of its level."""
    level = heading.split(" ", 1)[0]
    body = text.split(f"\n{heading}\n", 1)[1]
    return body.split(f"\n{level} ", 1)[0]


@pytest.mark.parametrize("key", ("cloud_cover", *_NEW_KEYS))
def test_page_tables_each_timeline_sensor(page_text: str, key: str) -> None:
    section = _section(page_text, "## The timeline sensors")
    [row] = [line for line in section.splitlines() if f"`sensor.pierpressure_<pier>_{key}`" in line]
    assert row.startswith("|")


def test_page_tables_each_sensors_unit(page_text: str) -> None:
    section = _section(page_text, "## The timeline sensors")
    assert "| Entity id | Unit | State |" in section
    for unit in ("%", "km/h", "°"):
        assert f"| {unit} |" in section


def test_page_says_an_altitude_is_for_the_start_of_the_hour(page_text: str) -> None:
    lowered = " ".join(page_text.lower().split())
    assert "start of the current hour" in lowered
    assert "one hour plus one recompute interval" in lowered


def test_page_says_an_altitude_shows_unknown_with_no_source(page_text: str) -> None:
    section = " ".join(_section(page_text, "## The timeline sensors").lower().split())
    assert "the altitudes too" in section
    assert "no weather source returned the current hour" in section


def test_page_names_all_nine_sensors_in_the_verdict_section(page_text: str) -> None:
    section = _section(page_text, "## Why the Verdict sensor leaves the timeline out")
    assert "starting with Cloud cover" not in section
    for name in ("Cloud cover", *_NEW_NAMES):
        assert name in section


def test_page_recorder_example_lists_all_nine_entities(page_text: str) -> None:
    section = _section(page_text, "## Keep the forecast out of the recorder")
    for key in ("cloud_cover", *_NEW_KEYS):
        assert f"- sensor.pierpressure_backyard_{key}\n" in section
    assert "each pier has its own" in " ".join(section.lower().split())
