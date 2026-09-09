"""Task 1.2: the pytest offline-guard helper (design D6).

The guard blocks any real network attempt so the determinism/offline tests can
prove ``produce_verdict`` and the sky math never touch the network. It must
*not* block loading the pinned ephemeris and built-in timescale from local data.
"""

from __future__ import annotations

import socket

import pytest

from .offline_guard import NetworkAccessError, no_network


def test_create_connection_is_blocked_under_guard() -> None:
    with no_network(), pytest.raises(NetworkAccessError):
        socket.create_connection(("example.com", 80), timeout=1)


def test_socket_connect_is_blocked_under_guard() -> None:
    with no_network(), pytest.raises(NetworkAccessError):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("example.com", 80))


def test_getaddrinfo_is_blocked_under_guard() -> None:
    with no_network(), pytest.raises(NetworkAccessError):
        socket.getaddrinfo("example.com", 80)


def test_guard_is_lifted_after_the_block() -> None:
    # The guard restores the real socket API on exit; getaddrinfo for localhost
    # (no outbound traffic) works again.
    with no_network():
        pass
    assert socket.getaddrinfo("localhost", 80)


def test_ephemeris_and_timescale_load_offline_under_guard() -> None:
    import os

    from skyfield.api import load, load_file, wgs84
    from skyfield_data import get_skyfield_data_path

    with no_network():
        eph = load_file(os.path.join(get_skyfield_data_path(), "de421.bsp"))
        ts = load.timescale(builtin=True)
        t = ts.utc(2026, 9, 8, 21, 30)
        observer = eph["earth"] + wgs84.latlon(51.5, -0.12, elevation_m=30.0)
        alt, _, _ = observer.at(t).observe(eph["sun"]).apparent().altaz()

    assert alt.degrees < 0  # sun is below the horizon at this pinned instant
