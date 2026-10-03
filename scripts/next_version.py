"""Compute the next release version (design D2, ADR-0013).

Versions are monthly CalVer, ``YYYY.M.N``: the UTC year and month of the release,
and a counter ``N`` that starts at 0 each month. Uses only the standard library,
so the release workflow can run it with any Python 3.12.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from datetime import date

# Exactly YYYY.M.N with no prefix and no leading zeros.
RELEASE_TAG = re.compile(r"(?P<year>[1-9]\d{3})\.(?P<month>[1-9]\d?)\.(?P<n>0|[1-9]\d*)")


def next_version(tags: Iterable[str], today: date) -> str:
    """Return the version for a release on ``today``, given the existing tags."""
    counters = [
        int(match["n"])
        for match in (RELEASE_TAG.fullmatch(tag) for tag in tags)
        if match and int(match["year"]) == today.year and int(match["month"]) == today.month
    ]
    n = max(counters) + 1 if counters else 0
    return f"{today.year}.{today.month}.{n}"
