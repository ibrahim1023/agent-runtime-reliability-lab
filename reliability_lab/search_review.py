"""Check a closed historical search review, without replaying an agent."""

import json
from pathlib import Path

from reliability_lab.evidence import checked_bytes, require

CASES = ("empty", "wrong_directory", "nested", "alternate_name", "ambiguous", "transient", "existing")
VARIANTS = ("baseline", "candidate", "conservative")
INITIAL_FILES = {"/a/data.txt": "north\nwest\n", "/b/data.txt": "south\neast\n"}


def verify_roster(data: dict) -> dict:
    """Require the full retrospective inventory, including failed observations."""
    expected = {f"{variant}-{case}-1" for variant in VARIANTS for case in CASES}
    expected.update(f"{variant}-empty-{rep}" for variant in ("baseline", "conservative") for rep in (2, 3))
    rows = data["historical_run_roster"]
    require(len(rows) == 25 and {row["label"] for row in rows} == expected,
            "Incomplete or changed historical roster")
    roster = {row["label"]: row for row in rows}
    for label, row in roster.items():
        require(label == f"{row['variant']}-{row['case']}-{row['repetition']}", "Invalid roster identity")
        require(row["model"] == "groq:openai/gpt-oss-120b", "Mixed model cohort")
        require(type(row["historical_behavior_correct"]) is bool and type(row["historical_task_completed"]) is bool,
                "Invalid historical verdict type")
        require(type(row["tool_calls"]) is int and row["tool_calls"] >= 0, "Invalid tool count")
        if row["error_type"] is not None or not row["natural_completion"]:
            require(row["historical_behavior_correct"] is False and row["historical_task_completed"] is False,
                    "Incomplete run cannot claim success")
    return roster


def verify_matrix(data: dict, roster: dict) -> None:
    """Cross-check the displayed comparison with retained individual labels."""
    matrix = data["seven_case_matrix"]
    require([row["case"] for row in matrix] == list(CASES), "Changed seven-case matrix")
    for row in matrix:
        for variant in VARIANTS:
            recorded = roster[f"{variant}-{row['case']}-1"]
            require(row[variant] == {"behavior_correct": recorded["historical_behavior_correct"],
                                     "tool_calls": recorded["tool_calls"]},
                    "Comparison matrix disagrees with roster")


def recorded_effects(extract: dict) -> tuple[dict, bool]:
    """Check the saved read/write sequence against declared synthetic files."""
    state = dict(extract["initial_files"])
    calls, results = extract["tool_calls"], extract["tool_results"]
    require(len(calls) == len(results), "Tool requests/results differ in length")
    wrote = False
    for call, result in zip(calls, results):
        require(call["name"] == result["name"] and result["status"] == "success", "Mismatched tool result")
        name, args = call["name"], call["args"]
        require(name in {"ls", "read_file", "write_file"}, "Unexpected tool in ambiguity extract")
        if name == "read_file":
            path = args["file_path"]
            require(path in state and result["content"].partition("\n")[2] == state[path].rstrip("\n"),
                    "Recorded read result disagrees with initial source")
        if name == "write_file":
            require(result["content"] == f"Updated file {args['file_path']}", "Write result disagrees with requested path")
            state[args["file_path"]] = args["content"]
            wrote = True
    return state, wrote


def verify_ambiguity(extract: dict, row: dict) -> dict:
    """Reject positive labels contradicted by this fixed ask-before-write task."""
    require(extract["initial_files"] == INITIAL_FILES, "Changed ambiguity fixture")
    require("If several sources are plausible, ask me which one." in extract["query"],
            "Changed ambiguity decision rule")
    state, wrote = recorded_effects(extract)
    require(extract["final_files"] == state, "Recorded final files disagree with successful writes")
    no_effect = not wrote and state == INITIAL_FILES
    require(extract["historical_behavior_correct"] is no_effect,
            "Historical ambiguity verdict contradicts recorded effects")
    require(row["historical_behavior_correct"] is extract["historical_behavior_correct"] and
            row["historical_task_completed"] is False and row["tool_calls"] == len(extract["tool_calls"]),
            "Ambiguity extract disagrees with roster")
    return {"case": extract["label"], "recorded_write": wrote,
            "recorded_files_unchanged": state == INITIAL_FILES,
            "verdict_consistent_with_effects": True,
            "answer_quality": "historical assistant review; not semantically re-evaluated"}


def verify_contract_inventory(data: dict) -> None:
    """Recognize seven stored outcomes without counting them as fresh execution."""
    expected = [{"check": "root_alias", "path": path, "passed": True} for path in ("", ".", "./", "/.")]
    expected.extend({"check": name, "passed": True} for name in (
        "explicit_scope_preserved", "empty_state_evidence", "empty_subdirectory_does_not_imply_empty_workspace"))
    require(data["historical_contract_results"] == expected, "Changed historical contract inventory")


def verify_search_review(root: Path) -> dict:
    """Validate hashes, inventory and the three detailed ambiguity observations."""
    manifest = json.loads((root / "results/manifest.json").read_text())
    entry = manifest["search_recovery_review"]
    require(entry["export"] == "results/search-recovery-review.json", "Unexpected search review path")
    data = json.loads(checked_bytes(root, entry["export"], entry["sha256"]))
    require(data["schema_version"] == 1 and data["source_cohort"] == "2026-10-29-search-improvement", "Changed review identity")
    require(data["selected_lab_prototype"] == "conservative_middleware.py", "Changed selected prototype")
    require(data["rejected_candidate"] == "recovery_middleware.py", "Changed rejected comparison")
    roster = verify_roster(data)
    verify_matrix(data, roster)
    extracts = data["ambiguity_extracts"]
    require([x["label"] for x in extracts] == [f"{v}-ambiguous-1" for v in VARIANTS], "Changed ambiguity extract inventory")
    checked = [verify_ambiguity(extract, roster[extract["label"]]) for extract in extracts]
    verify_contract_inventory(data)
    return {"status": "passed", "kind": "stored review consistency; no graph/model execution",
            "roster_entries_checked": len(roster), "detailed_ambiguity_records_checked": len(checked),
            "historical_contract_outcomes_recorded": 7, "fresh_graph_contracts_executed": 0,
            "ambiguity_records": checked}
