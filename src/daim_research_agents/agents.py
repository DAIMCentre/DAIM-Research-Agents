"""Deterministic workflow helpers corresponding to the three agent specifications."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping
from typing import Any


def _require_mapping(record: Mapping[str, Any] | object) -> Mapping[str, Any]:
    if not isinstance(record, Mapping):
        raise ValueError("input must be a mapping")
    return record


def _require_text(record: Mapping[str, Any], field: str) -> str:
    value = record.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"missing or empty required field: {field}")
    return value.strip()


def _require_list(record: Mapping[str, Any], field: str) -> list[Any]:
    value = record.get(field)
    if not isinstance(value, list):
        raise ValueError(f"missing or invalid required list: {field}")
    return value


def organise_literature(record: Mapping[str, Any]) -> dict[str, Any]:
    """Organise supplied source records without searching or adding evidence."""
    record = _require_mapping(record)
    research_question = _require_text(record, "research_question")
    sources = _require_list(record, "sources")

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    evidence_gaps: list[str] = []
    seen_ids: set[str] = set()

    for index, source in enumerate(sources, start=1):
        if not isinstance(source, Mapping):
            raise ValueError(f"source {index} must be a mapping")
        source_id = source.get("source_id")
        title = source.get("title")
        if not isinstance(source_id, str) or not source_id.strip():
            raise ValueError(f"source {index} is missing source_id")
        if not isinstance(title, str) or not title.strip():
            raise ValueError(f"source {index} is missing title")
        if source_id in seen_ids:
            raise ValueError(f"duplicate source_id: {source_id}")
        seen_ids.add(source_id)

        copied_source = dict(source)
        topic = copied_source.get("topic", "Uncategorised")
        if not isinstance(topic, str) or not topic.strip():
            topic = "Uncategorised"
        grouped[topic.strip()].append(copied_source)
        if not copied_source.get("citation") and not copied_source.get("url"):
            evidence_gaps.append(f"{source_id}: add a citation or retrievable URL")

    if not sources:
        evidence_gaps.append("No sources were supplied; no literature conclusions can be drawn.")

    return {
        "agent": "literature",
        "status": "draft_for_review",
        "research_question": research_question,
        "organised_sources": {topic: grouped[topic] for topic in sorted(grouped)},
        "evidence_gaps": evidence_gaps,
        "review_questions": [
            "Has each citation been checked against the original source?",
            "Are important disciplinary perspectives or contrary findings missing?",
            "Do the headings reflect the research question rather than convenience?",
        ],
        "human_review_required": True,
    }


def plan_experiment(record: Mapping[str, Any]) -> dict[str, Any]:
    """Turn supplied experiment metadata into a reviewable checklist."""
    record = _require_mapping(record)
    research_question = _require_text(record, "research_question")
    hypothesis = _require_text(record, "hypothesis")
    data = record.get("data")
    configuration = record.get("configuration")
    if not isinstance(data, Mapping):
        raise ValueError("missing or invalid required mapping: data")
    if not isinstance(configuration, Mapping):
        raise ValueError("missing or invalid required mapping: configuration")

    recommended_fields = [
        "experiment_id",
        "date",
        "researcher",
        "code_reference",
        "result_files",
        "interpretation",
        "limitations",
        "review_status",
    ]
    unresolved_fields = [field for field in recommended_fields if record.get(field) in (None, "", [])]

    return {
        "agent": "experiment",
        "status": "draft_for_review",
        "research_question": research_question,
        "hypothesis": hypothesis,
        "supplied_data": dict(data),
        "supplied_configuration": dict(configuration),
        "checklist": {
            "question_and_hypothesis": [
                "Confirm the prediction or observation that would count against the hypothesis.",
                "Confirm that the planned analysis can address the stated question.",
            ],
            "data_and_design": [
                "Check provenance, access conditions, exclusions and train/test boundaries.",
                "Name appropriate baselines, controls and sources of uncertainty.",
            ],
            "recording": [
                "Freeze code and configuration references before interpreting results.",
                "Preserve result files, failed runs, limitations and software versions.",
            ],
            "review": [
                "Obtain domain and methods review before running where required.",
                "Record who accepts, changes or rejects the final interpretation.",
            ],
        },
        "unresolved_fields": unresolved_fields,
        "review_questions": [
            "Are ethical, governance or safety approvals required?",
            "Could preprocessing or model selection leak information from evaluation data?",
            "Are the proposed metrics meaningful in the target discipline?",
        ],
        "human_review_required": True,
    }


def critique_claim(record: Mapping[str, Any]) -> dict[str, Any]:
    """Expose review questions without deciding whether a claim is true."""
    record = _require_mapping(record)
    claim = _require_text(record, "claim")
    supporting_evidence = _require_list(record, "supporting_evidence")
    limitations = record.get("limitations", [])
    if not isinstance(limitations, list):
        raise ValueError("limitations must be a list when provided")

    evidence_gaps: list[str] = []
    if not supporting_evidence:
        evidence_gaps.append("No supporting evidence identifiers were supplied.")
    if not limitations:
        evidence_gaps.append("No limitations were supplied.")
    if record.get("confidence") in (None, ""):
        evidence_gaps.append("No confidence description was supplied.")

    return {
        "agent": "critic",
        "status": "draft_for_review",
        "claim": claim,
        "supporting_evidence": list(supporting_evidence),
        "stated_limitations": list(limitations),
        "evidence_gaps": evidence_gaps,
        "scope_concerns": [
            "Check whether the claim covers more settings, populations or domains than the evidence.",
            "Check whether causal language is being inferred from an observational comparison.",
            "Check whether uncertainty and credible alternative explanations are represented.",
        ],
        "review_questions": [
            "Has a reviewer inspected every linked source or result?",
            "Would a negative or inconclusive result change this wording?",
            "Should the claim be narrowed, revised, rejected or retained?",
        ],
        "decision": "No decision: human review is required.",
        "human_review_required": True,
    }

