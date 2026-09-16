"""The explainer provider interface and its default Pydantic AI implementation (D3).

A provider turns a built :class:`~pierpressure.explain.prompt.PromptInput` into prose
text. The interface is the single named seam where a network call may happen, so a
test double replaces it with no network — mirroring the conditions-provider edge.

The default provider uses `Pydantic AI <https://ai.pydantic.dev>`_, which is
model-agnostic: the configured ``model`` string (e.g. ``"anthropic:claude-opus-5"``,
``"openai:gpt-4o"``, ``"google-gla:gemini-1.5-flash"``) selects the LLM provider, so
no provider is hard-coded. Pydantic AI is imported lazily so importing this package
never pulls it in, and so the pure core stays clear of it (the core-purity boundary
test also forbids ``pydantic_ai`` in ``core/``).

The returned text is treated as opaque: it is delivered as-is and never parsed back
into any field. Whether the prose reads as a faithful summary is a documented manual
acceptance check (spec verdict-narrative), not a mechanical assertion.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Protocol

from .prompt import PromptInput

logger = logging.getLogger(__name__)

# The default per-call timeout handed to the provider's own client, so a slow model
# self-aborts before the explainer wrapper's (slightly larger) hard bound (design D5).
PROVIDER_TIMEOUT = 5.0

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

# The standard environment variable each supported provider reads its key from.
# When an ``api_key`` is set in config, it is exported to the variable for the
# model's provider prefix; a provider outside this map takes its credentials from
# the environment directly (Pydantic AI resolves them). These names are stable
# provider conventions, not values invented here.
_PROVIDER_KEY_ENV = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "google-gla": "GEMINI_API_KEY",
    "google": "GEMINI_API_KEY",
    "google-vertex": "GOOGLE_API_KEY",
}


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
    was never provided (design D7).
    """
    return bool(api_key) and "${" not in (api_key or "")


@contextmanager
def _provider_key_env(model: str, api_key: str | None) -> Iterator[None]:
    """Expose a configured key to the provider only for the duration of one call.

    Pydantic AI reads each provider's key from its standard environment variable.
    Rather than write the secret into ``os.environ`` for the whole process lifetime
    (where it would outlive the call and be visible to any later-spawned process),
    this sets the variable only around the model call and restores the prior value
    afterwards — provider-agnostic, with no per-provider client wiring. A key for a
    provider outside the known map, or an unusable key, is left to the environment.
    """
    if not _key_is_usable(api_key):
        yield
        return
    env_name = _PROVIDER_KEY_ENV.get(model.split(":", 1)[0])
    if env_name is None:
        logger.warning(
            "explainer api_key is set but provider %r has no known key variable; "
            "supply its credentials in the environment instead",
            model.split(":", 1)[0],
        )
        yield
        return
    assert api_key is not None  # narrowed by _key_is_usable above
    previous = os.environ.get(env_name)
    os.environ[env_name] = api_key
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop(env_name, None)
        else:
            os.environ[env_name] = previous


@dataclass
class PydanticAIProvider:
    """The default provider: obtains prose through Pydantic AI, model-agnostically.

    ``model`` is a Pydantic AI model spec (``"provider:model-name"``); it selects the
    LLM provider, so nothing here is Anthropic-specific. When ``api_key`` is set, it is
    exposed to the provider's standard key variable for the call only (design D7);
    otherwise the key is taken from the environment. ``model_obj`` injects a Pydantic
    AI ``Model`` (a ``TestModel``/``FunctionModel``) so tests run with no network. A
    missing or unexpanded key raises inside Pydantic AI, which the explainer wrapper
    turns into "no narrative" — an unconfigured secret never crashes the service.
    """

    model: str
    api_key: str | None = None
    timeout: float = PROVIDER_TIMEOUT
    max_tokens: int = MAX_TOKENS
    model_obj: Any | None = None

    def generate(self, prompt: PromptInput) -> str:
        # Silence Pydantic AI's one-time startup banner at first use (not at import,
        # so importing this package — e.g. with the explainer disabled — has no
        # side effect). setdefault respects an operator's own choice.
        os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")
        # Imported lazily so importing this package never needs Pydantic AI, and so
        # the pure core (which the boundary test guards) can never pull it in.
        from pydantic_ai import Agent
        from pydantic_ai.settings import ModelSettings

        model = self.model_obj if self.model_obj is not None else self.model
        with _provider_key_env(self.model, self.api_key):
            agent: Any = Agent(
                model,
                system_prompt=SYSTEM_PROMPT,
                model_settings=ModelSettings(max_tokens=self.max_tokens, timeout=self.timeout),
            )
            result = agent.run_sync(prompt.text)
        return str(result.output).strip()
