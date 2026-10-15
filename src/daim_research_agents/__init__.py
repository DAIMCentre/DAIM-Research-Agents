"""Bounded, human-review-first research workflow prototypes."""

from .agents import critique_claim, organise_literature, plan_experiment
from .claude_model import ClaudeModel, ModelResponseError
from .evidence import EvidenceError, load_agent_case, load_yaml, save_yaml
from .evaluation import evaluate_trace
from .loop import AgentError, review_agent_run, run_agent
from .model import AgentModel, ScriptedModel
from .tools import EvidenceStore, ToolError, ToolRegistry, build_evidence_registry
from .types import AgentState, DraftAnswer, Observation, ToolCall

__all__ = [
    "AgentError",
    "AgentModel",
    "AgentState",
    "ClaudeModel",
    "DraftAnswer",
    "EvidenceStore",
    "EvidenceError",
    "ModelResponseError",
    "Observation",
    "ScriptedModel",
    "ToolCall",
    "ToolError",
    "ToolRegistry",
    "build_evidence_registry",
    "critique_claim",
    "evaluate_trace",
    "load_agent_case",
    "load_yaml",
    "organise_literature",
    "plan_experiment",
    "save_yaml",
    "review_agent_run",
    "run_agent",
]
