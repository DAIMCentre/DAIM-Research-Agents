"""Offline tests for ClaudeModel: a fake client stands in for the API."""

from types import SimpleNamespace

import pytest

from daim_research_agents import (
    AgentState,
    ClaudeModel,
    DraftAnswer,
    ModelResponseError,
    build_evidence_registry,
    evaluate_trace,
    run_agent,
)


EVIDENCE = [
    {"evidence_id": "E-1", "title": "First"},
    {"evidence_id": "E-2", "title": "Second"},
]


def tool_use(name, arguments=None):
    return SimpleNamespace(type="tool_use", name=name, input=arguments or {})


def response(*blocks, stop_reason="tool_use"):
    return SimpleNamespace(content=list(blocks), stop_reason=stop_reason)


class FakeClient:
    """Replays scripted responses and records every request body."""

    def __init__(self, responses):
        self._responses = list(responses)
        self.requests = []
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self._create))

    def _create(self, **request):
        self.requests.append(request)
        return self._responses.pop(0)


def test_claude_model_drives_the_existing_loop_to_the_human_gate() -> None:
    client = FakeClient(
        [
            response(tool_use("list_evidence")),
            response(tool_use("read_evidence", {"evidence_id": "E-1"})),
            response(
                tool_use(
                    "submit_draft",
                    {
                        "text": "E-1 is relevant.",
                        "cited_evidence_ids": ["E-1"],
                        "review_questions": ["Is E-2 needed?"],
                    },
                )
            ),
        ]
    )
    state = run_agent("Q?", ClaudeModel(client=client), build_evidence_registry(EVIDENCE))

    assert state.status == "waiting_for_human_review"
    assert state.draft == DraftAnswer("E-1 is relevant.", ("E-1",), ("Is E-2 needed?",))
    report = evaluate_trace(state)
    assert report["all_citations_were_observed"] is True
    assert report["unresolved_evidence_ids"] == ["E-2"]
    assert len(client.requests) == 3


def test_each_request_is_rebuilt_from_the_trace() -> None:
    client = FakeClient([response(tool_use("list_evidence")), response(tool_use("list_evidence"))])
    run_agent("Q?", ClaudeModel(client=client), build_evidence_registry(EVIDENCE), max_steps=2)

    first, second = (request["messages"] for request in client.requests)
    assert len(first) == len(second) == 1
    assert "E-1" not in first[0]["content"]
    assert "E-1" in second[0]["content"]


def test_request_uses_default_model_strict_tools_and_fallbacks(monkeypatch) -> None:
    monkeypatch.delenv("DAIM_AGENT_MODEL", raising=False)
    request = ClaudeModel(client=object()).build_request(AgentState("Q?", max_steps=3))

    assert request["model"] == "claude-opus-5-5"
    assert request["tool_choice"] == {"type": "auto", "disable_parallel_tool_use": True}
    assert all(tool["strict"] for tool in request["tools"])
    assert request["fallbacks"] == "default"


def test_model_can_be_chosen_by_environment(monkeypatch) -> None:
    monkeypatch.setenv("DAIM_AGENT_MODEL", "claude-haiku-5-5")
    model = ClaudeModel(client=object())
    request = model.build_request(AgentState("Q?", max_steps=3))

    assert model.name == "claude:claude-haiku-5-5"
    assert "fallbacks" not in request


@pytest.mark.parametrize(
    ("reply", "message"),
    [
        (response(stop_reason="refusal"), "declined"),
        (response(stop_reason="max_tokens"), "max_tokens"),
        (response(SimpleNamespace(type="text", text="hi"), stop_reason="end_turn"), "without calling"),
        (response(tool_use("submit_draft", {"text": "", "cited_evidence_ids": [], "review_questions": []})), "invalid"),
    ],
)
def test_unusable_responses_fail_clearly(reply, message) -> None:
    model = ClaudeModel(client=FakeClient([reply]))
    with pytest.raises(ModelResponseError, match=message):
        model.next_action(AgentState("Q?", max_steps=3))


def test_unknown_tool_from_model_is_stopped_by_the_registry() -> None:
    client = FakeClient([response(tool_use("delete_everything"))])
    state = run_agent("Q?", ClaudeModel(client=client), build_evidence_registry(EVIDENCE))

    assert state.status == "stopped_tool_error"
    assert "unknown tool" in state.stop_reason
