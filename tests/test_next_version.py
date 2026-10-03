"""release-image: the next CalVer release version (design D2, ADR-0013)."""

from __future__ import annotations

import subprocess
from datetime import date
from pathlib import Path

import pytest
from next_version import main, next_version


@pytest.mark.parametrize(
    ("tags", "today", "expected"),
    [
        pytest.param([], date(2026, 10, 3), "2026.10.0", id="first-release-of-a-month"),
        pytest.param(
            ["2026.10.0", "2026.10.1"], date(2026, 10, 20), "2026.10.2", id="later-same-month"
        ),
        pytest.param(["2026.10.4"], date(2026, 11, 1), "2026.11.0", id="monthly-reset"),
        pytest.param(
            ["2026.10.9", "2026.10.10"], date(2026, 10, 20), "2026.10.11", id="numeric-counter"
        ),
        pytest.param(
            ["v1.0", "2026.10.x", "2026.010.5", "2026.10.07", "v2026.10.3"],
            date(2026, 10, 3),
            "2026.10.0",
            id="non-matching-tags-ignored",
        ),
    ],
)
def test_next_version(tags: list[str], today: date, expected: str) -> None:
    assert next_version(tags, today) == expected


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A scratch git repository with one commit, as the working directory."""
    _git(tmp_path, "init", "-q")
    _git(
        tmp_path,
        "-c",
        "user.name=t",
        "-c",
        "user.email=t@example.com",
        "commit",
        "-q",
        "--allow-empty",
        "-m",
        "init",
    )
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_cli_refuses_a_commit_already_released(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _git(repo, "tag", "2026.10.0")

    assert main(today=date(2026, 10, 20)) != 0
    assert "2026.10.0" in capsys.readouterr().err


def test_cli_prints_the_next_version(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _git(repo, "tag", "2026.10.0")
    _git(
        repo,
        "-c",
        "user.name=t",
        "-c",
        "user.email=t@example.com",
        "commit",
        "-q",
        "--allow-empty",
        "-m",
        "next",
    )

    assert main(today=date(2026, 10, 20)) == 0
    assert capsys.readouterr().out == "2026.10.1\n"
