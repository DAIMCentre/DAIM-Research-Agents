from pathlib import Path
import subprocess
import sys

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_cli_writes_structured_output_for_human_review(tmp_path: Path) -> None:
    output = tmp_path / "critic.yaml"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "daim_research_agents.cli",
            "critic",
            "--input",
            str(PROJECT_ROOT / "evidence" / "example-claim.yaml"),
            "--output",
            str(output),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    result = yaml.safe_load(output.read_text(encoding="utf-8"))
    assert "draft critic output" in completed.stdout
    assert result["agent"] == "critic"
    assert result["human_review_required"] is True


def test_cli_reports_invalid_input(tmp_path: Path) -> None:
    invalid = tmp_path / "invalid.yaml"
    invalid.write_text("claim: Missing evidence list\n", encoding="utf-8")
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "daim_research_agents.cli",
            "critic",
            "--input",
            str(invalid),
            "--output",
            str(tmp_path / "unused.yaml"),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode != 0
    assert "supporting_evidence" in completed.stderr


def test_example_script_writes_all_three_outputs(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "examples" / "run_agent_example.py"),
            "--output-dir",
            str(tmp_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "Wrote 3 draft outputs" in completed.stdout
    assert {path.name for path in tmp_path.iterdir()} == {
        "critic-output.yaml",
        "experiment-output.yaml",
        "literature-output.yaml",
    }
    for path in tmp_path.iterdir():
        assert yaml.safe_load(path.read_text(encoding="utf-8"))["human_review_required"] is True

