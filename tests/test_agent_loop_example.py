from __future__ import annotations

import importlib.util
from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_example_module():
    path = PROJECT_ROOT / "examples" / "run_agent_from_scratch.py"
    spec = importlib.util.spec_from_file_location("run_agent_from_scratch", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_example_writes_complete_offline_trace(tmp_path: Path) -> None:
    output = tmp_path / "trace.yaml"
    module = load_example_module()
    result = module.run_example(
        input_path=PROJECT_ROOT / "evidence" / "agent-demo.yaml",
        output_path=output,
    )
    saved = yaml.safe_load(output.read_text(encoding="utf-8"))
    assert saved["registered_tools"] == ["list_evidence", "read_evidence"]
    assert saved["status"] == "waiting_for_human_review"
    assert saved["human_review_required"] is True
    assert saved["evaluation"]["all_citations_were_observed"] is True
    assert result["draft"]["cited_evidence_ids"] == ("E-DEMO-001", "E-DEMO-002")


def test_example_records_explicit_human_approval(tmp_path: Path) -> None:
    module = load_example_module()
    result = module.run_example(
        input_path=PROJECT_ROOT / "evidence" / "agent-demo.yaml",
        output_path=tmp_path / "approved.yaml",
        review_decision="approve",
        review_note="Records inspected for the demonstration.",
    )
    assert result["status"] == "completed"
    assert result["review"]["decision"] == "approve"
    assert result["evaluation"]["completed_without_approval"] is False
