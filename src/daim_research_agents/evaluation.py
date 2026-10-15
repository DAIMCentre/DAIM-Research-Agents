"""Structural evaluation that never decides whether a claim is true."""

from __future__ import annotations

from typing import Any

from .types import AgentState


def evaluate_trace(state: AgentState) -> dict[str, Any]:
    cited = set(state.draft.cited_evidence_ids if state.draft else ())
    observed = set(state.observed_evidence_ids)
    available = set(state.available_evidence_ids)
    tool_calls = [event for event in state.events if event.get("kind") == "tool_call"]
    tool_errors = [
        event
        for event in state.events
        if event.get("kind") == "observation" and not event.get("success")
    ]
    human_gate_reached = state.draft is not None
    return {
        "steps": state.step_count,
        "tool_calls": len(tool_calls),
        "tool_errors": len(tool_errors),
        "all_citations_were_observed": cited <= observed,
        "all_citations_exist": cited <= available,
        "human_gate_reached": human_gate_reached,
        "completed_without_approval": state.status == "completed" and state.review_decision != "approve",
        "stop_reason": state.stop_reason,
        "unresolved_evidence_ids": sorted(available - observed),
    }
