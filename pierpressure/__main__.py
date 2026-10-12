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

Inside a Home Assistant add-on, the Configuration form lists the piers, and the
config file adds the settings the form leaves unset (addon-form-horizon-file,
ADR-0021). When neither names a broker host, the broker comes from the
Supervisor's ``mqtt`` service (ha-addon-mqtt-service D1, D2).
"""

from __future__ import annotations

import logging
import os
import signal
import sys
from pathlib import Path
from typing import NamedTuple

from pierpressure import __version__
from pierpressure.addon_options import OPTIONS_PATH, is_set, read_form_values
from pierpressure.addon_settings import combine_settings
from pierpressure.conditions import build_provider
from pierpressure.core.clock import SystemClock
from pierpressure.core.config import (
    AppConfig,
    BrokerSettings,
    ConfigError,
    ConfigFile,
    build_config,
    read_config,
    read_config_mapping,
)
from pierpressure.delivery.mqtt import DeliveryError, MqttDelivery
from pierpressure.explain import Explainer, build_explainer
from pierpressure.service import Service
from pierpressure.supervisor import SETTINGS_PLACE, SupervisorError, fetch_mqtt_broker

logger = logging.getLogger("pierpressure")

DEFAULT_CONFIG_PATH = "config.yaml"

# The advice for a rejected login the Supervisor supplied (retry-broker-connection D3):
# the user never set mqtt.username or mqtt.password, and cannot set them alone. The
# delivery adapter gives it at startup and during a reconnect
# (reconnect-restores-delivery D5).
_RESTART_MOSQUITTO = (
    "The username and password came from the Supervisor's mqtt service, so restart the "
    "Mosquitto broker add-on"
)
# The Supervisor's broker is used only inside an add-on, so the advice names both
# places to set mqtt.host there (addon-form-horizon-file D7).
SUPERVISOR_LOGIN_ADVICE = (
    f"{_RESTART_MOSQUITTO}, or set mqtt.host {SETTINGS_PLACE} to use your own broker login."
)


class LoadedConfig(NamedTuple):
    """The validated config, and whether its broker came from the Supervisor."""

    config: AppConfig
    broker_from_supervisor: bool


def build_delivery_and_explainer(
    config: AppConfig, *, broker_from_supervisor: bool = False
) -> tuple[MqttDelivery, Explainer]:
    """Construct the delivery adapter and explainer from config (design D7).

    The single ``explainer.enabled`` flag drives both edges: when enabled, the real
    provider-backed explainer is wired and delivery manages the narrative entity;
    when disabled (or the block is absent), the no-op explainer is wired and delivery
    does not manage the entity — so no provider is constructed and no narrative entity
    appears.

    The login advice follows where the broker came from (addon-form-broker D4). A
    broker from the Supervisor gets :data:`SUPERVISOR_LOGIN_ADVICE`. A broker from
    the file or the form gets the adapter's default, which says to check the
    username and password (reconnect-restores-delivery D5).
    """
    manage_narrative = config.explainer is not None and config.explainer.enabled
    login_advice = SUPERVISOR_LOGIN_ADVICE if broker_from_supervisor else None
    delivery = MqttDelivery(
        config.mqtt,
        manage_narrative=manage_narrative,
        login_advice=login_advice,
    )
    explainer = build_explainer(config.explainer)
    return delivery, explainer


def load_app_config(
    config_path: str, options_path: str | os.PathLike[str] = OPTIONS_PATH
) -> LoadedConfig:
    """Load the config, asking the Supervisor for the broker only when needed (D1, D2).

    Outside an add-on (no ``SUPERVISOR_TOKEN``), the config file holds every
    setting. Inside an add-on, the Configuration form saved at ``options_path``
    lists the piers, and the config file, when it exists, adds the settings the
    form leaves unset (addon-form-horizon-file D4, D6). The Supervisor is asked
    for the broker only inside an add-on, and only when the settings name no
    ``mqtt.host``. Logs where the settings and the broker came from, never the
    broker's password (D8, addon-form-broker D6). Raises :class:`ConfigError`,
    :class:`OSError` or :class:`SupervisorError`.
    """
    token = os.environ.get("SUPERVISOR_TOKEN")
    if token:
        read, broker_place = _read_addon_settings(config_path, options_path)
    else:
        read = read_config(config_path)
        broker_place = Path(config_path).name
        logger.info("Settings from %s", broker_place)

    broker: BrokerSettings | None = None
    if token and not read.names_broker_host:
        broker = fetch_mqtt_broker(token)
    config = build_config(read, broker)

    source = "the Supervisor's mqtt service" if broker is not None else broker_place
    logger.info("MQTT broker from %s: %s:%d", source, config.mqtt.host, config.mqtt.port)
    return LoadedConfig(config, broker_from_supervisor=broker is not None)


def _read_addon_settings(
    config_path: str, options_path: str | os.PathLike[str]
) -> tuple[ConfigFile, str]:
    """Combine the add-on's form with its config file (addon-form-horizon-file D4, D6, D8).

    Returns the combined settings, and where a broker host in them came from.
    The file is read without the broker rule; :class:`ConfigFile` checks that
    rule on the combined settings, so a host on the form and a password in the
    file is reported as a conflict, not as a password without a host. Raises
    "Nothing is set up" when the form lists no piers; a missing options file
    counts as an empty form.
    """
    path = Path(config_path)
    options = read_form_values(options_path)
    if options is None or not options.get("piers"):
        raise ConfigError(_nothing_set_up(path))

    file = read_config_mapping(path) if path.exists() else None
    combined = combine_settings(options, file)
    if combined.file_adds:
        logger.info("Settings from the Configuration tab and %s", path.name)
    else:
        logger.info("Settings from the Configuration tab")

    form_mqtt = options.get("mqtt")
    form_host = isinstance(form_mqtt, dict) and is_set(form_mqtt.get("host"))
    broker_place = "the Configuration tab" if form_host else path.name
    return ConfigFile(raw=combined.raw, base_dir=path.resolve().parent), broker_place


def _nothing_set_up(path: Path) -> str:
    """The error for an empty form, naming the file's piers when it can (D6).

    A missing or broken file, or one with no usable pier ids, gives the short
    error, so the main cause, the empty form, is not hidden.
    """
    message = "Nothing is set up: the Configuration tab lists no piers."
    ids = _file_pier_ids(path)
    if not ids:
        return f"{message} Add a pier on the add-on's Configuration tab, then restart it."
    names = ", ".join(repr(pier_id) for pier_id in ids)
    return (
        f"{message} {path.name} lists the piers {names}, but {path.name} cannot list piers "
        "on its own. Add each of them on the add-on's Configuration tab with the same id, "
        f"keep only the extra settings in {path.name}, then restart the add-on."
    )


def _file_pier_ids(path: Path) -> list[str]:
    """The text ids of the file's piers, or none when the file cannot be read."""
    try:
        raw = read_config_mapping(path)
    except ConfigError, OSError:
        return []
    piers = raw.get("piers")
    if not isinstance(piers, list):
        return []
    ids = [p["id"] for p in piers if isinstance(p, dict) and isinstance(p.get("id"), str)]
    return list(dict.fromkeys(ids))


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
        loaded = load_app_config(config_path)
    except (ConfigError, OSError, SupervisorError) as exc:
        logger.error("Configuration error: %s", exc)
        return 1
    except KeyboardInterrupt:
        logger.info("Shutting down")
        return 0

    config = loaded.config
    delivery, explainer = build_delivery_and_explainer(
        config, broker_from_supervisor=loaded.broker_from_supervisor
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
