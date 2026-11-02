"""The six remaining original middleware fixtures, with scripted responses."""

from datetime import datetime, timezone
import json
from pathlib import Path
import uuid

from reliability_lab.evidence import require
from reliability_lab.offline import install_offline_guard
from reliability_lab.scripted_root import check_extractions, run_condition, runtime_identity

FIXTURES = [
    {"case": "dot", "tool": "glob", "args": {"path": ".", "pattern": "*.txt"}, "files": {"/incoming/data.txt": "found"}},
    {"case": "dot_slash", "tool": "glob", "args": {"path": "./", "pattern": "*.txt"}, "files": {"/incoming/data.txt": "found"}},
    {"case": "slash_dot", "tool": "glob", "args": {"path": "/.", "pattern": "*.txt"}, "files": {"/incoming/data.txt": "found"}},
    {"case": "explicit_scope", "tool": "glob", "args": {"path": "/visible", "pattern": "*.txt"},
     "files": {"/visible/data.txt": "visible", "/other/data.txt": "other"}},
    {"case": "empty_workspace", "tool": "ls", "args": {"path": "/"}, "files": {}},
    {"case": "empty_subdirectory", "tool": "ls", "args": {"path": "/missing"}, "files": {"/incoming/data.txt": "present"}},
]


def validate_condition(fixture: dict, observed: dict) -> None:
    """Check observed arguments and messages against the declared fixture."""
    require(observed["files_unchanged"] and observed["next_model_received_tool_result"],
            "File contents changed or model did not receive the resulting observation")
    require(observed["conversation_proposal"]["args"] == fixture["args"], "Original proposal changed")
    content = observed["model_facing_tool_result"]["content"]
    require(observed["model_facing_tool_result"]["status"] == "success", "Tool returned an error")
    if fixture["case"] in {"dot", "dot_slash", "slash_dot"}:
        require(observed["actual_tool_args"]["path"] == "/" and "/incoming/data.txt" in content,
                "Root alias was not corrected to a successful root search")
    else:
        require(observed["actual_tool_args"] == fixture["args"], "Explicit scope changed")
    if fixture["case"] == "explicit_scope":
        require("/visible/data.txt" in content and "/other/data.txt" not in content, "Search escaped explicit scope")
    if fixture["case"] == "empty_workspace":
        require("workspace currently contains zero files" in content, "Empty workspace fact was not delivered")
        require("zero files" not in observed["tool_result"]["content"], "Empty-workspace note was not distinguishable from raw result")
    if fixture["case"] == "empty_subdirectory":
        require("zero files" not in content, "Empty directory incorrectly implied empty workspace")


def run_scripted_filesystem(root: Path) -> tuple[dict, int]:
    """Execute only the six remaining cases; preserve per-case observations."""
    install_offline_guard()
    attempt = Path("work/scripted-filesystem") / uuid.uuid4().hex
    directory = root / attempt
    directory.mkdir(parents=True, exist_ok=False)
    report = {"schema_version": 1, "kind": "fresh scripted graph execution; no live-model evaluation",
              "started_at_utc": datetime.now(timezone.utc).isoformat(), "live_model_calls": 0,
              "learner_prediction": "not supplied; continued under request to proceed without another quiz",
              "assistant_hypothesis": "Root aliases are corrected, explicit scope is preserved, and empty-directory results do not imply an empty workspace.",
              "network": "Tracing disabled and Python socket operations blocked before runtime imports; not an OS sandbox",
              "report_path": str(attempt / "report.json"), "conditions": []}
    code = 1
    try:
        check_extractions(root)
        report["runtime_identity"] = runtime_identity()
        for fixture in FIXTURES:
            observed = run_condition(directory / fixture["case"], corrected=True, tool_name=fixture["tool"],
                                     tool_args=fixture["args"], initial_files=fixture["files"])
            observed.update(case=fixture["case"], initial_files=fixture["files"])
            report["conditions"].append(observed)
            validate_condition(fixture, observed)
        report["status"] = "passed"
        code = 0
    except (ImportError, OSError, ValueError, TypeError, KeyError, StopIteration) as exc:
        report["status"] = "failed"
        report["error_type"] = type(exc).__name__
        report["error"] = "Scripted filesystem fixture failed; inspect the retained per-case observations."
    report["exit_code"] = code
    report["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
    (directory / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    return report, code
