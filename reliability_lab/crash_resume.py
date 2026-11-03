"""Bounded fresh-process approval/commit/crash/resume experiment."""

from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid

from reliability_lab.crash_evidence import assess_case
from reliability_lab.evidence import checked_bytes, require
from reliability_lab.offline import install_offline_guard
from reliability_lab.receiver import Ledger
from reliability_lab.scripted_root import check_extractions, runtime_identity


def clean_environment() -> dict[str, str]:
    """Allow only process essentials; do not inherit keys or tracing configuration."""
    allowed = ("PATH", "HOME", "TMPDIR", "SYSTEMROOT", "LANG", "LC_ALL")
    return {**{name: os.environ[name] for name in allowed if name in os.environ},
            "LANGSMITH_TRACING": "false", "LANGCHAIN_TRACING_V2": "false",
            "PYTHONNOUSERSITE": "1"}


def read_events(directory: Path) -> list[dict]:
    """Read the durable journal; a partial final line is an observed failure."""
    path = directory / "events.jsonl"
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []


def launch(directory: Path, phase: str, remaining: float) -> dict:
    """Launch once, preserving failures and timeouts without automatic retry."""
    started = time.perf_counter()
    with (directory / f"{phase}.log").open("w") as log:
        process = subprocess.Popen([sys.executable, "-m", "reliability_lab.crash_worker", str(directory), phase],
                                   env=clean_environment(), stdout=log, stderr=subprocess.STDOUT)
        timeout = False
        try:
            code = process.wait(timeout=min(30, remaining))
        except subprocess.TimeoutExpired:
            process.kill()
            code = process.wait()
            timeout = True
    observation_path = directory / f"{phase}.json"
    observation = json.loads(observation_path.read_text()) if observation_path.exists() else {}
    return {"phase": phase, "pid": process.pid, "exit_code": code, "timeout": timeout,
            "duration_s": time.perf_counter() - started, "observation": observation}


def run_case(directory: Path, case: dict, deadline: float) -> dict:
    """Persist identity once and collect each declared phase's SQL/journal state."""
    directory.mkdir()
    identity = {"case": case["case"], "decision": case["decision"], "protected": case["protected"],
                "thread_id": str(uuid.uuid4()), "operation_id": str(uuid.uuid4()),
                "original_message": case.get("original_message", "record-once"),
                "approved_message": case.get("approved_message", "record-once")}
    with (directory / "identity.json").open("x") as stream:
        stream.write(json.dumps(identity, indent=2) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    ledger = Ledger(directory / "receiver.sqlite", protected=case["protected"])
    phases = []
    for name in ("initial", "restore", "decision", "resume")[:case["phases"]]:
        if time.perf_counter() >= deadline:
            break
        phase = launch(directory, name, deadline - time.perf_counter())
        events = read_events(directory)
        phase.update(effects=len(ledger.entries()),
                     tool_entries=sum(event["event"] == "tool_enter" for event in events),
                     pending_review=bool(phase["observation"].get("interrupts")))
        phases.append(phase)
        expected_exit = 86 if name == "decision" and case["decision"] != "reject" else 0
        if phase["timeout"] or phase["exit_code"] != expected_exit:
            break
    events = read_events(directory)
    final = phases[-1]["observation"] if phases else {}
    record = {**identity, "phases": phases, "entries": ledger.entries(),
              "tool_entries": [event for event in events if event["event"] == "tool_enter"],
              "receiver_results": [event for event in events if event["event"] == "receiver_result"],
              "events": events,
              "same_pending_review": len(phases) > 1 and bool(phases[0]["observation"].get("interrupts")) and
                  phases[0]["observation"].get("interrupts") == phases[1]["observation"].get("interrupts"),
              "graph_completed": bool(final) and final.get("checkpoint_next") == [] and not final.get("interrupts"),
              "final_tool_status": final.get("final_tool_status"), "final_tool_content": final.get("final_tool_content"),
              "answer": final.get("answer")}
    record["verdicts"] = assess_case(record) if len(phases) == case["phases"] else {
        "contract_met": False, "classification": "incomplete worker sequence; inspect retained logs; outcome may be unknown"}
    (directory / "record.json").write_text(json.dumps(record, indent=2) + "\n")
    return record


def run_crash_resume(root: Path) -> tuple[dict, int]:
    """Execute the frozen five-case plan once; never substitute live inference."""
    install_offline_guard()
    attempt = Path("work/crash-resume") / uuid.uuid4().hex
    directory = root / attempt
    directory.mkdir(parents=True)
    report = {"schema_version": 1, "experiment_id": "approval-commit-crash-resume-v1",
              "kind": "fresh deterministic scripted graph/process execution; not live-model evaluation",
              "started_at_utc": datetime.now(timezone.utc).isoformat(), "live_model_calls": 0,
              "estimated_provider_tokens": 0, "decision_source": "simulated_reviewer",
              "learner_prediction": "Checkpoint prevents the tool from repeating",
              "report_path": str(attempt / "report.json"), "cases": []}
    started = time.perf_counter()
    try:
        manifest = json.loads((root / "results/manifest.json").read_text())
        plan_ref = manifest["next_experiment_plan"]
        plan = json.loads(checked_bytes(root, plan_ref["export"], plan_ref["sha256"]))
        report["criteria_sha256"] = plan_ref["sha256"]
        require(plan["experiment_id"] == report["experiment_id"], "Unexpected plan identity")
        check_extractions(root)
        checked_bytes(root, "reliability_lab/receiver.py", plan["reuse_sources"]["receiver_sha256"])
        from langgraph.checkpoint.sqlite import SqliteSaver
        require(callable(SqliteSaver.from_conn_string), "SQLite checkpoint saver unavailable")
        report["runtime"] = runtime_identity()
        report["runtime"]["packages"].update({name: importlib.metadata.version(name) for name in
                                               ("langgraph-checkpoint", "langgraph-checkpoint-sqlite")})
        report["implementation_sha256"] = {name: hashlib.sha256((root / "reliability_lab" / name).read_bytes()).hexdigest()
                                              for name in ("crash_worker.py", "crash_resume.py", "crash_evidence.py", "receiver.py")}
        report["preflight"] = "passed; existing editable environment, not a clean-install proof"
        deadline = started + plan["budget"]["max_total_seconds"]
        for case in plan["cases"]:
            report["cases"].append(run_case(directory / case["case"], case, deadline))
        report["worker_processes"] = sum(len(case["phases"]) for case in report["cases"])
        report["status"] = "passed" if all(case["verdicts"]["contract_met"] for case in report["cases"]) else "failed"
    except (ImportError, OSError, ValueError, KeyError, TypeError) as exc:
        report["status"] = "interrupted"
        report["classification"] = "setup interruption" if not report["cases"] else "fixture interruption; inspect retained artifacts"
        report["error_type"] = type(exc).__name__
        # Detailed exceptions may contain private paths; retain locally only.
        (directory / "error.txt").write_text(str(exc))
    report["duration_s"] = time.perf_counter() - started
    report["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
    (directory / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    return report, 0 if report["status"] == "passed" else 1
