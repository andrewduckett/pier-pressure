"""The optional LLM explainer edge (proposal M7; ADR-0011; design D1-D7).

This package turns an already-computed verdict document into a short prose narrative
and lives entirely at the service edge — it is network-facing and non-deterministic,
so the pure ``core`` never imports it (the core-purity boundary test forbids both
``pierpressure.explain`` and ``anthropic`` in ``core/``). The narrative is delivered
as a separate Home Assistant entity, never merged into the verdict document, so the
numbers document stays byte-identical whether or not the explainer runs.

The explainer is disabled by default: :func:`build_explainer` returns a no-op unless
configuration enables it. When enabled, prose is obtained through a swappable
:class:`Provider` (default: a Pydantic AI provider whose ``model`` string selects any
supported LLM provider), cached on the exact prompt input, and produced under a
bounded timeout that degrades to no-narrative on any failure.
"""

from __future__ import annotations

from .explainer import (
    DEFAULT_TIMEOUT,
    Explainer,
    NarrativeExplainer,
    build_explainer,
    no_op_explainer,
)
from .prompt import PROMPT_TARGET_LIMIT, PromptInput, build_prompt_input
from .provider import FakeProvider, Provider, PydanticAIProvider

__all__ = [
    "DEFAULT_TIMEOUT",
    "PROMPT_TARGET_LIMIT",
    "Explainer",
    "FakeProvider",
    "NarrativeExplainer",
    "PromptInput",
    "Provider",
    "PydanticAIProvider",
    "build_explainer",
    "build_prompt_input",
    "no_op_explainer",
]
