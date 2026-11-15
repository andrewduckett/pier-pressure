"""firms-nearby-fire 3.4: the FIRMS key is masked in every log record (design DD5).

Each test calls ``mask_key`` after pytest's ``caplog`` handler is on the root
logger, as ``main()`` calls it after ``basicConfig``.
"""

from __future__ import annotations

import io
import logging

import httpx
import pytest
from pydantic import SecretStr

from pierpressure.conditions.firms import FirmsFetcher
from pierpressure.core.config import PierConfig
from pierpressure.redact import MASK, mask_key

_KEY = "abc123secret"
_URL = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{_KEY}/VIIRS_NOAA20_NRT/x/2"
_PIER = PierConfig(id="north", latitude=60.0, longitude=10.0, elevation_m=0.0)

logger = logging.getLogger("tests.redact")


def _leaks(caplog: pytest.LogCaptureFixture) -> list[str]:
    """Every place a captured record still shows the key."""
    found = []
    for record in caplog.records:
        shown = [
            record.getMessage(),
            str(record.msg),
            repr(record.args),
            record.exc_text or "",
            record.stack_info or "",
        ]
        found.extend(text for text in shown if _KEY in text)
    if _KEY in caplog.text:
        found.append(caplog.text)
    return found


def test_mask_key_masks_the_message_and_clears_its_args(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.INFO):
        mask_key(SecretStr(_KEY))
        logger.info("fetching %s for %s", _URL, "north")
    (record,) = caplog.records
    assert record.args == ()
    assert record.getMessage() == f"fetching {_URL.replace(_KEY, MASK)} for north"
    assert MASK == "**********"
    assert _leaks(caplog) == []


def test_mask_key_masks_an_exception_that_quotes_the_url(
    caplog: pytest.LogCaptureFixture,
) -> None:
    request = httpx.Request("GET", _URL)
    error = httpx.HTTPStatusError(
        f"Client error '400 Bad Request' for url '{_URL}'",
        request=request,
        response=httpx.Response(400, request=request),
    )
    with caplog.at_level(logging.INFO):
        mask_key(SecretStr(_KEY))
        try:
            raise error
        except httpx.HTTPStatusError as exc:
            logger.exception("fetch failed: %s", exc)
    (record,) = caplog.records
    assert "HTTPStatusError" in caplog.text
    assert MASK in (record.exc_text or "")
    assert _leaks(caplog) == []


def test_mask_key_masks_the_stack_info(caplog: pytest.LogCaptureFixture) -> None:
    record = logger.makeRecord(
        logger.name, logging.INFO, __file__, 1, "here", (), None, sinfo=f"Stack: {_URL}"
    )
    with caplog.at_level(logging.INFO):
        mask_key(SecretStr(_KEY))
        logger.handle(record)
    assert caplog.records[0].stack_info == f"Stack: {_URL.replace(_KEY, MASK)}"
    assert _leaks(caplog) == []


def test_mask_key_masks_httpx_request_log(caplog: pytest.LogCaptureFixture) -> None:
    client = httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(400)))
    fetcher = FirmsFetcher(map_key=SecretStr(_KEY), client=client)
    with caplog.at_level(logging.INFO):
        mask_key(SecretStr(_KEY))
        with pytest.raises(httpx.HTTPStatusError) as raised:
            fetcher.fetch(_PIER)
        logger.warning("FIRMS failed: %s", raised.value, exc_info=raised.value)
    assert any(r.name == "httpx" and "HTTP Request" in r.getMessage() for r in caplog.records)
    assert _leaks(caplog) == []


def test_mask_key_covers_every_root_handler_present() -> None:
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    root = logging.getLogger()
    root.addHandler(handler)
    try:
        mask_key(SecretStr(_KEY))
        logging.getLogger("httpx").warning("GET %s", _URL)
    finally:
        root.removeHandler(handler)
    assert MASK in stream.getvalue()
    assert _KEY not in stream.getvalue()


def test_a_message_that_cannot_be_formatted_is_still_masked(
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level(logging.INFO):
        mask_key(SecretStr(_KEY))
        logger.info("two %s %s", _URL)
    (record,) = caplog.records
    assert record.args == ()
    assert _leaks(caplog) == []
