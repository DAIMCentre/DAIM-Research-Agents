"""Explicit data structures for actions, observations and agent state."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class ToolCall:
    name: str
    arguments: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("tool name must be non-empty text")
        if not isinstance(self.arguments, dict):
            raise ValueError("tool arguments must be a dictionary")


@dataclass(frozen=True)
class DraftAnswer:
    text: str
    cited_evidence_ids: tuple[str, ...] = ()
    review_questions: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.text, str) or not self.text.strip():
            raise ValueError("draft text must be non-empty")
        if any(not isinstance(item, str) or not item.strip() for item in self.cited_evidence_ids):
            raise ValueError("cited evidence IDs must be non-empty text")


@dataclass(frozen=True)
class Observation:
    tool_name: str
    success: bool
    data: Any = None
    error: str | None = None


@dataclass
class AgentState:
    question: str
    max_steps: int
    status: str = "running"
    step_count: int = 0
    events: list[dict[str, Any]] = field(default_factory=list)
    available_evidence_ids: list[str] = field(default_factory=list)
    observed_evidence_ids: list[str] = field(default_factory=list)
    draft: DraftAnswer | None = None
    stop_reason: str | None = None
    human_review_required: bool = True
    review_decision: str | None = None
    review_note: str | None = None

    def to_record(self) -> dict[str, Any]:
        return {
            "question": self.question,
            "max_steps": self.max_steps,
            "step_count": self.step_count,
            "status": self.status,
            "stop_reason": self.stop_reason,
            "events": list(self.events),
            "available_evidence_ids": list(self.available_evidence_ids),
            "observed_evidence_ids": list(self.observed_evidence_ids),
            "draft": asdict(self.draft) if self.draft else None,
            "human_review_required": self.human_review_required,
            "review": {
                "decision": self.review_decision,
                "note": self.review_note,
            },
        }


AgentAction = ToolCall | DraftAnswer
