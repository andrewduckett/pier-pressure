"""Keep a secret that travels in a URL out of every log record (firms-nearby-fire DD5).

FIRMS takes its key only in the request path, and httpx logs every request URL
at INFO and quotes it in its errors. A filter on each root handler sees every
record that propagates to the root, httpx's included; a filter on a logger
would not see its children's records.
"""

from __future__ import annotations

import logging

from pydantic import SecretStr

MASK = "**********"


class _MaskFilter(logging.Filter):
    """Replaces the key in a record's message, exception text and stack."""

    def __init__(self, key: str) -> None:
        super().__init__()
        self._key = key

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            message = record.getMessage()
        except Exception:  # noqa: BLE001 - a bad format string must not skip the mask
            message = f"{record.msg} {record.args}"
        # The message is final once masked: a formatter reads ``msg`` as it is.
        record.msg = self._mask(message)
        record.args = ()
        if record.exc_info and not record.exc_text:
            record.exc_text = logging.Formatter().formatException(record.exc_info)
        if record.exc_text:
            record.exc_text = self._mask(record.exc_text)
        if record.stack_info:
            record.stack_info = self._mask(record.stack_info)
        return True

    def _mask(self, text: str) -> str:
        return text.replace(self._key, MASK)


def mask_key(key: SecretStr) -> None:
    """Mask ``key`` in every record each handler now on the root logger handles.

    Call it after logging is set up and before the first request; a handler
    added later is not covered.
    """
    mask = _MaskFilter(key.get_secret_value())
    for handler in logging.getLogger().handlers:
        handler.addFilter(mask)
