"""The dashboard card's repository files: HACS, the release, and the docs page.

The card's own behaviour is tested in ``card/`` with Vitest (night-card design,
Test Seams). These tests read what HACS and the release workflow read.
"""

from __future__ import annotations

import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_CARD_FILE = "pierpressure-card.js"


def test_hacs_json_names_the_card_file() -> None:
    hacs = json.loads((_ROOT / "hacs.json").read_text(encoding="utf-8"))

    assert hacs["name"]
    assert hacs["filename"] == _CARD_FILE


def test_hacs_json_leaves_the_add_on_repository_file_in_place() -> None:
    assert (_ROOT / "repository.yaml").is_file()
