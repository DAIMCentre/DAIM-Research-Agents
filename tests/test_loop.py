import pytest

from daim_research_agents import (
    AgentError,
    DraftAnswer,
    ScriptedModel,
    ToolCall,
    ToolRegistry,
    build_evidence_registry,
    review_agent_run,
    run_agent,
)


EVIDENCE = [
    {"evidence_id": "E-1", "title": "First"},
    {"evidence_id": "E-2", "title": "Second"},
]


def completed_draft_state():
    return run_agent("What is supplied?", ScriptedModel(), build_evidence_registry(EVIDENCE))


def test_scripted_loop_is_deterministic_and_stops_at_human_gate() -> None:
    first = completed_draft_state()
    second = completed_draft_state()
    assert first.to_record() == second.to_record()
    assert first.status == "waiting_for_human_review"
    assert first.observed_evidence_ids == ["E-1", "E-2"]
    assert first.draft is not None
    assert first.draft.cited_evidence_ids == ("E-1", "E-2")


def test_human_review_is_an_explicit_transition() -> None:
    assert review_agent_run(completed_draft_state(), "approve").status == "completed"
    assert review_agent_run(completed_draft_state(), "reject").status == "rejected"
    assert review_agent_run(completed_draft_state(), "revision").status == "waiting_for_revision"


def test_review_cannot_bypass_draft_gate() -> None:
    class RepeatingModel:
        name = "repeat"

        def next_action(self, state):
            return ToolCall("list_evidence")

    state = run_agent("Question", RepeatingModel(), build_evidence_registry(EVIDENCE), max_steps=1)
    assert state.status == "stopped_step_limit"
    with pytest.raises(AgentError, match="waiting for human review"):
        review_agent_run(state, "approve")


def test_tool_error_is_retained_and_stops_safely() -> None:
    class UnknownToolModel:
        name = "bad-tool"

        def next_action(self, state):
            return ToolCall("not_registered")

    state = run_agent("Question", UnknownToolModel(), ToolRegistry())
    assert state.status == "stopped_tool_error"
    assert state.events[-1]["success"] is False
    assert "unknown tool" in state.events[-1]["error"]


def test_invalid_model_output_fails_clearly() -> None:
    class InvalidModel:
        name = "invalid"

        def next_action(self, state):
            return "free-form text"

    with pytest.raises(AgentError, match="ToolCall or DraftAnswer"):
        run_agent("Question", InvalidModel(), ToolRegistry())
