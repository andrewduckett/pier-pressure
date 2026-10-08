"""Entry point: ``python -m pierpressure`` (design D9, D10).

Loads config, connects to the broker, publishes on startup, and runs the loop.
Exits non-zero on an unrecoverable startup failure (bad config, or the broker
unreachable at boot) rather than idling as if healthy.

Inside a Home Assistant add-on, a config file that names no broker host uses the
broker from the Supervisor's ``mqtt`` service (ha-addon-mqtt-service D1, D2).
"""

from __future__ import annotations

import logging
import os
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


def build_delivery_and_explainer(config: AppConfig) -> tuple[MqttDelivery, Explainer]:
    """Construct the delivery adapter and explainer from config (design D7).

    The single ``explainer.enabled`` flag drives both edges: when enabled, the real
    provider-backed explainer is wired and delivery manages the narrative entity;
    when disabled (or the block is absent), the no-op explainer is wired and delivery
    does not manage the entity — so no provider is constructed and no narrative entity
    appears.
    """
    manage_narrative = config.explainer is not None and config.explainer.enabled
    delivery = MqttDelivery(config.mqtt, manage_narrative=manage_narrative)
    explainer = build_explainer(config.explainer)
    return delivery, explainer


def load_app_config(config_path: str) -> AppConfig:
    """Load the config, asking the Supervisor for the broker only when needed (D1, D2).

    The Supervisor is asked only inside an add-on (``SUPERVISOR_TOKEN`` is set) and
    only when the file names no ``mqtt.host``. Logs where the broker came from,
    never its password (D6). Raises :class:`ConfigError`, :class:`OSError` or
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
    return config


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    # First, before config loads, so every report names the version (design D6).
    logger.info("PierPressure %s", __version__)
    args = sys.argv[1:] if argv is None else argv
    config_path = args[0] if args else os.environ.get("PIERPRESSURE_CONFIG", DEFAULT_CONFIG_PATH)

    try:
        config = load_app_config(config_path)
    except (ConfigError, OSError, SupervisorError) as exc:
        logger.error("Configuration error: %s", exc)
        return 1

    delivery, explainer = build_delivery_and_explainer(config)
    try:
        delivery.connect()
    except DeliveryError as exc:
        logger.error("Startup delivery failure: %s", exc)
        return 1

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
    delivery.subscribe_refresh([pier.id for pier in config.piers], service.enqueue_refresh)

    logger.info("PierPressure started for %d pier(s)", len(config.piers))
    try:
        service.run()
    except DeliveryError as exc:
        # Includes a failed startup health reset, which happens before the
        # process reports itself online (provider-health-entities D4).
        logger.error("Delivery failure: %s", exc)
        return 1
    except KeyboardInterrupt:  # pragma: no cover - interactive shutdown
        logger.info("Shutting down")
    finally:
        delivery.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
