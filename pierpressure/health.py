"""Provider health: what each fetch did, and what that adds up to (design D2, D6).

A :class:`FetchOutcome` records one fetch from one provider. :func:`fold` folds it
into that provider's :class:`ProviderHealth`, which the service keeps in memory per
pier and delivery publishes beside the verdict. Nothing here is weather-specific, so
another kind of provider could report health the same way.

Health describes the edge of the system. The pure core never imports this module,
and the verdict never reads it.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from datetime import datetime
from http import HTTPStatus
from typing import Literal

import httpx

Status = Literal["ok", "failed"]

# The error for a fetch that completed but returned nothing usable.
NO_READINGS = "no readings returned"

# The error for a computed source whose inputs all have a series, but share no
# hour with a value in each (computed-transparency DD6).
NO_SHARED_HOUR = "no hour has every input"

# The error for computed seeing when any seeing-column variable has no filled
# series (computed-seeing DD5). The column is one bundle, so it is named whole.
MISSING_SEEING_COLUMN = "missing input: seeing column"


def missing_input(variables: tuple[str, ...]) -> str:
    """The error for a computed source with no filled series for these input keys.

    It is built from variable keys only, so it is safe like :func:`describe_error`.
    """
    return f"missing input: {', '.join(variables)}"


@dataclass(frozen=True)
class ProviderInfo:
    """Who a provider is: its stable key, its display name, and the variables it declares."""

    key: str
    name: str
    variables: tuple[str, ...]


@dataclass(frozen=True)
class FetchOutcome:
    """The result of one fetch from one provider.

    ``error`` is set when the fetch failed, and on a successful computed outcome
    when one of its variables failed. ``issued_at`` is set only when it succeeded
    and the provider gave an issue time for its data. ``inputs`` is set only on a
    successful computed outcome: the provider keys each computed variable read.
    """

    key: str
    name: str
    variables: tuple[str, ...]
    fetched_at: datetime
    ok: bool
    error: str | None = None
    issued_at: datetime | None = None
    inputs: Mapping[str, tuple[str, ...]] | None = None


@dataclass(frozen=True)
class ProviderHealth:
    """A provider's health for one pier since the process started.

    ``tracking_since`` is when the service loop started, and stays fixed until a
    restart. ``last_success``, ``issued_at`` and ``inputs`` survive a failed fetch;
    the latest ``status``, ``last_fetch``, and ``last_error`` describe only the
    latest fetch. Only the computed source's records carry ``inputs``.
    """

    key: str
    name: str
    variables: tuple[str, ...]
    tracking_since: datetime
    status: Status | None = None
    last_fetch: datetime | None = None
    last_error: str | None = None
    last_success: datetime | None = None
    issued_at: datetime | None = None
    inputs: Mapping[str, tuple[str, ...]] | None = None

    @classmethod
    def empty(
        cls, *, key: str, name: str, variables: tuple[str, ...], tracking_since: datetime
    ) -> ProviderHealth:
        """A provider with no fetch yet."""
        return cls(key=key, name=name, variables=variables, tracking_since=tracking_since)


def fold(previous: ProviderHealth, outcome: FetchOutcome) -> ProviderHealth:
    """Fold one fetch's outcome into a provider's health.

    A success sets the last success, its issue time and its inputs, and takes the
    outcome's error, which only a partly failed computation carries. A failure
    keeps the earlier success, its issue time and its inputs, and records the
    error. Either way, the outcome becomes the latest status and fetch time.
    """
    if outcome.ok:
        return replace(
            previous,
            status="ok",
            last_fetch=outcome.fetched_at,
            last_error=outcome.error,
            last_success=outcome.fetched_at,
            issued_at=outcome.issued_at,
            inputs=outcome.inputs,
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
