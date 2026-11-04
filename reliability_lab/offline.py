"""Standard-library-only offline verification entry point."""

from datetime import datetime, timezone
import io
import json
import os
from pathlib import Path
import sys
import unittest
import uuid

from reliability_lab.evidence import verify_evidence
from reliability_lab.approval_evidence import verify_approval_evidence
from reliability_lab.missing_source_evidence import verify_missing_source_evidence
from reliability_lab.search_review import verify_search_review
from reliability_lab.search_evidence import verify_search_evidence
from reliability_lab.optional_inventory import verify_optional_inventory
from reliability_lab.crash_evidence import verify_crash_export
from reliability_lab.retry_evidence import verify_native_retry
from reliability_lab.run_budget_evidence import verify_run_budget
from reliability_lab.diagnostic_evidence import verify_diagnostics
from reliability_lab.recent_evidence import verify_clean_install, verify_outcome_reporting, verify_final_response


def install_offline_guard() -> None:
    """Disable tracing and reject Python socket operations in this process."""
    os.environ["LANGSMITH_TRACING"] = "false"
    os.environ["LANGCHAIN_TRACING_V2"] = "false"

    def guard(event: str, args: tuple) -> None:
        if event.startswith("socket."):
            raise PermissionError("Network disabled for offline verification")

    sys.addaudithook(guard)


def receiver_contracts(root: Path) -> dict:
    """Execute receiver contracts against fresh disposable local databases."""
    suite = unittest.defaultTestLoader.discover(str(root / "tests"), pattern="test_receiver.py")
    if suite.countTestCases() == 0:
        raise ValueError("No receiver contracts discovered")
    output = io.StringIO()
    result = unittest.TextTestRunner(stream=output, verbosity=2).run(suite)
    return {
        "kind": "fresh deterministic receiver executions; not LLM evaluations",
        "status": "passed" if result.wasSuccessful() else "failed",
        "tests_run": result.testsRun,
        "skipped": len(result.skipped),
        "failures": len(result.failures),
        "errors": len(result.errors),
        "log": output.getvalue(),
    }


def verify_offline(root: Path) -> tuple[dict, int]:
    """Check historical evidence first, then run fresh receiver contracts."""
    install_offline_guard()
    attempt = Path("work/attempts") / uuid.uuid4().hex
    directory = root / attempt
    directory.mkdir(parents=True, exist_ok=False)
    report = {
        "schema_version": 1,
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "python_version": sys.version.split()[0],
        "network": "Python socket operations blocked; no provider/tracing clients imported",
        "historical_evidence": {"status": "not_run"},
        "search_recovery_review": {"status": "not_run"},
        "historical_search_evidence": {"status": "not_run"},
        "optional_cohort_inventory": {"status": "not_run"},
        "crash_resume_evidence": {"status": "not_run"},
        "clean_install_evidence": {"status": "not_run"},
        "outcome_reporting_evidence": {"status": "not_run"},
        "final_response_evidence": {"status": "not_run"},
        "receiver_diagnostics_evidence": {"status": "not_run"},
        "native_retry_evidence": {"status": "not_run"},
        "run_budget_evidence": {"status": "not_run"},
        "receiver_contracts": {"status": "not_run"},
        "report_path": str(attempt / "report.json"),
    }
    stage = "historical_evidence"
    try:
        cases = verify_evidence(root) + verify_approval_evidence(root) + verify_missing_source_evidence(root)
        report[stage] = {"status": "passed", "kind": "stored evidence validation; no historical replay", "cases": cases}
        stage = "search_recovery_review"
        report[stage] = verify_search_review(root)
        stage = "historical_search_evidence"
        report[stage] = verify_search_evidence(root)
        stage = "optional_cohort_inventory"
        report[stage] = verify_optional_inventory(root)
        stage = "crash_resume_evidence"
        report[stage] = verify_crash_export(root)
        stage = "clean_install_evidence"
        report[stage] = verify_clean_install(root)
        stage = "outcome_reporting_evidence"
        report[stage] = verify_outcome_reporting(root)
        stage = "final_response_evidence"
        report[stage] = verify_final_response(root)
        stage = "receiver_diagnostics_evidence"
        report[stage] = verify_diagnostics(root)
        stage = "native_retry_evidence"
        report[stage] = verify_native_retry(root)
        stage = "run_budget_evidence"
        report[stage] = verify_run_budget(root)
        stage = "receiver_contracts"
        report[stage] = receiver_contracts(root)
    except (OSError, ValueError, KeyError, TypeError, StopIteration, ImportError) as exc:
        report[stage] = {"status": "failed", "error": str(exc)}
    passed = all(report[s]["status"] == "passed" for s in ("historical_evidence", "search_recovery_review", "historical_search_evidence", "optional_cohort_inventory", "crash_resume_evidence", "clean_install_evidence", "outcome_reporting_evidence", "final_response_evidence", "receiver_diagnostics_evidence", "native_retry_evidence", "run_budget_evidence", "receiver_contracts"))
    report["exit_code"] = 0 if passed else 1
    report["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
    (directory / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    return report, report["exit_code"]
