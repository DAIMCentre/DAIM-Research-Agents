from pathlib import Path

import pytest

from daim_research_agents import EvidenceError, load_agent_case, load_yaml, save_yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_supplied_evidence_examples_are_readable() -> None:
    experiment = load_yaml(PROJECT_ROOT / "evidence" / "example-experiment.yaml")
    claim = load_yaml(PROJECT_ROOT / "evidence" / "example-claim.yaml")

    assert experiment["experiment_id"] == "FM-EXAMPLE-001"
    assert {
        "experiment_id",
        "research_question",
        "hypothesis",
        "date",
        "researcher",
        "data",
        "code_reference",
        "configuration",
        "result_files",
        "interpretation",
        "limitations",
        "review_status",
    }.issubset(experiment)
    assert claim["claim_id"] == "CLAIM-EXAMPLE-001"
    assert {
        "claim_id",
        "claim",
        "supporting_evidence",
        "confidence",
        "limitations",
        "human_reviewed",
        "reviewer",
    }.issubset(claim)
    assert claim["human_reviewed"] is False


def test_agent_demo_case_is_valid() -> None:
    case = load_agent_case(PROJECT_ROOT / "evidence" / "agent-demo.yaml")
    assert case["question"]
    assert [item["evidence_id"] for item in case["evidence"]] == ["E-DEMO-001", "E-DEMO-002"]


def test_malformed_yaml_is_reported_clearly(tmp_path: Path) -> None:
    invalid = tmp_path / "invalid.yaml"
    invalid.write_text("claim: [not closed\n", encoding="utf-8")
    with pytest.raises(EvidenceError, match="malformed YAML"):
        load_yaml(invalid)


def test_non_mapping_yaml_is_rejected(tmp_path: Path) -> None:
    invalid = tmp_path / "list.yaml"
    invalid.write_text("- one\n- two\n", encoding="utf-8")
    with pytest.raises(EvidenceError, match="top level"):
        load_yaml(invalid)


def test_save_and_reload_round_trip(tmp_path: Path) -> None:
    path = save_yaml({"claim": "Example", "human_reviewed": False}, tmp_path / "record.yaml")
    assert load_yaml(path) == {"claim": "Example", "human_reviewed": False}
