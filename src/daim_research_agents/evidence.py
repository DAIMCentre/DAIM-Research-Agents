"""Read and write small, human-readable evidence records."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml


class EvidenceError(ValueError):
    """Raised when an evidence record cannot be understood safely."""


def load_yaml(path: str | Path) -> dict[str, Any]:
    """Load one YAML mapping and report malformed records clearly."""
    input_path = Path(path)
    try:
        with input_path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
    except OSError as exc:
        raise EvidenceError(f"could not read {input_path}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise EvidenceError(f"malformed YAML in {input_path}: {exc}") from exc

    if not isinstance(data, Mapping):
        raise EvidenceError(f"{input_path} must contain a YAML mapping at its top level")
    return dict(data)


def save_yaml(record: Mapping[str, Any], path: str | Path) -> Path:
    """Write one structured record, creating only its parent directory."""
    if not isinstance(record, Mapping):
        raise EvidenceError("record must be a mapping")

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with output_path.open("w", encoding="utf-8") as handle:
            yaml.safe_dump(dict(record), handle, sort_keys=False, allow_unicode=True)
    except OSError as exc:
        raise EvidenceError(f"could not write {output_path}: {exc}") from exc
    return output_path


def load_agent_case(path: str | Path) -> dict[str, Any]:
    """Load the question and supplied evidence for one bounded agent run."""
    record = load_yaml(path)
    question = record.get("question")
    evidence = record.get("evidence")
    if not isinstance(question, str) or not question.strip():
        raise EvidenceError("agent case is missing a non-empty question")
    if not isinstance(evidence, list):
        raise EvidenceError("agent case is missing an evidence list")
    for index, item in enumerate(evidence, start=1):
        if not isinstance(item, Mapping):
            raise EvidenceError(f"evidence item {index} must be a mapping")
        for field in ("evidence_id", "title"):
            if not isinstance(item.get(field), str) or not item[field].strip():
                raise EvidenceError(f"evidence item {index} is missing {field}")
    return record
