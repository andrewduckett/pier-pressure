"""Entry point: ``python -m pierpressure`` (design D9, D10).

Loads config, connects to the broker, publishes on startup, and runs the loop.
Exits non-zero on an unrecoverable startup failure (bad config, or the broker
unreachable at boot) rather than idling as if healthy.
"""

from __future__ import annotations

import logging
import os
import sys

from pierpressure.core.clock import SystemClock
from pierpressure.core.config import ConfigError, load_config
from pierpressure.delivery.mqtt import DeliveryError, MqttDelivery
from pierpressure.service import Service

logger = logging.getLogger("pierpressure")

DEFAULT_CONFIG_PATH = "config.yaml"


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    args = sys.argv[1:] if argv is None else argv
    config_path = args[0] if args else os.environ.get("PIERPRESSURE_CONFIG", DEFAULT_CONFIG_PATH)

    try:
        config = load_config(config_path)
    except (ConfigError, OSError) as exc:
        logger.error("Configuration error: %s", exc)
        return 1

    delivery = MqttDelivery(config.mqtt)
    try:
        delivery.connect()
    except DeliveryError as exc:
        logger.error("Startup delivery failure: %s", exc)
        return 1

    service = Service(config, delivery, SystemClock())
    delivery.subscribe_refresh([pier.id for pier in config.piers], service.enqueue_refresh)

    logger.info("PierPressure started for %d pier(s)", len(config.piers))
    try:
        service.run()
    except KeyboardInterrupt:  # pragma: no cover - interactive shutdown
        logger.info("Shutting down")
    finally:
        delivery.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
