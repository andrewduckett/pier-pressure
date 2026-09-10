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
"""

from __future__ import annotations

import logging
import queue
import time
from collections.abc import Callable

from pierpressure.core.clock import Clock
from pierpressure.core.conditions import ConditionsSnapshot
from pierpressure.core.config import AppConfig, PierConfig
from pierpressure.core.producer import produce_verdict
from pierpressure.delivery.mqtt import MqttDelivery

logger = logging.getLogger(__name__)

MonotonicFn = Callable[[], float]

# A conditions provider: given a pier, return an already-obtained snapshot. It
# never raises — a failed fetch yields a partial (possibly empty) snapshot, so
# the service always publishes an honest verdict (design D6).
ConditionsProvider = Callable[[PierConfig], ConditionsSnapshot]


def _no_conditions(_pier: PierConfig) -> ConditionsSnapshot:
    """Fallback provider: an empty snapshot (astronomy-only verdicts)."""
    return ConditionsSnapshot()


class Service:
    """The startup + interval + on-demand recompute loop."""

    def __init__(
        self,
        config: AppConfig,
        delivery: MqttDelivery,
        clock: Clock,
        refresh_queue: queue.Queue[str] | None = None,
        conditions_provider: ConditionsProvider | None = None,
    ) -> None:
        self._config = config
        self._delivery = delivery
        self._clock = clock
        self._queue: queue.Queue[str] = (
            refresh_queue if refresh_queue is not None else queue.Queue()
        )
        self._piers = {pier.id: pier for pier in config.piers}
        self._conditions_provider = conditions_provider or _no_conditions

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
        conditions = self._conditions_provider(pier)
        self._delivery.publish_verdict(produce_verdict(pier, self._clock, conditions))

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
        """Publish all piers on startup, then loop until stopped.

        ``monotonic`` and ``max_iterations`` are injection points for tests;
        production calls ``run()`` with the defaults (loops forever).
        """
        interval = self._config.recompute.interval_seconds
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
