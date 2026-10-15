"""Run and record the deterministic research-agent loop."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from daim_research_agents import (
    ClaudeModel,
    ScriptedModel,
    build_evidence_registry,
    evaluate_trace,
    load_agent_case,
    review_agent_run,
    run_agent,
    save_yaml,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
NOTES = {
    "scripted": (
        "This deterministic trace organises supplied evidence. It does not browse, "
        "call an LLM, invent evidence or make a scientific decision."
    ),
    "claude": (
        "Claude chose each action from the supplied evidence tools only. The draft "
        "is unreviewed model output and makes no scientific decision."
    ),
}


def run_example(
    *,
    input_path: Path,
    output_path: Path,
    max_steps: int = 10,
    review_decision: str | None = None,
    review_note: str | None = None,
    backend: str = "scripted",
    claude_model: str | None = None,
) -> dict[str, Any]:
    case = load_agent_case(input_path)
    registry = build_evidence_registry(case["evidence"])
    model = ClaudeModel(model=claude_model) if backend == "claude" else ScriptedModel()
    state = run_agent(case["question"], model, registry, max_steps=max_steps)
    if review_decision is not None:
        review_agent_run(state, review_decision, note=review_note)

    now = datetime.now(timezone.utc)
    record = {
        "run_id": f"agent-demo-{now.strftime('%Y%m%dT%H%M%S%fZ')}",
        "created_at": now.isoformat(),
        "model": model.name,
        "registered_tools": list(registry.names),
        **state.to_record(),
        "evaluation": evaluate_trace(state),
        "note": NOTES[backend],
    }
    save_yaml(record, output_path)
    return record


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=PROJECT_ROOT / "evidence" / "agent-demo.yaml",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Defaults to results/agent-example/ (scripted) or results/live-claude/ (claude).",
    )
    parser.add_argument(
        "--model",
        choices=("scripted", "claude"),
        default="scripted",
        help="scripted is offline and deterministic; claude calls the Anthropic API.",
    )
    parser.add_argument(
        "--claude-model",
        help="Claude model ID (default: $DAIM_AGENT_MODEL or claude-opus-5-5).",
    )
    parser.add_argument("--max-steps", type=int, default=10)
    parser.add_argument("--review", choices=("approve", "reject", "revision"))
    parser.add_argument("--review-note")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.output is None:
        folder = "live-claude" if args.model == "claude" else "agent-example"
        args.output = PROJECT_ROOT / "results" / folder / "agent-trace.yaml"
    record = run_example(
        input_path=args.input,
        output_path=args.output,
        max_steps=args.max_steps,
        review_decision=args.review,
        review_note=args.review_note,
        backend=args.model,
        claude_model=args.claude_model,
    )
    print(f"Status: {record['status']}")
    print(f"Recorded {record['run_id']} in {args.output.resolve()}")


if __name__ == "__main__":
    main()
