# daim-research-agents

[![tests](https://github.com/DAIMCentre/DAIM-Research-Agents/actions/workflows/tests.yml/badge.svg)](https://github.com/DAIMCentre/DAIM-Research-Agents/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Small, deterministic components for understanding a research agent from first
principles. The package separates model decisions, typed tool calls,
observations, state transitions, structural evaluation and human review.

By default it runs offline with a deterministic `ScriptedModel`. An optional
`ClaudeModel` lets Claude choose the actions instead, through the same tools and
the same human review gate. Neither backend browses the web, executes arbitrary
code or makes an autonomous scientific decision.

## Requirements and installation

- Python 3.10 or later
- no API key, GPU or network service for the default offline path

```bash
python3.11 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
python -m pip install -e ".[test]"
```

## Agent loop from scratch

Run the offline example:

```bash
python examples/run_agent_from_scratch.py
```

It reads `evidence/agent-demo.yaml` and writes
`results/agent-example/agent-trace.yaml`. The deterministic `ScriptedModel`
performs this policy:

```text
question + supplied evidence
  -> list_evidence tool call
  -> observation
  -> read_evidence tool calls
  -> observations
  -> cited draft
  -> waiting_for_human_review
```

The draft cannot complete its own run. A reviewer can make a separate,
explicit transition:

```bash
python examples/run_agent_from_scratch.py \
  --review approve \
  --review-note "Evidence records inspected."
```

The accepted review choices are `approve`, `reject` and `revision`. Every tool
call, observation, error and review event remains in the YAML trace.

The initial registry contains only two local read-only tools:

- `list_evidence`: list supplied evidence IDs and titles;
- `read_evidence`: return one supplied record by ID.

Unknown tools, missing arguments and tool failures are recorded and stop
safely. A maximum step count prevents an unproductive loop from running
indefinitely.

## Using an LLM to choose the actions

```bash
python -m pip install -e ".[llm]"
export ANTHROPIC_API_KEY=...     # Windows PowerShell: $env:ANTHROPIC_API_KEY="..."
python examples/run_agent_from_scratch.py --model claude
```

`ClaudeModel` (default model `claude-opus-5-5`; override with `--claude-model`
or `DAIM_AGENT_MODEL`) receives the question and the full trace each step and
calls one of three strict tools: `list_evidence`, `read_evidence` or
`submit_draft`. Its draft still stops at `waiting_for_human_review`. The trace
is written to `results/live-claude/`, which Git ignores.

See [docs/llm-backend.md](docs/llm-backend.md) for how it works and how to add
tools or other backends.

## Direct bounded workflows

The earlier three YAML-in/YAML-out functions remain available:

```bash
python examples/run_agent_example.py

daim-research-agent experiment \
  --input evidence/example-experiment.yaml \
  --output results/example/experiment-plan.yaml
```

The CLI accepts `literature`, `experiment` or `critic`. These functions organise
only the supplied records and always return:

```yaml
status: draft_for_review
human_review_required: true
```

## Supported Python interface

```python
from daim_research_agents import (
    ClaudeModel,
    DraftAnswer,
    ScriptedModel,
    ToolCall,
    build_evidence_registry,
    evaluate_trace,
    review_agent_run,
    run_agent,
)
```

The original `organise_literature`, `plan_experiment`, `critique_claim`,
`load_yaml` and `save_yaml` callables remain supported.

`evaluate_trace` checks structure rather than scientific truth: citation IDs,
observed evidence, tool errors, the human gate, stop reason and any unread
records.

## Tests

```bash
python -m pytest -q
```

The tests are deterministic and offline, including those for `ClaudeModel`,
which use a fake client. They verify tool permissions,
arguments, step limits, trace order, citation integrity and the review gate.

## Repository layout

```text
agents/     functional contracts for the three bounded workflows
docs/       design notes, including the LLM backend
evidence/   local example records and the agent-loop input
examples/   direct workflows and the from-scratch loop
src/        models (scripted and Claude), tools, loop, state and evaluation
tests/      offline unit and end-to-end tests
results/    generated trace records
```

Generated drafts and traces are workflow demonstrations, not reviewed research
claims.

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for setup,
ground rules and good first issues, and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
for how we work together.

## Licence

Code is released under the [MIT Licence](LICENSE).
