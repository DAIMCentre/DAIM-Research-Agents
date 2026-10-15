from daim_research_agents import ToolCall, ToolRegistry, build_evidence_registry


def test_only_registered_tools_execute() -> None:
    registry = ToolRegistry()
    result = registry.execute(ToolCall("missing"))
    assert result.success is False
    assert result.error == "unknown tool: missing"


def test_required_and_unexpected_arguments_are_checked() -> None:
    registry = build_evidence_registry([{"evidence_id": "E-1", "title": "One"}])
    missing = registry.execute(ToolCall("read_evidence"))
    extra = registry.execute(ToolCall("list_evidence", {"unused": True}))
    assert missing.success is False and "evidence_id" in missing.error
    assert extra.success is False and "unexpected" in extra.error


def test_local_evidence_tools_list_and_read_records() -> None:
    registry = build_evidence_registry([{"evidence_id": "E-1", "title": "One", "summary": "Supplied"}])
    listed = registry.execute(ToolCall("list_evidence"))
    read = registry.execute(ToolCall("read_evidence", {"evidence_id": "E-1"}))
    assert listed.data["evidence"] == [{"evidence_id": "E-1", "title": "One"}]
    assert read.data["summary"] == "Supplied"
