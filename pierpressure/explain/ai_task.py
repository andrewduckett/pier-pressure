"""The AI Task provider: the narrative from a Home Assistant AI Task entity (DD1-DD3).

Inside the add-on, the explainer can ask Home Assistant's ``ai_task.generate_data``
action for its prose, through the Supervisor's Core API, instead of calling an LLM
service itself. The user's own Home Assistant AI integration then picks the model
and holds its key.

The provider sits behind the same :class:`~pierpressure.explain.provider.Provider`
protocol as the default one, so :class:`~pierpressure.explain.NarrativeExplainer`
keeps owning the cache, the time bound and the failure log line.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from http import HTTPStatus

import httpx

from .prompt import PromptInput
from .provider import PROVIDER_TIMEOUT, SYSTEM_PROMPT

GENERATE_DATA_URL = "http://supervisor/core/api/services/ai_task/generate_data?return_response"

TASK_NAME = "PierPressure narrative"


class AiTaskError(Exception):
    """Home Assistant gave no narrative text.

    It carries the HTTP status, when the reply was not 200, and never any text from
    the reply, so no log of it can show what Home Assistant said (DD3).
    """

    def __init__(self, status_code: int | None = None) -> None:
        super().__init__()
        self.status_code = status_code


@dataclass
class AiTaskProvider:
    """Asks ``entity_id`` for the narrative through the Supervisor (DD1)."""

    entity_id: str
    token: str = field(repr=False)
    timeout: float = PROVIDER_TIMEOUT
    client: httpx.Client | None = field(default=None, repr=False)

    def generate(self, prompt: PromptInput) -> str:
        if self.client is None:
            # trust_env=False: a proxy named in HTTP_PROXY or ALL_PROXY must never see
            # the Supervisor token (spec "Proxy settings do not reach the AI Task request").
            self.client = httpx.Client(timeout=self.timeout, trust_env=False)
        # The action has no separate system prompt, so the framing goes first (DD2).
        body = {
            "task_name": TASK_NAME,
            "instructions": f"{SYSTEM_PROMPT}\n\n{prompt.text}",
            "entity_id": self.entity_id,
        }
        response = self.client.post(
            GENERATE_DATA_URL, json=body, headers={"Authorization": f"Bearer {self.token}"}
        )
        return _narrative(response)


def _narrative(response: httpx.Response) -> str:
    """The reply's ``service_response.data`` text, or :class:`AiTaskError` (DD3)."""
    if response.status_code != HTTPStatus.OK:
        raise AiTaskError(response.status_code)
    try:
        data = response.json()["service_response"]["data"]
    except ValueError, KeyError, TypeError:
        raise AiTaskError from None
    if not isinstance(data, str) or not data.strip():
        raise AiTaskError
    return data.strip()
