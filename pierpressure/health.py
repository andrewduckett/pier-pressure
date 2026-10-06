"""Provider health: what each fetch did, and what that adds up to (design D2, D6).

A :class:`FetchOutcome` records one fetch from one provider. :func:`fold` folds it
into that provider's :class:`ProviderHealth`, which the service keeps in memory per
pier and delivery publishes beside the verdict. Nothing here is weather-specific, so
another kind of provider could report health the same way.

Health describes the edge of the system. The pure core never imports this module,
and the verdict never reads it.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from http import HTTPStatus
from typing import Literal

import httpx

Role = Literal["base", "secondary"]
Status = Literal["ok", "failed"]

# The error for a fetch that completed but returned nothing usable.
NO_READINGS = "no readings returned"


@dataclass(frozen=True)
class ProviderInfo:
    """Who a provider is: its stable key, its display name, and its role."""

    key: str
    name: str
    role: Role


@dataclass(frozen=True)
class FetchOutcome:
    """The result of one fetch from one provider.

    ``error`` is set only when the fetch failed; ``issued_at`` only when it
    succeeded and the provider gave an issue time for its data.
    """

    key: str
    name: str
    role: Role
    fetched_at: datetime
    ok: bool
    error: str | None = None
    issued_at: datetime | None = None


@dataclass(frozen=True)
class ProviderHealth:
    """A provider's health for one pier since the process started.

    ``tracking_since`` is when the service loop started, and stays fixed until a
    restart. ``last_success`` and ``issued_at`` survive a failed fetch; the latest
    ``status``, ``last_fetch``, and ``last_error`` describe only the latest fetch.
    """

    key: str
    name: str
    role: Role
    tracking_since: datetime
    status: Status | None = None
    last_fetch: datetime | None = None
    last_error: str | None = None
    last_success: datetime | None = None
    issued_at: datetime | None = None

    @classmethod
    def empty(cls, *, key: str, name: str, role: Role, tracking_since: datetime) -> ProviderHealth:
        """A provider with no fetch yet."""
        return cls(key=key, name=name, role=role, tracking_since=tracking_since)


def fold(previous: ProviderHealth, outcome: FetchOutcome) -> ProviderHealth:
    """Fold one fetch's outcome into a provider's health.

    A success sets the last success and its issue time and clears the error. A
    failure keeps the earlier success and its issue time and records the error.
    Either way, the outcome becomes the latest status and fetch time.
    """
    if outcome.ok:
        return replace(
            previous,
            status="ok",
            last_fetch=outcome.fetched_at,
            last_error=None,
            last_success=outcome.fetched_at,
            issued_at=outcome.issued_at,
        )
    return replace(
        previous,
        status="failed",
        last_fetch=outcome.fetched_at,
        last_error=outcome.error,
    )


def describe_error(exc: BaseException) -> str:
    """A short error description built only from safe parts (design D6).

    It never copies the exception's own text, or the reason phrase the server
    sent: either can hold the request URL or the pier's coordinates. An HTTP status
    error gives its type, status code, and that code's standard phrase; any other
    error gives its type alone.
    """
    kind = type(exc).__name__
    if isinstance(exc, httpx.HTTPStatusError):
        code = exc.response.status_code
        try:
            return f"{kind}: {code} {HTTPStatus(code).phrase}"
        except ValueError:
            return f"{kind}: {code}"
    return kind
