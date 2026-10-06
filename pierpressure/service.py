"""The persistent service loop (design D7).

Wires the pure core to the delivery adapter and owns freshness: publish on
startup, on a configurable interval, and on demand via a refresh command.

Threading model: paho's network thread runs the refresh callback, which only
*enqueues* the pier id on a thread-safe queue — it never publishes. The main
thread owns all publishing (no concurrent writes) and waits on the queue against
an **absolute monotonic deadline** for the next periodic all-pier recompute.

The absolute deadline is what prevents starvation: a fresh per-call timeout
would reset on every dequeued refresh, so frequent refreshes could starve the
interval recompute forever. Instead each iteration first checks whether the
deadline has passed (recompute all, reset the deadline) and otherwise waits only
the remaining time; a dequeued refresh recomputes that one pier *without* moving
the deadline.

Provider health (provider-health-entities D3, D4) is kept here, in memory, per
pier and provider. On startup the service publishes every provider's health with
no history before it goes online, so no retained success from before a restart is
ever shown as current. After each fetch it folds that fetch's outcomes into the
pier's health and publishes it beside the verdict.
"""

from __future__ import annotations

import logging
import queue
import time
from collections.abc import Callable, Sequence

from pierpressure.conditions import FetchResult
from pierpressure.core.clock import Clock
from pierpressure.core.conditions import Conditions
from pierpressure.core.config import AppConfig, PierConfig
from pierpressure.core.producer import produce_verdict
from pierpressure.delivery.mqtt import MqttDelivery
from pierpressure.explain import Explainer, no_op_explainer
from pierpressure.health import ProviderHealth, ProviderInfo, fold

logger = logging.getLogger(__name__)

MonotonicFn = Callable[[], float]

# A conditions provider: given a pier, return an already-obtained Conditions
# value and the outcome of each source fetch behind it. It never raises — a failed
# fetch yields a partial (a present group beside an absent one) or empty value, so
# the service always publishes an honest verdict (design D6).
ConditionsProvider = Callable[[PierConfig], FetchResult]


def _no_conditions(_pier: PierConfig) -> FetchResult:
    """Fallback provider: the canonical empty value (astronomy-only verdicts)."""
    return FetchResult(Conditions(None, None))


class Service:
    """The startup + interval + on-demand recompute loop."""

    def __init__(
        self,
        config: AppConfig,
        delivery: MqttDelivery,
        clock: Clock,
        refresh_queue: queue.Queue[str] | None = None,
        conditions_provider: ConditionsProvider | None = None,
        explainer: Explainer | None = None,
        providers: Sequence[ProviderInfo] = (),
    ) -> None:
        self._config = config
        self._delivery = delivery
        self._clock = clock
        self._queue: queue.Queue[str] = (
            refresh_queue if refresh_queue is not None else queue.Queue()
        )
        self._piers = {pier.id: pier for pier in config.piers}
        self._conditions_provider = conditions_provider or _no_conditions
        # The optional explainer edge (design D1). The default no-op returns None,
        # so delivery receives no narrative and the existing behavior is unchanged.
        # It never raises — a failed provider is a logged miss inside the wrapper.
        # It is computed synchronously here (design D5), so on a cache miss it delays
        # this pier's publish by up to the explainer's bounded timeout (and those
        # waits serialize across piers); moving it off the publish thread is the
        # deferred async path (design Open Questions). The cache makes steady state a
        # local hit, and a disabled explainer adds nothing.
        self._explainer = explainer or no_op_explainer
        # The conditions providers whose health this service reports, and that
        # health per pier and provider key. It is seeded by run(); with no
        # providers (the default), no health is published.
        self._providers = tuple(providers)
        self._health: dict[str, dict[str, ProviderHealth]] = {}

    def enqueue_refresh(self, pier_id: str) -> None:
        """Callback for the network thread: record an on-demand refresh request."""
        self._queue.put(pier_id)

    def publish_pier(self, pier_id: str) -> None:
        """Recompute and publish a single pier."""
        pier = self._piers.get(pier_id)
        if pier is None:
            logger.warning("Ignoring refresh for unknown pier %r", pier_id)
            return
        self._publish(pier)

    def publish_all(self) -> None:
        """Recompute and publish every configured pier."""
        for pier in self._config.piers:
            self._publish(pier)

    def _publish(self, pier: PierConfig) -> None:
        """Fetch this pier's conditions and publish its recomputed verdict.

        Fetching happens here — before the pure core runs — on startup, on the
        interval, and on an on-demand refresh alike, so the container owns its own
        freshness (design D7). The provider never raises; a failed fetch degrades
        to a partial snapshot rather than skipping a publish.
        """
        result = self._conditions_provider(pier)
        # Only the conditions reach the core; the fetch outcomes feed health alone.
        document = produce_verdict(pier, self._clock, result.conditions)
        narrative = self._explainer(document)  # never raises; may be None
        self._delivery.publish_verdict(document, narrative=narrative)

        healths = self._health.get(pier.id)
        if healths:
            for outcome in result.outcomes:
                if outcome.key in healths:
                    healths[outcome.key] = fold(healths[outcome.key], outcome)
                else:
                    logger.warning(
                        "Ignoring fetch outcome from unconfigured provider %r", outcome.key
                    )
            self._delivery.publish_health(pier.id, healths.values())

    def _reset_health(self) -> None:
        """Seed every pier's health with no history and publish it (design D4).

        Raises :class:`~pierpressure.delivery.mqtt.DeliveryError` if the publish
        fails, so the process exits before it reports itself online.
        """
        tracking_since = self._clock.now()
        for pier in self._config.piers:
            self._health[pier.id] = {
                info.key: ProviderHealth.empty(
                    key=info.key, name=info.name, role=info.role, tracking_since=tracking_since
                )
                for info in self._providers
            }
            if self._providers:
                self._delivery.publish_health(pier.id, self._health[pier.id].values())

    def _drain_refreshes(self, first: str) -> set[str]:
        """Collapse duplicate queued refreshes into one recompute per pier (D7).

        Includes the already-dequeued ``first`` id, then drains everything
        currently pending so N identical spammed refreshes become a single
        recompute for that pier.
        """
        pier_ids = {first}
        while True:
            try:
                pier_ids.add(self._queue.get_nowait())
            except queue.Empty:
                break
        return pier_ids

    def run(
        self,
        *,
        monotonic: MonotonicFn = time.monotonic,
        max_iterations: int | None = None,
    ) -> None:
        """Reset health, go online, publish all piers, then loop until stopped.

        The health reset comes before ``go_online()`` and before any fetch, so an
        entity never shows a retained health time from before this start.
        ``monotonic`` and ``max_iterations`` are injection points for tests;
        production calls ``run()`` with the defaults (loops forever).
        """
        interval = self._config.recompute.interval_seconds
        self._reset_health()
        self._delivery.go_online()
        self.publish_all()
        deadline = monotonic() + interval

        iterations = 0
        while max_iterations is None or iterations < max_iterations:
            iterations += 1
            now = monotonic()
            if now >= deadline:
                # The deadline has been reached even though refreshes may still
                # be pending: do the periodic all-pier recompute regardless.
                self.publish_all()
                deadline = monotonic() + interval
                continue

            timeout = max(0.0, deadline - now)
            try:
                pier_id = self._queue.get(timeout=timeout)
            except queue.Empty:
                # Interval elapsed with no refresh: recompute all, reset deadline.
                self.publish_all()
                deadline = monotonic() + interval
            else:
                # On-demand refresh: recompute the target pier(s) only; the
                # deadline is left untouched so it cannot be starved.
                for target in self._drain_refreshes(pier_id):
                    self.publish_pier(target)
