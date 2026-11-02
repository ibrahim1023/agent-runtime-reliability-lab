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
        "receiver_contracts": {"status": "not_run"},
        "report_path": str(attempt / "report.json"),
    }
    stage = "historical_evidence"
    try:
        cases = verify_evidence(root)
        report[stage] = {"status": "passed", "kind": "stored evidence validation; no historical replay", "cases": cases}
        stage = "receiver_contracts"
        report[stage] = receiver_contracts(root)
    except (OSError, ValueError, KeyError, TypeError, StopIteration, ImportError) as exc:
        report[stage] = {"status": "failed", "error": str(exc)}
    passed = all(report[s]["status"] == "passed" for s in ("historical_evidence", "receiver_contracts"))
    report["exit_code"] = 0 if passed else 1
    report["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
    (directory / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    return report, report["exit_code"]
