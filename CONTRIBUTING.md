# Contributing to daim-research-agents

Thanks for helping. This repository teaches how a research agent works from
first principles, so a contribution is judged on two things: does it work, and
can a reader follow it?

## Set up

```bash
git clone https://github.com/DAIMCentre/DAIM-Research-Agents.git
cd DAIM-Research-Agents
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
python -m pip install -e ".[test]"
python -m pytest -q
```

All tests run offline. You do not need an API key to contribute, including to
the Claude backend: its tests use a fake client.

To try the live backend as well:

```bash
python -m pip install -e ".[test,llm]"
export ANTHROPIC_API_KEY=...     # Windows PowerShell: $env:ANTHROPIC_API_KEY="..."
python examples/run_agent_from_scratch.py --model claude
```

## Ground rules

These are the design commitments of the project. Pull requests that weaken
them will be asked to change.

1. **The human gate cannot be bypassed.** A model may only propose a
   `ToolCall` or a `DraftAnswer`. Only `review_agent_run` can complete a run.
2. **Everything is in the trace.** Every tool call, observation, error and
   review decision is recorded in `AgentState.events`.
3. **Tools are explicit and narrow.** Each tool is registered by name with
   its required arguments. Prefer read-only tools; a tool with side effects
   needs a clear reason and a test showing how it fails safely.
4. **Tests stay offline and deterministic.** No test may call a network
   service or depend on an API key.
5. **Plain Python first.** Avoid adding agent frameworks; the point is to see
   the loop.

## Good first contributions

- New evidence cases in `evidence/` with a matching test.
- New structural checks in `evaluate_trace` (for example, flagging drafts that
  cite nothing).
- A new read-only tool, such as searching evidence by keyword.
- A new model backend (see [docs/llm-backend.md](docs/llm-backend.md)).

## Making a change

1. Open an issue first for anything larger than a small fix, so the approach
   can be agreed before you write it.
2. Create a branch from `main`.
3. Add or update tests alongside the code.
4. Run `python -m pytest -q`.
5. Open a pull request and fill in the template.

Keep pull requests focused: one idea per PR is much easier to review.

## What not to commit

- API keys, `.env` files or any credentials
- generated traces under `results/agent-example/` or `results/live-*/`
- private or unpublished research data

## Licence

By contributing you agree that your contribution is released under the
[MIT Licence](LICENSE) of this repository.
