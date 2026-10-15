"""Run all three transparent workflow prototypes on tiny local records."""

from __future__ import annotations

import argparse
from pathlib import Path

from daim_research_agents import (
    critique_claim,
    load_yaml,
    organise_literature,
    plan_experiment,
    save_yaml,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run_examples(output_dir: Path) -> list[Path]:
    literature_input = {
        "research_question": "What evidence would demonstrate cross-domain time-series transfer?",
        "sources": [
            {
                "source_id": "DAIM-FM-CHARTER",
                "title": "DAIM Foundation Models Project Charter",
                "topic": "Research scope",
                "citation": "DAIM Foundation Models, PROJECT_CHARTER.md (local programme document)",
                "notes": "Defines the first-stage question and scope used by this example.",
            }
        ],
    }
    experiment_input = load_yaml(PROJECT_ROOT / "evidence" / "example-experiment.yaml")
    claim_input = load_yaml(PROJECT_ROOT / "evidence" / "example-claim.yaml")

    outputs = {
        "literature-output.yaml": organise_literature(literature_input),
        "experiment-output.yaml": plan_experiment(experiment_input),
        "critic-output.yaml": critique_claim(claim_input),
    }
    paths = [save_yaml(record, output_dir / name) for name, record in outputs.items()]
    return paths


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "results" / "example",
        help="Directory for the three review records.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    paths = run_examples(args.output_dir)
    print(f"Wrote {len(paths)} draft outputs for human review to {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
