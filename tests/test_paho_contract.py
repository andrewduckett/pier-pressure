"""retry-broker-connection: pin the paho 2.1 behaviour the startup wait relies on.

The fake client in ``conftest.py`` plays paho's callbacks from a script. These
tests check that real paho behaves the way the script assumes (design Context,
D2, D3, D5). Each test plays the broker on one end of a ``socket.socketpair()``
and hands paho the other end, so nothing reaches the network.
"""

from __future__ import annotations

import socket
import threading
import time
from collections.abc import Iterator
from typing import Any

import paho.mqtt.client as mqtt
import pytest

from pierpressure.delivery.mqtt import LoginRejected, MqttDelivery

from .conftest import make_mqtt_config
from .offline_guard import no_network

# CONNACK packets for MQTT 3.1.1: type 0x20, length 2, no session, return code.
_CONNACK_ACCEPTED = b"\x20\x02\x00\x00"
_CONNACK_UNSUPPORTED_VERSION = b"\x20\x02\x00\x01"
_CONNACK_IDENTIFIER_REJECTED = b"\x20\x02\x00\x02"

_TIMEOUT_SECONDS = 5.0


class Broker:
    """Hands paho one socket per attempt, and keeps the broker's end of each."""

    def __init__(self) -> None:
        self.ends: list[socket.socket] = []
        self._replies: list[bytes | None] = []

    def expect(self, reply: bytes | None) -> None:
        """Queue the next attempt: reply with these bytes, or fail to open (``None``)."""
        self._replies.append(reply)

    def create_socket(self) -> socket.socket:
        reply = self._replies.pop(0)
        if reply is None:
            raise ConnectionRefusedError(111, "Connection refused")
        client_end, broker_end = socket.socketpair()
        broker_end.sendall(reply)
        self.ends.append(broker_end)
        return client_end

    def connect_packet(self, attempt: int) -> bytes:
        """Read the CONNECT packet paho sent on the given attempt (0-based)."""
        end = self.ends[attempt]
        end.settimeout(_TIMEOUT_SECONDS)
        return end.recv(1024)


@pytest.fixture
def broker(monkeypatch: pytest.MonkeyPatch) -> Iterator[Broker]:
    # loop_start builds a loopback socket pair with socket.connect, which the
    # offline guard blocks. A Unix socket pair needs no connect.
    monkeypatch.setattr(mqtt, "_socketpair_compat", socket.socketpair)
    fake = Broker()
    with no_network():
        yield fake
    for end in fake.ends:
        end.close()


def _paho_client(broker: Broker, **kwargs: Any) -> mqtt.Client:
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, **kwargs)  # type: ignore[attr-defined]
    client._create_socket = broker.create_socket  # type: ignore[method-assign]
    client.reconnect_delay_set(1, 1)
    return client


def _wait_until(condition: Any) -> bool:
    deadline = time.monotonic() + _TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        if condition():
            return True
        time.sleep(0.01)
    return False


def _connect_within_timeout(delivery: MqttDelivery) -> None:
    """Run ``delivery.connect`` on a worker, so a paho change fails the test, not hangs it."""
    outcome: list[BaseException | None] = []

    def run() -> None:
        try:
            delivery.connect()
        except BaseException as exc:  # noqa: BLE001 - handed back to the test
            outcome.append(exc)
        else:
            outcome.append(None)

    worker = threading.Thread(target=run, daemon=True)
    worker.start()
    worker.join(_TIMEOUT_SECONDS * 2)
    assert outcome, "connect() did not finish"
    if outcome[0] is not None:
        raise outcome[0]


def _protocol_name(connect: bytes) -> bytes:
    # Fixed header (1 byte + 1-byte length here), then a 2-byte length and the name.
    size = int.from_bytes(connect[2:4], "big")
    return connect[4 : 4 + size]


def _client_id(connect: bytes) -> bytes:
    # The client ID follows the protocol name, the level, the flags and keep-alive.
    start = 4 + len(_protocol_name(connect)) + 4
    size = int.from_bytes(connect[start : start + 2], "big")
    return connect[start + 2 : start + 2 + size]


def test_paho_keeps_its_network_thread_in_thread_while_running(broker: Broker) -> None:
    broker.expect(b"")
    client = _paho_client(broker)
    client.connect_async("broker.test", 1883)
    client.loop_start()
    try:
        assert client._thread is not None and client._thread.is_alive()
    finally:
        client.loop_stop()


def test_paho_tries_mqtt_3_1_at_once_after_an_unsupported_version(broker: Broker) -> None:
    broker.expect(_CONNACK_UNSUPPORTED_VERSION)
    broker.expect(b"")
    client = _paho_client(broker)
    client.connect_async("broker.test", 1883)
    client.loop_start()
    try:
        assert _wait_until(lambda: len(broker.ends) == 2)
        assert _protocol_name(broker.connect_packet(1)) == b"MQIsdp"
    finally:
        client.loop_stop()


def test_paho_does_not_call_on_connect_before_the_version_retry(broker: Broker) -> None:
    broker.expect(_CONNACK_UNSUPPORTED_VERSION)
    broker.expect(b"")
    calls: list[Any] = []
    client = _paho_client(broker)
    client.on_connect = lambda *args: calls.append(args)
    client.connect_async("broker.test", 1883)
    client.loop_start()
    try:
        assert _wait_until(lambda: len(broker.ends) == 2)
        broker.connect_packet(1)
        assert calls == []
    finally:
        client.loop_stop()


@pytest.mark.filterwarnings("ignore::pytest.PytestUnhandledThreadExceptionWarning")
def test_a_failed_version_retry_ends_the_network_thread(broker: Broker) -> None:
    broker.expect(_CONNACK_UNSUPPORTED_VERSION)
    broker.expect(None)
    client = _paho_client(broker)
    client.connect_async("broker.test", 1883)
    client.loop_start()
    assert _wait_until(lambda: client._thread is None)


def test_paho_tries_a_generated_client_id_after_an_empty_one_is_rejected(
    broker: Broker,
) -> None:
    broker.expect(_CONNACK_IDENTIFIER_REJECTED)
    broker.expect(b"")
    client = _paho_client(broker, client_id="")
    client.connect_async("broker.test", 1883)
    client.loop_start()
    try:
        assert _wait_until(lambda: len(broker.ends) == 2)
        assert _client_id(broker.connect_packet(0)) == b""
        assert _client_id(broker.connect_packet(1)) != b""
    finally:
        client.loop_stop()


@pytest.mark.parametrize("code", [4, 5], ids=["bad-user-name-or-password", "not-authorized"])
def test_delivery_stops_on_a_real_rejected_login(broker: Broker, code: int) -> None:
    broker.expect(bytes([0x20, 0x02, 0x00, code]))
    delivery = MqttDelivery(make_mqtt_config(), client=_paho_client(broker))
    with pytest.raises(LoginRejected):
        _connect_within_timeout(delivery)


@pytest.mark.filterwarnings("ignore::pytest.PytestUnhandledThreadExceptionWarning")
def test_delivery_connects_after_a_failed_version_retry_ends_the_thread(
    broker: Broker,
) -> None:
    broker.expect(_CONNACK_UNSUPPORTED_VERSION)
    broker.expect(None)
    broker.expect(_CONNACK_ACCEPTED)
    client = _paho_client(broker)
    delivery = MqttDelivery(make_mqtt_config(), client=client)
    try:
        _connect_within_timeout(delivery)
        assert client.is_connected()
    finally:
        client.loop_stop()
