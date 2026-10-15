# Adding an LLM to the agent loop

The loop in `src/daim_research_agents/loop.py` never needs to know which model
is deciding. A model is anything with a `name` and one method:

```python
class AgentModel(Protocol):
    name: str

    def next_action(self, state: AgentState) -> ToolCall | DraftAnswer: ...
```

`ScriptedModel` implements this with fixed rules. `ClaudeModel` implements the
same method by asking Claude. Everything else stays the same: the tool registry,
the step limit, the trace, `evaluate_trace` and the human review gate.

## Running the Claude backend

```bash
python -m pip install -e ".[llm]"
export ANTHROPIC_API_KEY=...
python examples/run_agent_from_scratch.py --model claude
```

The trace is written to `results/live-claude/agent-trace.yaml`, which Git
ignores. Choose another model with `--claude-model` or the `DAIM_AGENT_MODEL`
environment variable. The default is `claude-opus-5-5`; `claude-sonnet-5-5`
and `claude-haiku-5-5` are cheaper options.

From Python:

```python
from daim_research_agents import ClaudeModel, build_evidence_registry, run_agent

state = run_agent(question, ClaudeModel(), build_evidence_registry(evidence))
```

## How one step works

```text
AgentState (question + every event so far)
  -> render_state(): one user message containing the question and the trace
  -> Messages API request with three strict tools:
       list_evidence, read_evidence, submit_draft
  -> Claude calls exactly one tool
  -> parse_response():
       list_evidence / read_evidence  -> ToolCall    (executed by the registry)
       submit_draft                   -> DraftAnswer (stops at the human gate)
```

Design choices worth knowing:

- **The request is rebuilt from the trace every step.** Claude has no hidden
  memory between steps. If it is not in `state.events`, the model did not see
  it, which keeps the YAML trace a complete record.
- **Finishing is a tool call.** `submit_draft` has a strict schema, so a draft
  always arrives with its citations and review questions as structured data.
- **The registry, not the model, decides what runs.** If Claude names a tool
  that is not registered, the registry records an error and the loop stops.
- **Failures are explicit.** A refusal, a reply with no tool call or invalid
  draft arguments raise `ModelResponseError` rather than being guessed at.
- **Evidence is data.** The system prompt tells Claude to ignore instructions
  that appear inside evidence records.
- **Refusal fallback.** On models that support it, the request opts into the
  API's server-side fallback (`fallbacks: "default"`), so a safety-classifier
  refusal is retried on a fallback model inside the same call.

## Testing without an API key

`tests/test_claude_model.py` passes a fake client that replays scripted
responses and records each request. Use the same pattern for any new backend:
test the request you build and the action you parse, never the live API.

## Next steps for contributors

Each of these is a self-contained pull request:

1. **More tools.** Add a read-only tool to `build_evidence_registry`, add its
   schema to `TOOLS` in `claude_model.py`, and add a test. Keyword search over
   evidence is a good first one.
2. **Usage and cost in the trace.** Record `response.usage` per step so runs
   can be compared on tokens as well as outcomes.
3. **A revision loop.** When a reviewer chooses `revision`, start a new run
   whose input includes the reviewer's note.
4. **Another provider.** Write a new class with the same `next_action`
   method in its own module, with its SDK as a separate optional dependency.
5. **Evaluation across backends.** Run `ScriptedModel` and `ClaudeModel` on
   the same evidence cases and compare `evaluate_trace` results.
