"""Assess local crash/resume observations without importing the runtime."""

import json


def receipt_from_message(record: dict) -> dict:
    """Accept a bare receipt or the exact observed edit notice, with matching args."""
    content = record["final_tool_content"]
    if record["decision"] == "edit":
        arguments = json.dumps({"message": record["approved_message"]})
        prefix = ("Note: a human reviewer replaced this tool call before it ran. "
                  "The call recorded in your message is the one you produced, not the one that executed. "
                  "This was intentional and authorized. Do not re-issue your original call. "
                  f"Executed instead: record_action with arguments {arguments}.\n\nTool response:\n")
        if content.startswith(prefix):
            content = content[len(prefix):]
    return json.loads(content)


def assess_case(record: dict) -> dict:
    """Keep expected fixture behavior, task completion and reporting separate."""
    rejected = record["decision"] == "reject"
    entries, attempts = record["entries"], record["tool_entries"]
    results, phases = record["receiver_results"], record["phases"]
    expected_effects = 0 if rejected else (1 if record["protected"] else 2)
    identity = all(item["operation_id"] == record["operation_id"] and
                   item["message"] == record["approved_message"] for item in entries + attempts)
    review = (record["same_pending_review"] and len(phases) == (3 if rejected else 4) and
              all(phase.get("pending_review") and phase["effects"] == phase["tool_entries"] == 0
                  for phase in phases[:2]) and not phases[-1].get("pending_review", False))
    processes = len({phase["pid"] for phase in phases}) == len(phases)
    exits = [phase["exit_code"] for phase in phases] == ([0, 0, 0] if rejected else [0, 0, 86, 0])
    if rejected:
        receipts = not results
        reporting = (record["final_tool_status"] == "error" and
                     record["answer"] == record["final_tool_content"])
    else:
        receipts = (len(results) == 2 and results[0]["reused"] is False and
                    results[1]["reused"] is record["protected"] and
                    [item["receipt"] for item in results] ==
                    ([entries[0], entries[0]] if len(entries) == 1 else entries))
        try:
            reporting = (record["answer"] == record["final_tool_content"] and receipt_from_message(record) == entries[-1]
                         and record["final_tool_status"] == "success")
        except (ValueError, TypeError, IndexError):
            reporting = False
    effects = len(entries) == expected_effects
    attempts_match = len(attempts) == (0 if rejected else 2)
    phase_counts = (phases[-1]["effects"] == len(entries) and
                    phases[-1]["tool_entries"] == len(attempts))
    if not rejected and len(phases) > 2:
        phase_counts = phase_counts and phases[2]["effects"] == phases[2]["tool_entries"] == 1
    contract = all((identity, review, processes, exits, receipts, effects, attempts_match,
                    phase_counts, reporting, record["graph_completed"]))
    return {"contract_met": contract, "graph_completed": record["graph_completed"],
            "review_policy_handled": review and identity,
            "approved_task_completed": not rejected and len(entries) == 1 and identity and record["graph_completed"],
            "report_matches_observed_tool_result": reporting,
            "report_accounts_for_all_effects": reporting and len(entries) <= 1,
            "tool_body_entries": len(attempts), "committed_effects": len(entries),
            "checks": {"stable_approved_identity": identity, "review_boundary": review,
                       "fresh_processes": processes, "expected_exits": exits,
                       "receipt_replay": receipts, "effect_count": effects,
                       "attempt_count": attempts_match, "phase_counts": phase_counts}}


def verify_crash_export(root) -> dict:
    """Validate saved phase evidence; do not start workers or model calls."""
    from reliability_lab.evidence import checked_bytes, require
    manifest = json.loads((root / "results/manifest.json").read_text())
    references = manifest["crash_resume_v1"]
    loaded = {name: json.loads(checked_bytes(root, references[name]["export"], references[name]["sha256"]))
              for name in ("execution", "reassessment")}
    checked_bytes(root, references["amendment"]["export"], references["amendment"]["sha256"])
    plan_ref = manifest["next_experiment_plan"]
    plan = json.loads(checked_bytes(root, plan_ref["export"], plan_ref["sha256"]))
    execution, reassessment = loaded["execution"], loaded["reassessment"]
    require(execution["criteria_sha256"] == plan_ref["sha256"], "Changed frozen criteria")
    require(execution["status"] == "failed" and execution["live_model_calls"] == 0, "Original attempt relabelled")
    require(len(execution["cases"]) == 5 and execution["worker_processes"] == 19 and
            execution["duration_s"] <= 600, "Execution bound mismatch")
    require(reassessment["execution_sha256"] == references["execution"]["sha256"], "Reassessment input changed")
    computed = []
    for case, expected in zip(execution["cases"], plan["cases"], strict=True):
        require(all(case[key] == expected[key] for key in ("case", "decision", "protected")), "Case roster changed")
        require(case["approved_message"] == expected.get("approved_message", "record-once"), "Approved payload changed")
        phases, events = case["phases"], case["events"]
        require(len(phases) == expected["phases"] and all(not p["timeout"] and p["duration_s"] <= 30 for p in phases),
                "Worker sequence or bound changed")
        starts = [event for event in events if event["event"] == "worker_start"]
        require([(p["phase"], p["pid"]) for p in phases] == [(e["phase"], e["pid"]) for e in starts], "Worker journal mismatch")
        for key, event_name in (("tool_entries", "tool_enter"), ("receiver_results", "receiver_result")):
            require(case[key] == [event for event in events if event["event"] == event_name], "Tool journal mismatch")
        initial, restored = (phase["observation"].get("interrupts") for phase in phases[:2])
        require(bool(initial) and initial == restored and case["same_pending_review"] is True, "Pending review changed")
        request = initial[0]["value"]["action_requests"]
        require(request == [{"name": "record_action", "args": {"message": case["original_message"]},
                             "description": request[0]["description"]}], "Initial review does not match proposal")
        final = phases[-1]["observation"]
        require(case["graph_completed"] == (final.get("checkpoint_next") == [] and not final.get("interrupts")), "Completion mismatch")
        require(all(case[key] == final[key] for key in ("answer", "final_tool_status", "final_tool_content")), "Final observation mismatch")
        observed = [event for event in events if event["event"] == "model_observed_tool"]
        require(len(observed) == 1 and observed[0]["content"] == case["final_tool_content"], "Model observation mismatch")
        verdict = assess_case(case)
        require(verdict["contract_met"], "Saved crash contract failed")
        require(case["verdicts"]["approved_task_completed"] == expected["approved_task_completed"], "Original task verdict relabelled")
        require(verdict["tool_body_entries"] == expected["expected_tool_entries"] and
                verdict["committed_effects"] == expected["expected_committed_effects"], "Frozen count mismatch")
        computed.append({"case": case["case"], "verdicts": verdict})
    require(computed == reassessment["cases"], "Saved reassessment contradicts observations")
    return {"status": "passed", "kind": "stored fresh-runtime evidence validation; no workers or models executed",
            "cases_checked": 5, "original_execution_status": execution["status"],
            "worker_processes_observed": 19, "approved_tasks_completed": 3,
            "assessment_amendment": "A1; original failed assessment preserved"}
