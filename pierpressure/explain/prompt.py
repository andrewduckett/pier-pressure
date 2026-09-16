"""The prompt-input builder for the explainer edge (design D6).

The provider input is derived only from the finished verdict's terms — the verdict
value, the score, the confidence, the ``reasons`` list, and the emitted fields of
the top-ranked targets — never from any astronomy, conditions, or ranking source.
:func:`build_prompt_input` renders those terms into a canonical string so the same
document always produces the same bytes, which is both what the provider sees and
what the narrative cache keys on (design D4). ``generated_at`` is excluded: it is
not part of the prompt, so successive recomputes of an unchanged verdict build an
identical prompt and reuse one narrative.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from pierpressure.core.model import VerdictDocument

# How many top-ranked targets the prose may mention. The list is already ranked by
# the core, so the first few are the ones worth naming; keeping the count fixed
# keeps the prompt (and its cache key) stable and bounded.
PROMPT_TARGET_LIMIT = 3


@dataclass(frozen=True)
class PromptInput:
    """The exact, canonical bytes handed to the provider as the prompt data.

    ``text`` is a deterministic JSON rendering of the verdict terms; ``key`` is a
    stable hash of those bytes, so the cache is keyed on precisely what influences
    the prose — no prompt-influencing field can drift out of the key (design D4).
    """

    text: str

    @property
    def key(self) -> str:
        return hashlib.sha256(self.text.encode("utf-8")).hexdigest()


def build_prompt_input(
    document: VerdictDocument, *, target_limit: int = PROMPT_TARGET_LIMIT
) -> PromptInput:
    """Build the canonical prompt input from a finished verdict document.

    Only the verdict, score, confidence, reasons, and the top ``target_limit``
    targets' emitted fields are included. Each target is rendered through the
    document's own serialization so the prompt carries exactly the emitted (rounded)
    field values, and JSON keys are sorted so the bytes are order-independent and
    stable across runs.
    """
    payload = {
        "verdict": document.verdict.value,
        "score": document.score,
        "confidence": {
            "band": document.confidence.band.value,
            "value": document.confidence.value,
        },
        "reasons": list(document.reasons),
        "targets": [
            json.loads(target.model_dump_json()) for target in document.targets[:target_limit]
        ],
    }
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return PromptInput(text=text)
