"""Offline guard for tests (design D6).

A context manager that makes any real network attempt raise, so tests can prove
the core computes verdicts fully offline. It blocks *connection establishment*
(``getaddrinfo``/``create_connection``/``socket.connect``) rather than replacing
the ``socket`` class — ``ssl.SSLSocket`` subclasses ``socket.socket``, so
swapping the class out breaks unrelated imports. Creating a socket object is
allowed; using it to reach the network is not.
"""

from __future__ import annotations

import socket
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any


class NetworkAccessError(RuntimeError):
    """Raised when code under :func:`no_network` attempts network access."""


@contextmanager
def no_network() -> Iterator[None]:
    """Block outbound network access for the duration of the ``with`` block."""

    def _blocked(*_args: Any, **_kwargs: Any) -> Any:
        raise NetworkAccessError("network access attempted under the offline guard")

    saved_getaddrinfo = socket.getaddrinfo
    saved_create_connection = socket.create_connection
    saved_connect = socket.socket.connect
    saved_connect_ex = socket.socket.connect_ex

    socket.getaddrinfo = _blocked  # type: ignore[assignment]
    socket.create_connection = _blocked  # type: ignore[assignment]
    socket.socket.connect = _blocked  # type: ignore[assignment,method-assign]
    socket.socket.connect_ex = _blocked  # type: ignore[assignment,method-assign]
    try:
        yield
    finally:
        socket.getaddrinfo = saved_getaddrinfo  # type: ignore[assignment]
        socket.create_connection = saved_create_connection  # type: ignore[assignment]
        socket.socket.connect = saved_connect  # type: ignore[method-assign]
        socket.socket.connect_ex = saved_connect_ex  # type: ignore[method-assign]
