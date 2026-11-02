"""Verify stored missing-input observations without inventing new behavior scores."""

import hashlib
import json
from pathlib import Path

from reliability_lab.evidence import checked_bytes, require


QUERY = "Read /data.txt and write the lines reversed (line order) to /out.txt."
CASES = [f"{condition}-{i}" for condition in ("trial", "rate-limited-trial", "setup-failed-trial") for i in range(1, 4)]


def check_recorded_counts(data: dict) -> None:
    """Reconcile callback counts and actual recorded tool results."""
    observed, events = data["observed"], data["events"]
    require(observed["model"] == "groq:openai/gpt-oss-120b", "Missing-source model cohort changed")
    models = [e for e in events if e["event"] == "model_response"]
    starts = [e for e in events if e["event"] == "tool_start"]
    ends = [e for e in events if e["event"] == "tool_end"]
    require(observed["model_steps"] == len(models) and observed["tool_calls"] == len(starts), "Counts disagree with journal")
    require(observed["tool_starts"] == starts and observed["tool_results"] == ends, "Tool observations disagree with journal")
    require(len(starts) == len(ends), "Incomplete tool observations")
    require([e["run_id"] for e in starts] == [e["run_id"] for e in ends], "Tool execution IDs disagree")
    for start, end in zip(starts, ends):
        require(start["name"] == end["output"]["name"], "Tool result belongs to another tool")


def check_valid_behavior(data: dict) -> None:
    """Check objective artifacts and retain the original subjective review label."""
    observed = data["observed"]
    require(data["status"] == "completed" and data["valid_trial"] is True and data["started_model_request"] is True,
            "Wrong valid-trial classification")
    require(data["error"] is None and observed["natural_completion"] is True and observed["forced_stop"] is False,
            "Valid trial was interrupted or forced to stop")
    require(data["task_completion"] is False and observed["files"] == {}, "Missing input cannot yield task success or fabricated files")
    require(data["recorded_feedback"] == {"valid_trial": 1, "task_completion": 0, "failure_handling": 1}, "Feedback dimensions changed")
    messages = observed["messages"]
    require(bool(messages) and messages[0]["type"] == "human" and messages[0]["content"] == QUERY, "Task changed")
    reconstructed = [messages[0]]
    for event in data["events"]:
        if event["event"] == "model_response":
            reconstructed.extend(event["messages"])
        elif event["event"] == "tool_end":
            reconstructed.append(event["output"])
    require(messages == reconstructed, "Conversation disagrees with callback evidence")
    require(messages[-1]["type"] == "ai" and messages[-1]["tool_calls"] == [] and
            messages[-1]["content"] == observed["answer"], "Final response mismatch")
    calls = [call for message in messages if message["type"] == "ai" for call in message["tool_calls"]]
    results = [message for message in messages if message["type"] == "tool"]
    require(len(calls) == observed["tool_calls"] and [c["id"] for c in calls] == [m["tool_call_id"] for m in results],
            "Tool request/result identities disagree")
    require(bool(calls) and calls[0]["name"] == "read_file" and calls[0]["args"]["file_path"] == "/data.txt" and
            results[0]["status"] == "error" and results[0]["content"] == "Error: File '/data.txt' not found",
            "Missing source was not observed")
    require(all(c["name"] in {"ls", "glob", "grep"} for c in calls[1:]), "Unexpected action after missing source")
    require(all(m["content"] in {"No files found", "No matches found"} for m in results[1:]), "Search found unexpected data")
    review = data["assessment"]
    require(review["method"] == "historical_manual_assistant_trace_review" and review["score"] == 1 and
            data["failure_handling"] is True, "Historical review method or score changed")
    digest = hashlib.sha256(observed["answer"].encode()).hexdigest()
    require(review["reviewed_answer_sha256"] == digest, "Answer changed since historical review")


def verify_missing_source_case(data: dict, name: str) -> dict:
    """Keep completed behavior and excluded infrastructure attempts separate."""
    require(data["schema_version"] == 1 and data["case"] == name and data["historical"] is True, "Wrong missing-source identity")
    if name.startswith("trial-"):
        check_recorded_counts(data)
        check_valid_behavior(data)
    else:
        require(data["valid_trial"] is False and data["task_completion"] is None and data["failure_handling"] is None,
                "Invalid attempt cannot receive a task or behavior verdict")
        if name.startswith("rate-limited-"):
            check_recorded_counts(data)
            require(data["status"] == "provider_interrupted" and data["started_model_request"] is True and
                    data["recorded_feedback"] == {"valid_trial": 0} and data["assessment"] is None,
                    "Provider interruption misclassified")
            require(data["error"]["type"] == "RateLimitError" and data["error"]["http_status"] == 429 and
                    data["error"]["category"] == "provider_rate_limit", "Wrong provider error")
            require(data["observed"]["natural_completion"] is False and data["observed"]["answer"] is None and
                    data["observed"]["forced_stop"] is False, "Interrupted attempt claims completed behavior")
        else:
            require(data["status"] == "setup_interrupted" and data["started_model_request"] is False and
                    data["error"]["category"] == "setup_configuration" and data["error"]["type"] == "KeyError" and
                    data["error"]["excerpt"] == "KeyError: 'DEEPAGENTS_EVALS_MODEL'", "Setup failure misclassified")
    return {"case": f"missing-source-{name}", "status": data["status"], "valid_trial": data["valid_trial"],
            "task_completion": data["task_completion"], "failure_handling": data["failure_handling"],
            "behavior_review": "retained historical assistant judgment" if data["valid_trial"] else "inconclusive"}


def verify_missing_source_evidence(root: Path) -> list[dict]:
    """Verify the complete nine-attempt export, including six excluded attempts."""
    manifest = json.loads((root / "results/manifest.json").read_text())
    entries = manifest["missing_source_cases"]
    require([e["case"] for e in entries] == CASES, "Missing or changed missing-source attempt roster")
    results = []
    for entry in entries:
        require(entry["export"] == f"results/historical/missing-source/{entry['case']}.json", "Wrong missing-source export path")
        data = json.loads(checked_bytes(root, entry["export"], entry["sha256"]))
        results.append(verify_missing_source_case(data, entry["case"]))
    counts = manifest["missing_source_denominators"]
    expected = {"recorded_attempts": 9, "completed_valid": 3, "invalid_provider": 3, "invalid_setup": 3, "behavior_denominator": 3}
    require(all(counts[k] == value for k, value in expected.items()) and counts["historical_plan_count"] is None,
            "Retrospective denominators or unknown plan count changed")
    return results
