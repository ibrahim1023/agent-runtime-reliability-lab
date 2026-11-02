"""Cross-check stored approval records; never synthesize a runtime or decision."""

import json
from pathlib import Path

from reliability_lab.evidence import checked_bytes, require


CASES = ["approve", "reject", "edit"]


def check_pending(phases: list, name: str) -> dict:
    """Require unchanged pending review and no effects across recorded restart."""
    require([p["phase"] for p in phases] == ["initial", "restore", "decision"], f"{name}: wrong phases")
    pids = [p["pid"] for p in phases]
    require(all(type(pid) is int for pid in pids) and len(set(pids)) == 3,
            f"{name}: three distinct processes required")
    initial, restored, final = phases
    for phase in phases:
        require(phase["decision"] == name, f"{name}: changed decision case")
    for phase in phases[:2]:
        require(phase["ledger"] == [] and phase["answer"] is None, f"{name}: effect or answer before decision")
        require(phase["checkpoint_next"] == ["HumanInTheLoopMiddleware.after_model"], f"{name}: missing pending gate")
    require(initial["interrupts"] == restored["interrupts"] and
            initial["messages"] == restored["messages"], f"{name}: pending review changed on restore")
    require(len(initial["interrupts"]) == 1 and bool(initial["interrupts"][0]["id"]), f"{name}: missing interrupt")
    interrupt = initial["interrupts"][0]["value"]
    require(len(initial["messages"]) == 2, f"{name}: unexpected initial history")
    calls = initial["messages"][1]["tool_calls"]
    require(len(calls) == 1 and calls[0]["name"] == "record_action" and bool(calls[0]["id"]),
            f"{name}: wrong proposed tool")
    proposed = "original-proposal" if name == "edit" else "approval-demo"
    require(calls[0]["args"] == {"message": proposed}, f"{name}: wrong proposed contents")
    requests = interrupt["action_requests"]
    require(len(requests) == 1 and requests[0]["name"] == "record_action" and
            requests[0]["args"] == calls[0]["args"], f"{name}: interrupt and proposal disagree")
    allowed = ["approve", "edit", "reject"] if name == "edit" else ["approve", "reject"]
    require(interrupt["review_configs"] == [{"action_name": "record_action", "allowed_decisions": allowed}],
            f"{name}: review policy differs")
    require(final["interrupts"] == [] and final["checkpoint_next"] == [], f"{name}: final execution remains pending")
    require(len(final["messages"]) == 4 and final["messages"][:2] == initial["messages"],
            f"{name}: original proposal history changed or action reissued")
    return calls[0]


def check_journal(data: dict, name: str) -> list:
    """Require simulated decision to precede every actual tool-body entry."""
    events, phases = data["events"], data["phases"]
    expected = ["worker_start", "worker_start", "worker_start", "reviewer_decision"]
    if name != "reject":
        expected += ["tool_enter", "ledger_result"]
    require([e["event"] for e in events] == expected, f"{name}: tool ran before review or after rejection")
    for event, phase in zip(events[:3], phases):
        require(event["pid"] == phase["pid"] and event["phase"] == phase["phase"], f"{name}: journal phase mismatch")
    require(all(e["pid"] == phases[-1]["pid"] for e in events[3:]), f"{name}: execution process differs")
    review = events[3]
    require(review["source"] == "simulated_reviewer" and review["decision"]["type"] == name,
            f"{name}: wrong reviewer source or decision")
    if name == "edit":
        require(review["decision"]["edited_action"] == {
            "name": "record_action", "args": {"message": "reviewer-approved"}}, f"{name}: wrong replacement")
    return events


def verify_approval_case(data: dict, name: str) -> dict:
    """Check historical proposal, review, actual tool input, and SQL artifact."""
    require(data["schema_version"] == 1 and data["case"] == name and data["historical"] is True,
            f"{name}: wrong evidence identity")
    require(data["decision_source"] == "simulated_reviewer", f"{name}: reviewer must remain simulated")
    require(data["model_id"] == "groq:openai/gpt-oss-120b" and data["immutable_model_revision"] is None,
            f"{name}: changed model provenance")
    proposal = check_pending(data["phases"], name)
    events = check_journal(data, name)
    final = data["phases"][-1]
    tool, answer = final["messages"][2:]
    require(tool["type"] == "tool" and tool["name"] == "record_action" and
            tool["tool_call_id"] == proposal["id"], f"{name}: wrong tool response identity")
    require(answer["type"] == "ai" and answer["tool_calls"] == [] and
            answer["content"] == final["answer"], f"{name}: invalid final answer record")
    rows = data["committed_receipts"]
    require(rows == final["ledger"], f"{name}: SQL export and phase disagree")
    if name == "reject":
        require(rows == [] and tool["status"] == "error", f"{name}: rejection had an effect")
        require("rejected" in tool["content"].lower() and "not executed" in final["answer"].lower(),
                f"{name}: recorded rejection explanation differs")
    else:
        message = "reviewer-approved" if name == "edit" else "approval-demo"
        require(len(rows) == 1 and tool["status"] == "success", f"{name}: expected one effect")
        receipt = rows[0]
        require(receipt["message"] == message and receipt["operation_id"] == data["operation_id"] and
                receipt["status"] == "recorded" and bool(receipt["receipt_id"]), f"{name}: wrong committed action")
        require(events[4]["message"] == message and events[4]["operation_id"] == data["operation_id"],
                f"{name}: actual tool input differs")
        require(events[5]["receipt"] == receipt and events[5]["reused"] is False, f"{name}: journal receipt differs")
        content = tool["content"]
        if name == "edit":
            require("reviewer replaced" in content and "Do not re-issue" in content,
                    f"{name}: missing replacement notice")
            content = content.split("Tool response:\n", 1)[-1]
        require(json.loads(content) == receipt and receipt["receipt_id"] in final["answer"],
                f"{name}: reported receipt differs")
    return {"case": f"approval-{name}", "effects_before_decision": 0,
            "committed_effects": len(rows), "tool_body_entries": 0 if name == "reject" else 1,
            "simulated_reviewer": True, "pending_review_preserved_in_records": True}


def verify_approval_evidence(root: Path) -> list[dict]:
    """Check all three frozen approval cases without runtime or dashboard access."""
    manifest = json.loads((root / "results/manifest.json").read_text())
    cases = manifest["approval_cases"]
    require([case["case"] for case in cases] == CASES, "Incomplete approval cohort")
    results = []
    for case in cases:
        require(case["export"] == f"results/historical/approval/{case['case']}.json", "Wrong approval export path")
        data = json.loads(checked_bytes(root, case["export"], case["sha256"]))
        results.append(verify_approval_case(data, case["case"]))
    return results
