"""The AI Task provider (addon-explainer-ai-task DD1-DD3, DD7).

The provider asks a Home Assistant AI Task entity for the narrative through the
Supervisor's Core API. Every test drives it with an injected ``httpx.MockTransport``
or a patched socket, so no test reaches the network.
"""

from __future__ import annotations

import json
import logging
import socket
import threading
import time
from typing import Any

import httpx
import pytest

from pierpressure.explain import NarrativeExplainer, build_prompt_input
from pierpressure.explain.ai_task import AiTaskProvider
from pierpressure.explain.provider import SYSTEM_PROMPT

from .test_explainer import _document

TOKEN = "tok-3e9a"
ENTITY = "ai_task.openai"


def _reply(data: Any = "Clear skies.") -> httpx.Response:
    return httpx.Response(
        200,
        json={"changed_states": [], "service_response": {"conversation_id": "c1", "data": data}},
    )


def _provider(handler: Any) -> AiTaskProvider:
    client = httpx.Client(transport=httpx.MockTransport(handler))
    return AiTaskProvider(entity_id=ENTITY, token=TOKEN, client=client)


# --------------------------------------------------------------------------- #
# 2.1 — the request
# --------------------------------------------------------------------------- #


def test_the_request_goes_to_the_generate_data_action() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return _reply()

    _provider(handler).generate(build_prompt_input(_document()))

    assert len(requests) == 1
    assert requests[0].method == "POST"
    assert str(requests[0].url) == (
        "http://supervisor/core/api/services/ai_task/generate_data?return_response"
    )


def test_the_request_carries_the_supervisor_token() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return _reply()

    _provider(handler).generate(build_prompt_input(_document()))

    assert requests[0].headers["Authorization"] == f"Bearer {TOKEN}"


def test_the_body_names_the_entity_with_no_other_fields() -> None:
    bodies: list[dict[str, Any]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        bodies.append(json.loads(request.content))
        return _reply()

    _provider(handler).generate(build_prompt_input(_document()))

    assert set(bodies[0]) == {"task_name", "instructions", "entity_id"}
    assert bodies[0]["entity_id"] == ENTITY


def test_the_instructions_hold_the_framing_then_the_verdict_prompt() -> None:
    bodies: list[dict[str, Any]] = []
    prompt = build_prompt_input(_document())

    def handler(request: httpx.Request) -> httpx.Response:
        bodies.append(json.loads(request.content))
        return _reply()

    _provider(handler).generate(prompt)

    instructions = bodies[0]["instructions"]
    assert instructions.startswith(SYSTEM_PROMPT)
    assert instructions.endswith(prompt.text)


def test_the_request_bypasses_proxy_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HTTP_PROXY", "http://proxy.example:3128")
    monkeypatch.setenv("ALL_PROXY", "http://proxy.example:3128")
    reached: list[str] = []

    def record(address: tuple[str, int], *_args: Any, **_kwargs: Any) -> socket.socket:
        reached.append(address[0])
        raise OSError("blocked in test")

    monkeypatch.setattr(socket, "create_connection", record)
    provider = AiTaskProvider(entity_id=ENTITY, token=TOKEN)

    with pytest.raises(httpx.ConnectError):
        provider.generate(build_prompt_input(_document()))

    assert reached == ["supervisor"]


def _explainer(handler: Any) -> NarrativeExplainer:
    return NarrativeExplainer(_provider(handler))


# --------------------------------------------------------------------------- #
# 2.2 — the reply
# --------------------------------------------------------------------------- #


def test_a_text_reply_becomes_the_stripped_narrative() -> None:
    explainer = _explainer(lambda _request: _reply(" Clear skies. "))

    assert explainer(_document()) == "Clear skies."


@pytest.mark.parametrize(
    "reply",
    [
        httpx.Response(200, text="not json"),
        httpx.Response(200, json={"changed_states": [], "service_response": {}}),
        httpx.Response(200, json={"changed_states": []}),
        httpx.Response(200, json=["not", "a", "mapping"]),
        _reply(""),
        _reply("   "),
        _reply({"text": "Clear skies."}),
        _reply(None),
    ],
    ids=["not-json", "no-data", "no-service-response", "list", "empty", "blank", "mapping", "null"],
)
def test_a_reply_without_text_gives_no_narrative(reply: httpx.Response) -> None:
    explainer = _explainer(lambda _request: reply)

    assert explainer(_document()) is None


# --------------------------------------------------------------------------- #
# 2.3 — failures and the log line
# --------------------------------------------------------------------------- #

REJECTION = {"message": "AI Task entity ai_task.marker90 not found."}


def _secrets_absent(caplog: pytest.LogCaptureFixture) -> None:
    for text in ("marker90", "not found", TOKEN):
        assert text not in caplog.text


@pytest.mark.parametrize("status", [400, 401, 403, 500, 502])
def test_an_error_status_gives_no_narrative(status: int) -> None:
    explainer = _explainer(lambda _request: httpx.Response(status, json=REJECTION))

    assert explainer(_document()) is None


@pytest.mark.parametrize("status", [400, 401, 403, 500, 502])
def test_an_error_status_is_logged_by_kind_and_status_only(
    caplog: pytest.LogCaptureFixture, status: int
) -> None:
    explainer = _explainer(lambda _request: httpx.Response(status, json=REJECTION))

    with caplog.at_level(logging.DEBUG):
        explainer(_document())

    failures = [r.getMessage() for r in caplog.records if "explainer provider" in r.getMessage()]
    assert failures == [f"explainer provider failed: AiTaskError (HTTP {status}); no narrative"]
    _secrets_absent(caplog)


def test_a_refused_connection_gives_no_narrative(caplog: pytest.LogCaptureFixture) -> None:
    def refuse(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("[Errno 111] Connection refused", request=request)

    with caplog.at_level(logging.DEBUG):
        narrative = _explainer(refuse)(_document())

    assert narrative is None
    assert "explainer provider failed: ConnectError; no narrative" in caplog.text
    assert TOKEN not in caplog.text


def test_a_request_that_never_answers_gives_up_within_the_bound(
    caplog: pytest.LogCaptureFixture,
) -> None:
    release = threading.Event()

    def hang(_request: httpx.Request) -> httpx.Response:
        release.wait(5.0)
        return _reply()

    explainer = NarrativeExplainer(_provider(hang), timeout=0.2)
    start = time.monotonic()
    try:
        with caplog.at_level(logging.DEBUG):
            narrative = explainer(_document())
        elapsed = time.monotonic() - start
    finally:
        release.set()

    assert narrative is None
    assert elapsed < 1.0
    assert TOKEN not in caplog.text


def test_a_failed_call_is_retried_on_the_next_recompute() -> None:
    replies = iter([httpx.Response(500), _reply("Clear skies.")])
    explainer = _explainer(lambda _request: next(replies))

    assert explainer(_document()) is None
    assert explainer(_document()) == "Clear skies."
