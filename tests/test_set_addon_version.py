"""ha-addon: the release moves the add-on to its new version (design D5)."""

from __future__ import annotations

from pathlib import Path

import pytest
from set_addon_version import main, set_version

CONFIG = """\
# A comment that mentions version: 1.0.0
name: PierPressure
version: "2026.10.0"
slug: pierpressure
environment:
  version: kept
"""


def test_replaces_only_the_version_line() -> None:
    updated = set_version(CONFIG, "2026.10.1")

    assert updated == CONFIG.replace('version: "2026.10.0"', 'version: "2026.10.1"')


def test_keeps_windows_line_endings() -> None:
    crlf = CONFIG.replace("\n", "\r\n")

    assert set_version(crlf, "2026.11.0") == crlf.replace("2026.10.0", "2026.11.0")


@pytest.mark.parametrize("version", ["v2026.10.1", "2026.10", "2026.010.1", "2026.10.01", ""])
def test_rejects_a_version_that_is_not_a_release_version(version: str) -> None:
    with pytest.raises(ValueError, match="YYYY.M.N"):
        set_version(CONFIG, version)


def test_rejects_a_file_with_no_version_line() -> None:
    with pytest.raises(ValueError, match="no top-level version"):
        set_version("name: PierPressure\n  version: nested\n", "2026.10.1")


def test_cli_rewrites_the_file_in_place(tmp_path: Path) -> None:
    config = tmp_path / "config.yaml"
    config.write_bytes(CONFIG.encode())

    assert main(["2026.10.1", str(config)]) == 0
    assert config.read_bytes() == CONFIG.replace("2026.10.0", "2026.10.1").encode()


@pytest.mark.parametrize(
    ("args", "content", "message"),
    [
        pytest.param(["2026.10"], CONFIG, "YYYY.M.N", id="bad-version"),
        pytest.param(["2026.10.1"], "name: PierPressure\n", "no top-level version", id="no-line"),
    ],
)
def test_cli_fails_with_a_message_and_leaves_the_file(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    args: list[str],
    content: str,
    message: str,
) -> None:
    config = tmp_path / "config.yaml"
    config.write_text(content)

    assert main([*args, str(config)]) != 0
    assert message in capsys.readouterr().err
    assert config.read_text() == content
