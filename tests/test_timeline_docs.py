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
