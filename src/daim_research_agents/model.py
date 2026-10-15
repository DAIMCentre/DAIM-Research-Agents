"""The narrow model interface and a deterministic teaching policy."""

from __future__ import annotations

from typing import Protocol

from .types import AgentAction, AgentState, DraftAnswer, ToolCall


class AgentModel(Protocol):
    """Anything that chooses the next typed action from explicit state."""

    name: str

    def next_action(self, state: AgentState) -> AgentAction:
        ...


class ScriptedModel:
    """An inspectable policy: list, read every record, then draft."""

    name = "scripted-model-v1"

    def next_action(self, state: AgentState) -> AgentAction:
        listed = any(
            event.get("kind") == "observation" and event.get("tool_name") == "list_evidence"
            for event in state.events
        )
        if not listed:
            return ToolCall("list_evidence")

        unread = [
            evidence_id
            for evidence_id in state.available_evidence_ids
            if evidence_id not in state.observed_evidence_ids
        ]
        if unread:
            return ToolCall("read_evidence", {"evidence_id": unread[0]})

        cited = tuple(state.observed_evidence_ids)
        if cited:
            text = (
                "The supplied evidence records have been collected for human review: "
                + ", ".join(cited)
                + ". No scientific conclusion has been made automatically."
            )
        else:
            text = "No evidence records were supplied, so no scientific conclusion can be drafted."
        return DraftAnswer(
            text=text,
            cited_evidence_ids=cited,
            review_questions=(
                "Does each cited record support the wording used in this draft?",
                "What contrary evidence or disciplinary context is missing?",
                "Should the draft be approved, rejected or returned for revision?",
            ),
        )
