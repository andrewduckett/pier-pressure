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
