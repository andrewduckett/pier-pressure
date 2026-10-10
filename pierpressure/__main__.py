"""Entry point: ``python -m pierpressure`` (design D9, D10).

Loads config, connects to the broker, publishes on startup, and runs the loop.
When the broker cannot be reached, it waits and tries again rather than exiting
(retry-broker-connection). It exits non-zero on a startup failure that retrying
cannot fix: bad config, or a broker that rejects the login. After a later outage
it reconnects and restores its delivery without a restart; a login rejected then
is logged, and it keeps trying (reconnect-restores-delivery). A publish during an
outage is held for that restore, so it never stops the process
(publish-failure-resilience).

SIGTERM stops it the same way as Ctrl-C: it closes the delivery, which publishes
the retained ``offline`` first, and exits 0 (stop-goes-offline).

Inside a Home Assistant add-on, a config file that names no broker host uses the
broker from the Supervisor's ``mqtt`` service (ha-addon-mqtt-service D1, D2).
"""

from __future__ import annotations

import logging
import os
import signal
import sys
from pathlib import Path

from pierpressure import __version__
from pierpressure.conditions import build_provider
from pierpressure.core.clock import SystemClock
from pierpressure.core.config import (
    AppConfig,
    BrokerSettings,
    ConfigError,
    build_config,
    read_config,
)
from pierpressure.delivery.mqtt import DeliveryError, MqttDelivery
from pierpressure.explain import Explainer, build_explainer
from pierpressure.service import Service
from pierpressure.supervisor import SupervisorError, fetch_mqtt_broker

logger = logging.getLogger("pierpressure")

DEFAULT_CONFIG_PATH = "config.yaml"

# The advice for a rejected login the Supervisor supplied (retry-broker-connection D3):
# the user never set mqtt.username or mqtt.password, and cannot set them alone. The
# delivery adapter gives it at startup and during a reconnect
# (reconnect-restores-delivery D5).
SUPERVISOR_LOGIN_ADVICE = (
    "The username and password came from the Supervisor's mqtt service, so restart the "
    "Mosquitto broker add-on, or set mqtt.host to use your own broker login."
)


def build_delivery_and_explainer(
    config: AppConfig, *, broker_from_supervisor: bool = False
) -> tuple[MqttDelivery, Explainer]:
    """Construct the delivery adapter and explainer from config (design D7).

    The single ``explainer.enabled`` flag drives both edges: when enabled, the real
    provider-backed explainer is wired and delivery manages the narrative entity;
    when disabled (or the block is absent), the no-op explainer is wired and delivery
    does not manage the entity — so no provider is constructed and no narrative entity
    appears.

    A broker from the Supervisor gets the Supervisor's login advice; a broker from
    the file gets the adapter's default (reconnect-restores-delivery D5).
    """
    manage_narrative = config.explainer is not None and config.explainer.enabled
    delivery = MqttDelivery(
        config.mqtt,
        manage_narrative=manage_narrative,
        login_advice=SUPERVISOR_LOGIN_ADVICE if broker_from_supervisor else None,
    )
    explainer = build_explainer(config.explainer)
    return delivery, explainer


def load_app_config(config_path: str) -> tuple[AppConfig, bool]:
    """Load the config, asking the Supervisor for the broker only when needed (D1, D2).

    The Supervisor is asked only inside an add-on (``SUPERVISOR_TOKEN`` is set) and
    only when the file names no ``mqtt.host``. Logs where the broker came from,
    never its password (D6). Returns the config, and whether the broker came from
    the Supervisor. Raises :class:`ConfigError`, :class:`OSError` or
    :class:`SupervisorError`.
    """
    read = read_config(config_path)
    token = os.environ.get("SUPERVISOR_TOKEN")
    broker: BrokerSettings | None = None
    if token and not read.names_broker_host:
        broker = fetch_mqtt_broker(token)
    config = build_config(read, broker)

    source = "the Supervisor's mqtt service" if broker is not None else Path(config_path).name
    logger.info("MQTT broker from %s: %s:%d", source, config.mqtt.host, config.mqtt.port)
    return config, broker is not None


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    # First, before config loads, so every report names the version (design D6).
    logger.info("PierPressure %s", __version__)
    args = sys.argv[1:] if argv is None else argv
    config_path = args[0] if args else os.environ.get("PIERPRESSURE_CONFIG", DEFAULT_CONFIG_PATH)
    # A container stop sends SIGTERM; raise KeyboardInterrupt, as Ctrl-C does
    # (stop-goes-offline D3). First, so a stop during startup is handled too.
    signal.signal(signal.SIGTERM, signal.default_int_handler)

    try:
        config, broker_from_supervisor = load_app_config(config_path)
    except (ConfigError, OSError, SupervisorError) as exc:
        logger.error("Configuration error: %s", exc)
        return 1
    except KeyboardInterrupt:
        logger.info("Shutting down")
        return 0

    delivery, explainer = build_delivery_and_explainer(
        config, broker_from_supervisor=broker_from_supervisor
    )
    clock = SystemClock()
    conditions = build_provider(now=clock.now)
    service = Service(
        config,
        delivery,
        clock,
        conditions_provider=conditions.get,
        explainer=explainer,
        providers=conditions.providers,
    )
    # Before connect, so a reconnect just after the first accept reaches the
    # service (reconnect-restores-delivery D3).
    delivery.on_reconnect(service.enqueue_reconnect)
    # Every stop from here on closes the delivery, which publishes ``offline``
    # once connected (stop-goes-offline D1, D3).
    try:
        delivery.connect()
        delivery.subscribe_refresh([pier.id for pier in config.piers], service.enqueue_refresh)
        logger.info("PierPressure started for %d pier(s)", len(config.piers))
        # A failed publish never ends the loop; the delivery adapter logs it
        # (publish-failure-resilience D5).
        service.run()
    except DeliveryError as exc:
        logger.error("Startup delivery failure: %s", exc)
        return 1
    except KeyboardInterrupt:
        logger.info("Shutting down")
    finally:
        delivery.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
