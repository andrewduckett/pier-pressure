"""The explainer provider interface and its default Anthropic implementation (D3).

A provider turns a built :class:`~pierpressure.explain.prompt.PromptInput` into prose
text. The interface is the single named seam where a network call may happen, so a
test double replaces it with no network — mirroring the conditions-provider edge.
The default provider calls the Anthropic (Claude) API; the SDK is imported lazily so
importing this package never pulls the SDK in, and so the pure core stays clear of
it (the core-purity boundary test also forbids ``anthropic`` in ``core/``).

The returned text is treated as opaque: it is delivered as-is and never parsed back
into any field. Whether the prose reads as a faithful summary is a documented manual
acceptance check (spec verdict-narrative), not a mechanical assertion.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Protocol

from .prompt import PromptInput

logger = logging.getLogger(__name__)

# The framing given to the model. It is constant, so it does not affect the cache
# key; it instructs the model to explain the supplied terms and invent nothing.
SYSTEM_PROMPT = (
    "You are an astronomy assistant. You are given a machine-computed observing "
    "verdict for tonight as JSON: the go/no-go verdict, a 0-100 score, a confidence "
    "band, an itemized list of reasons, and the top-ranked deep-sky targets. Write a "
    "short, plain-language paragraph (two to four sentences) that explains this "
    "verdict to a stargazer: whether tonight is worth setting up for and what to "
    "point at. Use only the facts in the JSON — introduce no numbers, objects, or "
    "claims that are not present. Do not restate the raw JSON; summarize it."
)

# A conservative output cap: the narrative is a short paragraph, so a small budget
# keeps latency and cost low on a cache miss.
MAX_TOKENS = 400


class Provider(Protocol):
    """Anything that can turn a prompt input into prose text.

    ``generate`` may raise, block, or return an empty string; the explainer wrapper
    is the graceful boundary that turns any of those into "no narrative".
    """

    def generate(self, prompt: PromptInput) -> str: ...


@dataclass
class FakeProvider:
    """A network-free provider double: returns fixed text and counts its calls."""

    text: str = "Tonight looks worth it."
    calls: int = 0

    def generate(self, prompt: PromptInput) -> str:
        self.calls += 1
        return self.text


def _key_is_usable(api_key: str | None) -> bool:
    """An API key is usable only if it is non-empty and fully expanded.

    An unset ``${ENV}`` reference is left as its literal ``${VAR}`` placeholder by
    the config's env expansion, so a key still containing ``${`` means the secret
    was never provided — the provider then degrades to no-narrative rather than
    sending a bad request (design D7).
    """
    return bool(api_key) and "${" not in (api_key or "")


@dataclass
class AnthropicProvider:
    """The default provider: calls the Anthropic (Claude) API for the narrative.

    ``client`` is injectable so tests drive a mocked SDK client with no network; in
    production it is created lazily from ``api_key`` (and ``timeout``). A missing or
    unexpanded key degrades to an empty string — the wrapper reads that as "no
    narrative" — so an unconfigured secret never raises.
    """

    model: str
    api_key: str | None = None
    timeout: float = 10.0
    client: Any | None = None
    _client: Any | None = field(default=None, init=False, repr=False)

    def _get_client(self) -> Any | None:
        if self.client is not None:
            return self.client
        if self._client is not None:
            return self._client
        if not _key_is_usable(self.api_key):
            return None
        import anthropic  # imported lazily so importing this package never needs the SDK

        # No client-side retries: the explainer is bounded and degrades gracefully,
        # so a retry storm must not eat the publish thread's timeout budget.
        self._client = anthropic.Anthropic(
            api_key=self.api_key, timeout=self.timeout, max_retries=0
        )
        return self._client

    def generate(self, prompt: PromptInput) -> str:
        client = self._get_client()
        if client is None:
            logger.warning("explainer provider has no usable API key; no narrative produced")
            return ""
        message = client.messages.create(
            model=self.model,
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt.text}],
            output_config={"effort": "low"},
        )
        return _extract_text(message)


def _extract_text(message: Any) -> str:
    """Join the text blocks of an Anthropic message response into one string."""
    parts = [
        getattr(block, "text", "")
        for block in getattr(message, "content", [])
        if getattr(block, "type", None) == "text"
    ]
    return "".join(parts).strip()
