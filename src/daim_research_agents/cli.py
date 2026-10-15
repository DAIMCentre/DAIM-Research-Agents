"""YAML-in/YAML-out interface for the bounded research workflows."""

from __future__ import annotations

import argparse
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from .agents import critique_claim, organise_literature, plan_experiment
from .evidence import EvidenceError, load_yaml, save_yaml


AgentFunction = Callable[[Mapping[str, Any]], dict[str, Any]]
AGENTS: dict[str, AgentFunction] = {
    "literature": organise_literature,
    "experiment": plan_experiment,
    "critic": critique_claim,
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("agent", choices=sorted(AGENTS), help="Bounded workflow to run.")
    parser.add_argument("--input", type=Path, required=True, help="Input YAML mapping.")
    parser.add_argument("--output", type=Path, required=True, help="Output YAML record.")
    return parser


def run(agent_name: str, input_path: Path, output_path: Path) -> Path:
    """Run one named workflow and save its structured output."""
    if agent_name not in AGENTS:
        raise EvidenceError(f"unknown agent: {agent_name}")
    record = load_yaml(input_path)
    try:
        result = AGENTS[agent_name](record)
    except ValueError as exc:
        raise EvidenceError(f"invalid input for {agent_name} agent: {exc}") from exc
    return save_yaml(result, output_path)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        output_path = run(args.agent, args.input, args.output)
    except EvidenceError as exc:
        parser.exit(status=2, message=f"error: {exc}\n")
    print(f"Wrote draft {args.agent} output for human review to {output_path.resolve()}")


if __name__ == "__main__":
    main()

