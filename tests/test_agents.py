import pytest

from daim_research_agents import critique_claim, organise_literature, plan_experiment


def test_literature_agent_preserves_sources_and_requires_review() -> None:
    result = organise_literature(
        {
            "research_question": "Which evidence is relevant?",
            "sources": [
                {
                    "source_id": "S-1",
                    "title": "Checked source",
                    "topic": "Methods",
                    "url": "https://example.org/source",
                }
            ],
        }
    )
    assert result["organised_sources"]["Methods"][0]["source_id"] == "S-1"
    assert result["human_review_required"] is True
    assert result["status"] == "draft_for_review"


def test_literature_agent_flags_missing_provenance() -> None:
    result = organise_literature(
        {
            "research_question": "Which evidence is relevant?",
            "sources": [{"source_id": "S-1", "title": "Unverified source"}],
        }
    )
    assert "citation or retrievable URL" in result["evidence_gaps"][0]


def test_experiment_agent_returns_reviewable_checklist() -> None:
    result = plan_experiment(
        {
            "research_question": "Does the method transfer?",
            "hypothesis": "Transfer is better for similar seasonal structure.",
            "data": {"name": "Example"},
            "configuration": {"horizon": 12},
        }
    )
    assert set(result["checklist"]) == {
        "question_and_hypothesis",
        "data_and_design",
        "recording",
        "review",
    }
    assert result["human_review_required"] is True
    assert "experiment_id" in result["unresolved_fields"]


def test_critic_agent_preserves_claim_and_never_decides() -> None:
    result = critique_claim(
        {
            "claim": "A model transfers across domains.",
            "supporting_evidence": ["EXP-1"],
            "limitations": ["Only two domains were tested."],
            "confidence": "low",
        }
    )
    assert result["claim"] == "A model transfers across domains."
    assert result["supporting_evidence"] == ["EXP-1"]
    assert result["decision"] == "No decision: human review is required."
    assert result["human_review_required"] is True


@pytest.mark.parametrize(
    ("function", "record", "message"),
    [
        (organise_literature, {"sources": []}, "research_question"),
        (
            plan_experiment,
            {"research_question": "Question", "hypothesis": "Hypothesis", "data": {}},
            "configuration",
        ),
        (critique_claim, {"claim": "Claim"}, "supporting_evidence"),
    ],
)
def test_agents_reject_missing_required_fields(function, record, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        function(record)

