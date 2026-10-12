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
broker from the Supervisor's ``mqtt`` service (ha-addon-mqtt-service D1, D2). When
the add-on's Configuration form lists a pier, the form replaces the config file
(addon-options-form D2), and the form's broker host, when set, replaces the
Supervisor's broker (addon-form-broker).
"""

from __future__ import annotations

import logging
import os
import signal
import sys
from pathlib import Path
from typing import NamedTuple

from pierpressure import __version__
from pierpressure.addon_options import OPTIONS_PATH, read_addon_options
from pierpressure.conditions import build_provider
from pierpressure.core.clock import SystemClock
from pierpressure.core.config import (
    AppConfig,
    BrokerSettings,
    ConfigError,
    ConfigFile,
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
_RESTART_MOSQUITTO = (
    "The username and password came from the Supervisor's mqtt service, so restart the "
    "Mosquitto broker add-on"
)
SUPERVISOR_LOGIN_ADVICE = f"{_RESTART_MOSQUITTO}, or set mqtt.host to use your own broker login."

# On the form path, the Supervisor's errors and login advice name the Configuration
# tab as the place to set mqtt.host, and add this note, because config.yaml is not
# read there (addon-form-broker D4, D5).
FORM_PLACE = "on the Configuration tab"
FORM_NOTE = "config.yaml is not read while the Configuration tab lists piers."
FORM_LOGIN_ADVICE = (
    f"{_RESTART_MOSQUITTO}, or set mqtt.host {FORM_PLACE} to use your own broker login. {FORM_NOTE}"
)


class LoadedConfig(NamedTuple):
    """The validated config, and where its settings and broker came from."""

    config: AppConfig
    broker_from_supervisor: bool
    from_form: bool


def build_delivery_and_explainer(
    config: AppConfig, *, broker_from_supervisor: bool = False, from_form: bool = False
) -> tuple[MqttDelivery, Explainer]:
    """Construct the delivery adapter and explainer from config (design D7).

    The single ``explainer.enabled`` flag drives both edges: when enabled, the real
    provider-backed explainer is wired and delivery manages the narrative entity;
    when disabled (or the block is absent), the no-op explainer is wired and delivery
    does not manage the entity — so no provider is constructed and no narrative entity
    appears.

    The login advice follows where the broker came from, not the settings
    (addon-form-broker D4). A broker from the Supervisor gets the Supervisor's
    advice, which names the Configuration tab when the settings came from the form.
    A broker from the file or the form gets the adapter's default, which says to
    check the username and password (reconnect-restores-delivery D5).
    """
    manage_narrative = config.explainer is not None and config.explainer.enabled
    login_advice: str | None = None
    if broker_from_supervisor:
        login_advice = FORM_LOGIN_ADVICE if from_form else SUPERVISOR_LOGIN_ADVICE
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

    Inside an add-on (``SUPERVISOR_TOKEN`` is set), the Configuration form saved at
    ``options_path`` is read first. When it lists a pier, it replaces the config
    file, which is then not read (addon-options-form D2). The Supervisor is asked
    for the broker only inside an add-on, and only when the settings, from the
    file or the form, name no ``mqtt.host``. Logs where the settings and the broker
    came from, never the broker's password (D6, addon-form-broker D6). Returns the
    config, whether the broker came from the Supervisor, and whether the settings
    came from the form. Raises :class:`ConfigError`, :class:`OSError` or
    :class:`SupervisorError`; on the form path, a :class:`SupervisorError` names the
    Configuration tab and notes that the file is not read (addon-form-broker D5).
    """
    token = os.environ.get("SUPERVISOR_TOKEN")
    form = read_addon_options(options_path) if token else None
    if form is not None:
        if Path(config_path).exists():
            logger.warning(
                "%s is ignored: the Configuration tab lists piers, so only its settings apply",
                config_path,
            )
        read = ConfigFile(raw=form, base_dir=Path(config_path).resolve().parent)
        logger.info("Settings from the Configuration tab")
    else:
        read = _read_config_file(config_path, inside_addon=bool(token))
        logger.info("Settings from %s", Path(config_path).name)

    broker: BrokerSettings | None = None
    if token and not read.names_broker_host:
        try:
            broker = fetch_mqtt_broker(token)
        except SupervisorError as exc:
            if form is None:
                raise
            raise SupervisorError(f"{exc} {FORM_NOTE}") from exc
    config = build_config(read, broker)

    if broker is not None:
        source = "the Supervisor's mqtt service"
    elif form is not None:
        source = "the Configuration tab"
    else:
        source = Path(config_path).name
    logger.info("MQTT broker from %s: %s:%d", source, config.mqtt.host, config.mqtt.port)
    return LoadedConfig(
        config, broker_from_supervisor=broker is not None, from_form=form is not None
    )


def _read_config_file(config_path: str, *, inside_addon: bool) -> ConfigFile:
    """Read the config file; inside an add-on, a missing one points to the form (D4)."""
    try:
        return read_config(config_path)
    except FileNotFoundError as exc:
        if not inside_addon:
            raise
        raise ConfigError(
            f"Nothing is set up: the Configuration tab lists no piers, and {config_path} "
            "does not exist. Add a pier on the add-on's Configuration tab, then restart it."
        ) from exc


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
        config, broker_from_supervisor=loaded.broker_from_supervisor, from_form=loaded.from_form
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
