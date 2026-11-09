"""Allowlisted observations for one hosted reproduction; never launch graphs."""

import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import platform
import re
import sys

from reliability_lab.crash_evidence import assess_case
from reliability_lab.recent_evidence import validate_saved_run

CASES = ("protected-approve-1", "protected-approve-2", "unprotected-approve-control",
         "protected-edit", "protected-reject")


def summarize_execution(report: dict, exit_code: int | None) -> dict:
    """Recompute existing contracts and omit raw receipts, answers and paths."""
    plan_path = Path(__file__).resolve().parents[1] / "results/next-experiment-plan-v1.json"
    try:
        validate_saved_run(report, json.loads(plan_path.read_text()))
        consistent = True
    except (KeyError, TypeError, ValueError, IndexError):
        consistent = False
    observations = report.get("cases", [])
    rows = []
    for case in observations:
        if case.get("case") not in CASES:
            continue
        try:
            verdict = assess_case(case)
            bounded = all(not p["timeout"] and 0 <= p["duration_s"] <= 30 for p in case["phases"])
            rows.append({"case": case["case"], "contract_met": verdict["contract_met"] and bounded,
                         "tool_entries": verdict["tool_body_entries"], "committed_effects": verdict["committed_effects"],
                         "approved_task_completed": verdict["approved_task_completed"],
                         "graph_completed": verdict["graph_completed"],
                         "review_policy_handled": verdict["review_policy_handled"],
                         "exact_receipt_reused": (case["receiver_results"][0]["receipt"] ==
                                                   case["receiver_results"][1]["receipt"])
                                                  if len(case["receiver_results"]) == 2 else None,
                         "report_accounts_for_all_effects": verdict["report_accounts_for_all_effects"],
                         "phase_exit_codes": [p["exit_code"] for p in case["phases"]],
                         "phase_effect_counts": [p["effects"] for p in case["phases"]],
                         "phase_tool_entries": [p["tool_entries"] for p in case["phases"]],
                         "fresh_processes": verdict["checks"]["fresh_processes"],
                         "stable_approved_identity": verdict["checks"]["stable_approved_identity"]})
        except (KeyError, TypeError, ValueError, IndexError):
            rows.append({"case": case["case"], "contract_met": False})
    roster = [c.get("case") for c in observations] == list(CASES)
    workers = sum(len(c.get("phases", [])) for c in observations)
    passed = (consistent and exit_code == 0 and report.get("status") == "passed" and roster and workers == 19
              and report.get("worker_processes") == 19 and all(row["contract_met"] for row in rows))
    return {"runtime_exit_code": exit_code, "all_contracts_met": passed,
            "saved_observations_consistent": consistent, "roster_matches": roster, "worker_phases_observed": workers, "cases": rows}


def environment_identity() -> dict:
    """Record installed versions and origin facts without publishing paths."""
    prefix = Path(sys.prefix).resolve()
    spec = importlib.util.find_spec("deepagents")
    distribution = importlib.metadata.distribution("deepagents")
    direct = json.loads(distribution.read_text("direct_url.json") or "{}")
    packages = {d.metadata["Name"].lower().replace("_", "-"): d.version
                for d in importlib.metadata.distributions()}
    configuration = (prefix / "pyvenv.cfg").read_text()
    return {"python": platform.python_version(), "system": platform.system(), "machine": platform.machine(),
            "virtual_environment": sys.prefix != sys.base_prefix,
            "system_site_packages": "include-system-site-packages = true" in configuration.lower(),
            "deepagents_inside_environment": bool(spec and spec.origin and Path(spec.origin).resolve().is_relative_to(prefix)),
            "deepagents_editable": bool(direct.get("dir_info", {}).get("editable")),
            "installed_packages": dict(sorted(packages.items()))}


def selected_runtime(report: dict) -> dict:
    """Copy only known version and selected-module identity fields."""
    runtime = report.get("runtime", {})
    packages = {name: value for name, value in runtime.get("packages", {}).items()
                if re.fullmatch(r"[a-z0-9-]+", name) and re.fullmatch(r"[0-9A-Za-z.+-]+", value)}
    hashes = {name: value for name, value in runtime.get("selected_loaded_module_sha256", {}).items()
              if re.fullmatch(r"[a-z_]+(?:\.[a-z_]+)+", name) and re.fullmatch(r"[a-f0-9]{64}", value)}
    return {"packages": packages, "selected_loaded_module_sha256": hashes}


def main() -> int:
    """Capture origin facts, or write only public summary JSON for CI upload."""
    directory = Path("work/ci")
    directory.mkdir(parents=True, exist_ok=True)
    if sys.argv[1:] == ["environment"]:
        identity = environment_identity()
        (directory / "environment.json").write_text(json.dumps(identity, indent=2) + "\n")
        return 0 if (identity["virtual_environment"] and not identity["system_site_packages"]
                     and identity["deepagents_inside_environment"] and not identity["deepagents_editable"]) else 1
    report, identity = {}, {}
    for name, destination in (("execution.json", report), ("environment.json", identity)):
        try:
            destination.update(json.loads((directory / name).read_text()))
        except (OSError, ValueError):
            pass
    code_path = directory / "runtime-exit.txt"
    code = int(code_path.read_text()) if code_path.exists() else None
    summary = summarize_execution(report, code)
    seeds = dict(line.split("==") for line in Path("requirements-runtime.txt").read_text().splitlines()
                 if line and not line.startswith("#"))
    seeds_match = all(identity.get("installed_packages", {}).get(k) == v for k, v in seeds.items())
    origin = (identity.get("virtual_environment") is True and identity.get("system_site_packages") is False
              and identity.get("deepagents_inside_environment") is True and identity.get("deepagents_editable") is False)
    summary.update(live_model_calls=report.get("live_model_calls"),
                   estimated_provider_tokens=report.get("estimated_provider_tokens"), environment=identity, seed_versions_match=seeds_match, runtime_identity=selected_runtime(report),
                   experiment_id="portable-crash-reproduction-v1", kind="allowlisted observations from one runtime attempt",
                   commit=os.environ.get("GITHUB_SHA"), run_id=os.environ.get("GITHUB_RUN_ID"),
                   run_attempt=os.environ.get("GITHUB_RUN_ATTEMPT"),
                   learner_prediction=os.environ.get("LEARNER_PREDICTION", "not supplied"),
                   install_outcome=os.environ.get("INSTALL_OUTCOME", "not_observed"),
                   runtime_outcome=os.environ.get("RUNTIME_OUTCOME", "not_observed"))
    summary["all_contracts_met"] = (summary["all_contracts_met"] and seeds_match and origin
                                    and identity.get("python") == "3.14.6" and identity.get("system") == "Linux")
    (directory / "public-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return 0 if summary["all_contracts_met"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
