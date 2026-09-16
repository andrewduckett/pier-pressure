"""The explainer callable: caching, bounded latency, and graceful fallback (D1,D4,D5).

An :data:`Explainer` takes a finished verdict document and returns short prose, or
``None`` when there is no narrative. The default :func:`no_op_explainer` always
returns ``None`` (the explainer disabled), so the existing behavior is the default.

:class:`NarrativeExplainer` wraps a provider with the two bounds the design requires:
an in-memory cache keyed on the exact prompt input (identical verdict terms reuse
the prose with no new provider call), and a per-call timeout so a slow or hung
provider can never stall the publish thread. Every provider failure — an exception,
a timeout, or empty text — is logged and turned into ``None``; it never raises into
the recompute loop and never blocks or delays delivery of the verdict.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeoutError
from dataclasses import dataclass, field

from pierpressure.core.config import ExplainerConfig
from pierpressure.core.model import VerdictDocument

from .prompt import PromptInput, build_prompt_input
from .provider import Provider, PydanticAIProvider

logger = logging.getLogger(__name__)

# The default per-call bound on a provider request. On a cache miss the publish
# thread waits at most this long before giving up and delivering the verdict
# without a narrative (design D5).
DEFAULT_TIMEOUT = 10.0

# An explainer turns a finished verdict document into short prose, or None when
# there is no narrative (disabled, unconfigured, or a failed provider call).
Explainer = Callable[[VerdictDocument], str | None]


def no_op_explainer(_document: VerdictDocument) -> None:
    """The default explainer: produces no narrative (the explainer is disabled)."""
    return None


@dataclass
class NarrativeExplainer:
    """A provider-backed explainer with a deterministic cache and a bounded timeout."""

    provider: Provider
    timeout: float = DEFAULT_TIMEOUT
    _cache: dict[str, str] = field(default_factory=dict, init=False, repr=False)

    def __call__(self, document: VerdictDocument) -> str | None:
        prompt = build_prompt_input(document)
        cached = self._cache.get(prompt.key)
        if cached is not None:
            return cached
        narrative = self._generate(prompt)
        if narrative:
            self._cache[prompt.key] = narrative
            return narrative
        return None

    def _generate(self, prompt: PromptInput) -> str | None:
        """Call the provider under a timeout; any failure logs and yields None."""
        executor = ThreadPoolExecutor(max_workers=1)
        try:
            future = executor.submit(self.provider.generate, prompt)
            result = future.result(timeout=self.timeout)
        except FuturesTimeoutError:
            logger.warning("explainer provider timed out after %ss; no narrative", self.timeout)
            return None
        except Exception as exc:  # noqa: BLE001 - any provider failure degrades to no-narrative
            logger.warning("explainer provider failed: %s", exc)
            return None
        finally:
            # Do not wait: a hung worker must not block the publish thread. The
            # provider carries its own timeout, so the worker cannot linger forever.
            executor.shutdown(wait=False)
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
