"""The explainer callable: caching, bounded latency, and graceful fallback (D1,D4,D5).

An :data:`Explainer` takes a finished verdict document and returns short prose, or
``None`` when there is no narrative. The default :func:`no_op_explainer` always
returns ``None`` (the explainer disabled), so the existing behavior is the default.

:class:`NarrativeExplainer` wraps a provider with the two bounds the design requires:
a bounded in-memory cache keyed on the exact prompt input (identical verdict terms
reuse the prose with no new provider call), and a per-call timeout so a slow or hung
provider can never stall the publish thread indefinitely. Every provider failure — an
exception, a timeout, or empty text — is logged and turned into ``None``; it never
raises into the recompute loop.

Latency, not zero delay: producing the narrative is synchronous on the publish
thread (design D5), so on a cache miss delivery is delayed by up to ``timeout`` and,
across piers, those waits serialize. The cache makes steady state a local hit; moving
generation off the publish thread is the deferred async path (design Open Questions).
"""

from __future__ import annotations

import logging
from collections import OrderedDict
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeoutError
from dataclasses import dataclass, field

from pierpressure.core.config import ExplainerConfig
from pierpressure.core.model import VerdictDocument

from .prompt import PromptInput, build_prompt_input
from .provider import PROVIDER_TIMEOUT, Provider, PydanticAIProvider

logger = logging.getLogger(__name__)

# The wrapper's per-call bound on a provider request: the hard wall-clock guarantee
# for the publish thread, whatever the provider does. It sits just above the
# provider's own timeout (PROVIDER_TIMEOUT) so a provider that honors its timeout
# self-aborts first and its worker is reclaimed, and this bound only bites for a
# provider that ignores its own (design D5).
DEFAULT_TIMEOUT = PROVIDER_TIMEOUT + 1.0

# The narrative cache is a performance/cost bound, never load-bearing (design D4).
# It is capped so a long-running service whose nightly verdicts vary cannot grow it
# without limit; the least-recently-used entry is evicted past the cap.
DEFAULT_MAX_CACHE = 256

# An explainer turns a finished verdict document into short prose, or None when
# there is no narrative (disabled, unconfigured, or a failed provider call).
Explainer = Callable[[VerdictDocument], str | None]


def no_op_explainer(_document: VerdictDocument) -> None:
    """The default explainer: produces no narrative (the explainer is disabled)."""
    return None


@dataclass
class NarrativeExplainer:
    """A provider-backed explainer with a bounded LRU cache and a bounded timeout."""

    provider: Provider
    timeout: float = DEFAULT_TIMEOUT
    max_cache: int = DEFAULT_MAX_CACHE
    _cache: OrderedDict[str, str] = field(default_factory=OrderedDict, init=False, repr=False)
    _executor: ThreadPoolExecutor | None = field(default=None, init=False, repr=False)

    def __call__(self, document: VerdictDocument) -> str | None:
        prompt = build_prompt_input(document)
        cached = self._cache.get(prompt.key)
        if cached is not None:
            self._cache.move_to_end(prompt.key)  # mark most-recently-used
            return cached
        narrative = self._generate(prompt)
        if narrative:
            self._cache[prompt.key] = narrative
            self._cache.move_to_end(prompt.key)
            while len(self._cache) > self.max_cache:
                self._cache.popitem(last=False)  # evict least-recently-used
            return narrative
        return None

    def _generate(self, prompt: PromptInput) -> str | None:
        """Call the provider under a timeout; any failure logs and yields None.

        The provider runs on one shared single-worker executor rather than a fresh
        pool per call. A provider that honors its own timeout finishes (with a value
        or an exception) before the wrapper's timeout, so the worker is reclaimed
        normally; only a provider that ignores its timeout leaves the worker running,
        which then blocks the next call's slot until it returns — the publish thread
        itself is never blocked past ``timeout``.
        """
        if self._executor is None:
            self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="explainer")
        future = self._executor.submit(self.provider.generate, prompt)
        try:
            result = future.result(timeout=self.timeout)
        except FuturesTimeoutError:
            future.cancel()  # a running task cannot be cancelled, but a queued one can
            logger.warning("explainer provider timed out after %ss; no narrative", self.timeout)
            return None
        except Exception as exc:  # noqa: BLE001 - any provider failure degrades to no-narrative
            logger.warning("explainer provider failed: %s", exc)
            return None
        if not result or not result.strip():
            return None
        return result


def build_explainer(config: ExplainerConfig | None) -> Explainer:
    """Wire the explainer from config: the no-op when disabled, else a real provider.

    An absent block or ``enabled: false`` yields :func:`no_op_explainer` and
    constructs no provider (design D7). When enabled, the default Pydantic AI provider
    is wired behind the caching, bounded-timeout wrapper; the config ``model`` string
    selects the LLM provider.
    """
    if config is None or not config.enabled:
        return no_op_explainer
    provider = PydanticAIProvider(model=config.model, api_key=config.api_key)
    return NarrativeExplainer(provider)
