"""The Home Assistant Supervisor's ``mqtt`` service (ha-addon-mqtt-service D3-D5).

Inside an add-on, the Supervisor hands out the broker that another add-on (usually
Mosquitto) provides. :func:`fetch_mqtt_broker` asks for it once at startup and
returns plain :class:`~pierpressure.core.config.BrokerSettings` for the core to use.

The Mosquitto add-on withdraws its details for a few seconds each time it starts,
so a missing service is retried for a bounded time (D4). A refused token, a broker
that requires TLS, or one that needs another MQTT version fails at once, because
waiting cannot fix them. No error message or log line includes the token or the
broker password.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from http import HTTPStatus
from typing import Any

import httpx

from pierpressure.core.config import BrokerSettings

logger = logging.getLogger(__name__)

SERVICE_URL = "http://supervisor/services/mqtt"

# No request starts later than this after the first one (spec "The add-on waits a
# bounded time for the Supervisor's broker").
WAIT_SECONDS = 60.0
PAUSE_SECONDS = 2.0
REQUEST_TIMEOUT_SECONDS = 5.0

# The Supervisor's default, which also applies when a provider names none (D5).
SUPPORTED_PROTOCOL = "3.1.1"

ISSUES_URL = "https://github.com/andrewduckett/pier-pressure/issues"

_NO_BROKER = (
    "No MQTT broker was found: the Supervisor gave no usable mqtt service "
    "(last answer: {reason}). "
    "Install the Mosquitto broker add-on, or set mqtt.host in config.yaml."
)


class SupervisorError(Exception):
    """The Supervisor gave no broker PierPressure can use."""


class _NotYet(Exception):
    """The Supervisor does not provide the broker yet; worth asking again (D4)."""


def fetch_mqtt_broker(
    token: str,
    *,
    client: httpx.Client | None = None,
    sleep: Callable[[float], None] = time.sleep,
    monotonic: Callable[[], float] = time.monotonic,
) -> BrokerSettings:
    """Ask the Supervisor for its ``mqtt`` service's broker settings.

    Retries a missing service, pausing :data:`PAUSE_SECONDS` between requests, and
    starts no request later than :data:`WAIT_SECONDS` after the first. Raises
    :class:`SupervisorError` when the wait runs out, when the Supervisor refuses
    access, or when the broker requires TLS or another MQTT version.
    """
    if client is not None:
        return _wait_for_broker(client, token, sleep, monotonic)
    # trust_env=False: a proxy named in HTTP_PROXY or ALL_PROXY must never see the
    # Supervisor token (spec "Proxy settings do not reach the token").
    with httpx.Client(timeout=REQUEST_TIMEOUT_SECONDS, trust_env=False) as own_client:
        return _wait_for_broker(own_client, token, sleep, monotonic)


def _wait_for_broker(
    client: httpx.Client,
    token: str,
    sleep: Callable[[float], None],
    monotonic: Callable[[], float],
) -> BrokerSettings:
    deadline = monotonic() + WAIT_SECONDS
    waiting = False
    while True:
        try:
            return _ask(client, token)
        except _NotYet as exc:
            reason = str(exc)
            if not waiting:
                waiting = True
                logger.info(
                    "Waiting up to %d seconds for the Supervisor's mqtt service (%s)",
                    WAIT_SECONDS,
                    exc,
                )
        remaining = deadline - monotonic()
        if remaining <= 0:
            raise SupervisorError(_NO_BROKER.format(reason=reason))
        sleep(min(PAUSE_SECONDS, remaining))


def _ask(client: httpx.Client, token: str) -> BrokerSettings:
    """Make one request; raise :class:`_NotYet` for anything worth retrying."""
    try:
        response = client.get(SERVICE_URL, headers={"Authorization": f"Bearer {token}"})
    except httpx.TransportError as exc:
        # The exception's text is left out so nothing from the request can leak.
        raise _NotYet(f"request failed: {type(exc).__name__}") from None

    if response.status_code in (HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN):
        raise SupervisorError(
            f"The Supervisor refused access to the mqtt service "
            f"(HTTP {response.status_code}). Set mqtt.host in config.yaml to use "
            f"your broker directly, and report this problem at {ISSUES_URL}."
        )
    if response.status_code != HTTPStatus.OK:
        raise _NotYet(f"HTTP {response.status_code}")

    try:
        body = response.json()
    except ValueError:
        raise _NotYet("the response is not JSON") from None
    data = body.get("data") if isinstance(body, dict) else None
    if not isinstance(data, dict):
        raise _NotYet("the response has no service details")
    return _broker_from(data)


def _broker_from(data: dict[str, Any]) -> BrokerSettings:
    host = data.get("host")
    port = data.get("port")
    if not isinstance(host, str) or not host or not isinstance(port, int) or isinstance(port, bool):
        raise _NotYet("the response has no usable host and port")

    if data.get("ssl") is True:
        raise SupervisorError(
            "The Supervisor's MQTT broker requires TLS, which PierPressure does not "
            "support. Set mqtt.host and mqtt.port in config.yaml to a broker listener "
            "that accepts connections without TLS."
        )
    # A missing or null protocol is the Supervisor's default (spec D5).
    protocol = data.get("protocol") or SUPPORTED_PROTOCOL
    if protocol != SUPPORTED_PROTOCOL:
        raise SupervisorError(
            f"The Supervisor's MQTT broker asks for MQTT {protocol}, but PierPressure "
            f"supports only MQTT {SUPPORTED_PROTOCOL}. Set mqtt.host and mqtt.port in "
            "config.yaml to a broker that accepts MQTT 3.1.1."
        )

    username = data.get("username")
    password = data.get("password")
    return BrokerSettings(
        host=host,
        port=port,
        username=username if isinstance(username, str) else None,
        password=password if isinstance(password, str) else None,
    )
