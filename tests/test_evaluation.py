from daim_research_agents import DraftAnswer, ToolRegistry, evaluate_trace, run_agent


def test_evaluation_flags_a_citation_that_was_not_observed() -> None:
    class UnsupportedDraftModel:
        name = "unsupported"

        def next_action(self, state):
            return DraftAnswer("Draft requiring review.", ("UNKNOWN",))

    state = run_agent("Question", UnsupportedDraftModel(), ToolRegistry())
    result = evaluate_trace(state)
    assert result["all_citations_were_observed"] is False
    assert result["all_citations_exist"] is False
    assert result["human_gate_reached"] is True
    assert result["completed_without_approval"] is False
