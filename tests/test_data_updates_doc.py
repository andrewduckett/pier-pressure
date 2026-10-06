"""The maintainer data-update runbook exists and covers its points (#27).

A light guard that the plain-language runbook stays present and keeps naming each
pinned dataset, the licence obligation the catalogue carries, the command that
regenerates the golden verdicts, and the tests that prove an update.
"""

from __future__ import annotations

from pathlib import Path

import pytest

_DOC = Path(__file__).resolve().parent.parent / "docs" / "data-updates.md"


def test_data_updates_doc_exists() -> None:
    assert _DOC.is_file()


@pytest.fixture
def doc_text() -> str:
    return _DOC.read_text(encoding="utf-8").lower()


@pytest.mark.parametrize("dataset", ["de421", "skyfield-data", "built-in timescale", "openngc"])
def test_doc_names_each_pinned_dataset(doc_text: str, dataset: str) -> None:
    assert dataset in doc_text


def test_doc_states_the_catalogue_licence_obligation(doc_text: str) -> None:
    assert "cc by-sa 4.0" in doc_text
    assert "notice" in doc_text


def test_doc_gives_the_golden_regeneration_command(doc_text: str) -> None:
    assert "pp_write_goldens=1 uv run pytest tests/test_golden_verdict.py" in doc_text


@pytest.mark.parametrize(
    "test_file",
    ["test_determinism.py", "test_golden_verdict.py", "test_catalog.py"],
)
def test_doc_names_the_tests_that_prove_an_update(doc_text: str, test_file: str) -> None:
    assert test_file in doc_text
