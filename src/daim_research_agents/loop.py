"""A synchronous act-observe loop with a non-bypassable human gate."""

from __future__ import annotations

from dataclasses import asdict

from .model import AgentModel
from .tools import ToolRegistry, observation_record
from .types import AgentState, DraftAnswer, ToolCall


class AgentError(RuntimeError):
    """Raised when the model or state violates the loop contract."""


def run_agent(
    question: str,
    model: AgentModel,
    registry: ToolRegistry,
    *,
    max_steps: int = 10,
) -> AgentState:
    """Run until a draft, tool error or explicit step limit is reached."""
    if not isinstance(question, str) or not question.strip():
        raise ValueError("question must be non-empty text")
    if not isinstance(max_steps, int) or isinstance(max_steps, bool) or max_steps <= 0:
        raise ValueError("max_steps must be a positive integer")
    state = AgentState(question=question.strip(), max_steps=max_steps)

    while state.step_count < max_steps:
        state.step_count += 1
        action = model.next_action(state)
        if isinstance(action, ToolCall):
            state.events.append(
                {"step": state.step_count, "kind": "tool_call", **asdict(action)}
            )
            observation = registry.execute(action)
            state.events.append(
                {"step": state.step_count, "kind": "observation", **observation_record(observation)}
            )
            if not observation.success:
                state.status = "stopped_tool_error"
                state.stop_reason = observation.error
                return state
            if action.name == "list_evidence":
                items = observation.data.get("evidence", [])
                state.available_evidence_ids = [item["evidence_id"] for item in items]
            elif action.name == "read_evidence":
                evidence_id = observation.data.get("evidence_id")
                if evidence_id not in state.observed_evidence_ids:
                    state.observed_evidence_ids.append(evidence_id)
            continue
        if isinstance(action, DraftAnswer):
            state.draft = action
            state.events.append(
                {"step": state.step_count, "kind": "draft", **asdict(action)}
            )
            state.status = "waiting_for_human_review"
            state.stop_reason = "draft_ready"
            return state
        raise AgentError("model output must be ToolCall or DraftAnswer")

    state.status = "stopped_step_limit"
    state.stop_reason = "maximum steps reached"
    return state


def review_agent_run(state: AgentState, decision: str, *, note: str | None = None) -> AgentState:
    """Apply a decision that the model cannot issue for itself."""
    if state.status != "waiting_for_human_review" or state.draft is None:
        raise AgentError("only a draft waiting for human review can be reviewed")
    statuses = {
        "approve": "completed",
        "reject": "rejected",
        "revision": "waiting_for_revision",
    }
    if decision not in statuses:
        raise ValueError("decision must be approve, reject or revision")
    state.review_decision = decision
    state.review_note = note
    state.status = statuses[decision]
    state.stop_reason = f"human_{decision}"
    state.events.append(
        {
            "step": state.step_count,
            "kind": "human_review",
            "decision": decision,
            "note": note,
        }
    )
    return state
