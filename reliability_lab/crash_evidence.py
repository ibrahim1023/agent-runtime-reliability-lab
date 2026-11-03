"""Assess local crash/resume observations without importing the runtime."""

import json


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
            reporting = (json.loads(record["answer"]) == json.loads(record["final_tool_content"]) == entries[-1]
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
