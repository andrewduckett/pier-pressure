"""dev-checks: what ``mise run check`` runs before a pull request.

The contract tests run the ``specs`` task's own command with the OpenSpec CLI
pinned in ``mise.toml``, against throwaway OpenSpec roots (design D3, D4). They
pin the behaviour the check relies on: strict mode fails a main spec with a
requirement over 500 characters. An OpenSpec update that stops doing so fails
here, on the update's pull request.
"""

from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import tomllib
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent
_TASKS = tomllib.loads((_ROOT / "mise.toml").read_text(encoding="utf-8"))["tasks"]

# Long enough for strict mode, so only a requirement's length can fail it.
_PURPOSE = "A throwaway capability that the spec-check contract tests validate."
_LONG_REQUIREMENT_WARNING = "Requirement text is very long (>500 characters)"


def _requirement(length: int) -> str:
    text = "The pier SHALL hold the mount steady."
    return text + " " + "x" * (length - len(text) - 2) + "."


def _write_spec(path: Path, requirement: str) -> None:
    path.parent.mkdir(parents=True)
    path.write_text(
        f"# {path.parent.name} Specification\n\n"
        f"## Purpose\n{_PURPOSE}\n\n"
        "## Requirements\n"
        f"### Requirement: The pier holds the mount\n{requirement}\n\n"
        "#### Scenario: The mount is on the pier\n"
        "- **WHEN** the mount is on the pier\n"
        "- **THEN** the pier holds it steady\n",
        encoding="utf-8",
    )


def _openspec_root(tmp_path: Path, main_requirement: str) -> Path:
    root = tmp_path / "project"
    _write_spec(root / "openspec" / "specs" / "demo" / "spec.md", main_requirement)
    (root / "openspec" / "config.yaml").write_text("schema: spec-driven\n", encoding="utf-8")
    return root


def _require_openspec() -> None:
    """Skip without the OpenSpec CLI, except in CI, which must never pass by skipping."""
    if shutil.which("openspec") is not None:
        return
    reason = "openspec is not on PATH; run the tests with `mise run test`"
    if os.environ.get("CI"):
        pytest.fail(reason)
    pytest.skip(reason)


def _run_spec_check(root: Path, tmp_path: Path) -> subprocess.CompletedProcess[str]:
    _require_openspec()
    command = shlex.split(_TASKS["specs"]["run"])
    # A copy of the environment keeps PATH, so openspec and Node are found.
    env = os.environ | {
        "OPENSPEC_TELEMETRY": "0",
        "OPENSPEC_NO_UPDATE_CHECK": "1",
        "XDG_CONFIG_HOME": str(tmp_path / "config"),
    }
    return subprocess.run(
        command, cwd=root, env=env, capture_output=True, text=True, timeout=60, check=False
    )


def test_spec_check_fails_a_requirement_over_500_characters(tmp_path: Path) -> None:
    root = _openspec_root(tmp_path, _requirement(501))

    result = _run_spec_check(root, tmp_path)

    # OpenSpec names the spec and the warning on standard error.
    output = result.stdout + result.stderr
    assert result.returncode != 0
    assert "spec/demo" in output
    assert _LONG_REQUIREMENT_WARNING in output


def test_spec_check_passes_requirements_within_500_characters(tmp_path: Path) -> None:
    root = _openspec_root(tmp_path, _requirement(500))

    result = _run_spec_check(root, tmp_path)

    assert result.returncode == 0, result.stdout + result.stderr


def test_spec_check_ignores_a_change_in_progress(tmp_path: Path) -> None:
    root = _openspec_root(tmp_path, _requirement(500))
    change = root / "openspec" / "changes" / "longer-pier"
    delta = change / "specs" / "demo" / "spec.md"
    delta.parent.mkdir(parents=True)
    (change / ".openspec.yaml").write_text("schema: spec-driven\n", encoding="utf-8")
    delta.write_text(
        "## ADDED Requirements\n\n"
        f"### Requirement: The pier holds a second mount\n{_requirement(501)}\n\n"
        "#### Scenario: Two mounts are on the pier\n"
        "- **WHEN** two mounts are on the pier\n"
        "- **THEN** the pier holds both steady\n",
        encoding="utf-8",
    )

    result = _run_spec_check(root, tmp_path)

    assert result.returncode == 0, result.stdout + result.stderr


def test_missing_openspec_skips_off_ci(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PATH", str(tmp_path))
    monkeypatch.delenv("CI", raising=False)

    with pytest.raises(pytest.skip.Exception):
        _require_openspec()


def test_missing_openspec_fails_in_ci(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PATH", str(tmp_path))
    monkeypatch.setenv("CI", "true")

    with pytest.raises(pytest.fail.Exception):
        _require_openspec()
