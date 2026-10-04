"""Set the Home Assistant add-on's version (design D5).

The release workflow runs this after it publishes an image, to move
``ha-addon/config.yaml`` to the new release. Only the top-level ``version:`` line
value changes; every other byte of the file, including a trailing comment on that
line, stays as it was. Uses only the standard
library, so the release workflow can run it with any Python 3.12.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from next_version import RELEASE_TAG

DEFAULT_CONFIG = Path("ha-addon/config.yaml")

# The top-level key only: an indented `version:` belongs to some other mapping.
# Matches the key and its value (quoted or bare), not any comment after it.
VERSION_VALUE = re.compile(
    r"""^(version:[ \t]*)(?:"[^"\r\n]*"|'[^'\r\n]*'|[^\s#]+)""", re.MULTILINE
)


def set_version(text: str, version: str) -> str:
    """Return ``text`` with its top-level ``version:`` line set to ``version``.

    Raises ``ValueError`` if ``version`` is not a release version, or if ``text``
    has no top-level ``version:`` line.
    """
    if not RELEASE_TAG.fullmatch(version):
        raise ValueError(f"{version!r} is not a release version (YYYY.M.N)")
    # Quoted, so YAML reads 2026.10 style versions as strings, not floats.
    updated, count = VERSION_VALUE.subn(rf'\g<1>"{version}"', text, count=1)
    if count == 0:
        raise ValueError("the add-on config has no top-level version: line")
    return updated


def main(argv: list[str] | None = None) -> int:
    """Rewrite the add-on config in place: ``set_addon_version.py VERSION [PATH]``."""
    args = sys.argv[1:] if argv is None else argv
    if len(args) not in (1, 2):
        print("usage: set_addon_version.py VERSION [PATH]", file=sys.stderr)
        return 2
    path = Path(args[1]) if len(args) == 2 else DEFAULT_CONFIG
    # newline="" turns off newline translation, so line endings stay as they were.
    with path.open(encoding="utf-8", newline="") as file:
        text = file.read()
    try:
        updated = set_version(text, args[0])
    except ValueError as exc:
        print(f"{path}: {exc}", file=sys.stderr)
        return 1
    path.write_text(updated, encoding="utf-8", newline="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
