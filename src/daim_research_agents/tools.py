"""A tiny registry containing only explicit, read-only evidence tools."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict
from typing import Any

from .types import Observation, ToolCall


class ToolError(ValueError):
    """A safe, expected tool validation or execution error."""


ToolFunction = Callable[..., Any]


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, tuple[ToolFunction, frozenset[str]]] = {}

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._tools))

    def register(self, name: str, function: ToolFunction, *, required_arguments: Sequence[str] = ()) -> None:
        if not isinstance(name, str) or not name.strip():
            raise ValueError("tool name must be non-empty text")
        if name in self._tools:
            raise ValueError(f"tool already registered: {name}")
        self._tools[name] = (function, frozenset(required_arguments))

    def execute(self, call: ToolCall) -> Observation:
        registered = self._tools.get(call.name)
        if registered is None:
            return Observation(call.name, False, error=f"unknown tool: {call.name}")
        function, required = registered
        missing = sorted(required - call.arguments.keys())
        if missing:
            return Observation(
                call.name,
                False,
                error=f"missing required tool arguments: {', '.join(missing)}",
            )
        unexpected = sorted(call.arguments.keys() - required)
        if unexpected:
            return Observation(
                call.name,
                False,
                error=f"unexpected tool arguments: {', '.join(unexpected)}",
            )
        try:
            return Observation(call.name, True, data=function(**call.arguments))
        except ToolError as exc:
            return Observation(call.name, False, error=str(exc))
        except Exception as exc:  # pragma: no cover - defensive boundary
            return Observation(call.name, False, error=f"tool failed safely: {type(exc).__name__}")


class EvidenceStore:
    """Validate supplied evidence and expose two read-only operations."""

    def __init__(self, evidence: Sequence[Mapping[str, Any]]) -> None:
        self._records: dict[str, dict[str, Any]] = {}
        for index, item in enumerate(evidence, start=1):
            if not isinstance(item, Mapping):
                raise ValueError(f"evidence item {index} must be a mapping")
            evidence_id = item.get("evidence_id")
            title = item.get("title")
            if not isinstance(evidence_id, str) or not evidence_id.strip():
                raise ValueError(f"evidence item {index} is missing evidence_id")
            if not isinstance(title, str) or not title.strip():
                raise ValueError(f"evidence item {index} is missing title")
            if evidence_id in self._records:
                raise ValueError(f"duplicate evidence_id: {evidence_id}")
            self._records[evidence_id] = dict(item)

    def list_evidence(self) -> dict[str, Any]:
        return {
            "evidence": [
                {"evidence_id": evidence_id, "title": self._records[evidence_id]["title"]}
                for evidence_id in sorted(self._records)
            ]
        }

    def read_evidence(self, evidence_id: str) -> dict[str, Any]:
        try:
            return dict(self._records[evidence_id])
        except KeyError as exc:
            raise ToolError(f"unknown evidence_id: {evidence_id}") from exc


def build_evidence_registry(evidence: Sequence[Mapping[str, Any]]) -> ToolRegistry:
    store = EvidenceStore(evidence)
    registry = ToolRegistry()
    registry.register("list_evidence", store.list_evidence)
    registry.register("read_evidence", store.read_evidence, required_arguments=("evidence_id",))
    return registry


def observation_record(observation: Observation) -> dict[str, Any]:
    return asdict(observation)
