"""Provider health: the empty record, the fold rule, and safe error text (design D2, D6)."""

from __future__ import annotations

import json
from datetime import UTC, datetime

import httpx
import pytest

from pierpressure.health import FetchOutcome, ProviderHealth, describe_error, fold

_START = datetime(2026, 10, 5, 9, 0, tzinfo=UTC)
_FIRST = datetime(2026, 10, 5, 12, 0, tzinfo=UTC)
_SECOND = datetime(2026, 10, 5, 18, 0, tzinfo=UTC)
_ISSUED = datetime(2026, 10, 5, 11, 0, tzinfo=UTC)
_LATITUDE = "51.5"


def _empty() -> ProviderHealth:
    return ProviderHealth.empty(
        key="open_meteo", name="Open-Meteo", role="base", tracking_since=_START
    )


def _outcome(
    fetched_at: datetime,
    *,
    ok: bool,
    error: str | None = None,
    issued_at: datetime | None = None,
) -> FetchOutcome:
    return FetchOutcome(
        key="open_meteo",
        name="Open-Meteo",
        role="base",
        fetched_at=fetched_at,
        ok=ok,
        error=error,
        issued_at=issued_at,
    )


# --------------------------------------------------------------------------- #
# 1.1 an empty record has no history
# --------------------------------------------------------------------------- #


def test_an_empty_record_has_no_history() -> None:
    health = _empty()
    assert (health.key, health.name, health.role) == ("open_meteo", "Open-Meteo", "base")
    assert health.tracking_since == _START
    assert health.status is None
    assert health.last_fetch is None
    assert health.last_error is None
    assert health.last_success is None
    assert health.issued_at is None


# --------------------------------------------------------------------------- #
# 1.2 fold
# --------------------------------------------------------------------------- #


def test_a_success_sets_last_success_and_issue_time_and_clears_the_error() -> None:
    failed = fold(_empty(), _outcome(_FIRST, ok=False, error="ConnectError"))
    health = fold(failed, _outcome(_SECOND, ok=True, issued_at=_ISSUED))
    assert health.status == "ok"
    assert health.last_fetch == _SECOND
    assert health.last_success == _SECOND
    assert health.issued_at == _ISSUED
    assert health.last_error is None
    assert health.tracking_since == _START


def test_a_failure_keeps_the_earlier_success_and_sets_the_error() -> None:
    succeeded = fold(_empty(), _outcome(_FIRST, ok=True, issued_at=_ISSUED))
    health = fold(succeeded, _outcome(_SECOND, ok=False, error="ReadTimeout"))
    assert health.status == "failed"
    assert health.last_fetch == _SECOND
    assert health.last_success == _FIRST
    assert health.issued_at == _ISSUED
    assert health.last_error == "ReadTimeout"


def test_a_success_with_no_issue_time_gives_a_null_issue_time() -> None:
    succeeded = fold(_empty(), _outcome(_FIRST, ok=True, issued_at=_ISSUED))
    health = fold(succeeded, _outcome(_SECOND, ok=True, issued_at=None))
    assert health.last_success == _SECOND
    assert health.issued_at is None


def test_a_failure_with_no_earlier_success_leaves_the_success_unknown() -> None:
    health = fold(_empty(), _outcome(_FIRST, ok=False, error="ConnectError"))
    assert health.status == "failed"
    assert health.last_fetch == _FIRST
    assert health.last_success is None
    assert health.issued_at is None


# --------------------------------------------------------------------------- #
# 1.3 describe_error builds text from an allowlist only
# --------------------------------------------------------------------------- #

_URL = f"https://api.open-meteo.com/v1/forecast?latitude={_LATITUDE}&longitude=-0.12"


def _status_error(code: int, reason: str | None = None) -> httpx.HTTPStatusError:
    request = httpx.Request("GET", _URL)
    extensions = {"reason_phrase": reason.encode()} if reason is not None else {}
    response = httpx.Response(code, request=request, extensions=extensions)
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        return exc
    raise AssertionError("expected an HTTP status error")  # pragma: no cover


def test_an_http_status_error_gives_its_code_and_standard_phrase() -> None:
    assert describe_error(_status_error(503)) == "HTTPStatusError: 503 Service Unavailable"


def test_a_server_reason_phrase_is_never_copied() -> None:
    exc = _status_error(503, reason=f"Overloaded near {_LATITUDE}")
    assert _LATITUDE in str(exc)  # the raw message does carry it
    text = describe_error(exc)
    assert text == "HTTPStatusError: 503 Service Unavailable"
    assert _LATITUDE not in text


def test_an_unknown_status_code_gives_no_phrase() -> None:
    assert describe_error(_status_error(599)) == "HTTPStatusError: 599"


def test_a_connect_error_gives_its_type_only() -> None:
    exc = httpx.ConnectError(f"failed to reach {_URL}", request=httpx.Request("GET", _URL))
    assert describe_error(exc) == "ConnectError"


def test_a_value_error_holding_a_latitude_gives_its_type_only() -> None:
    assert describe_error(ValueError(f"bad latitude {_LATITUDE}")) == "ValueError"


@pytest.mark.parametrize(
    "exc",
    [json.JSONDecodeError("Expecting value", "51.5", 0), httpx.ReadTimeout("timed out")],
)
def test_other_errors_give_their_type_name(exc: Exception) -> None:
    assert describe_error(exc) == type(exc).__name__
