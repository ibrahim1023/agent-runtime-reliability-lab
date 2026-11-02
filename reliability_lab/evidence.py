"""Validate historical exports without accessing the original checkout or network."""

import hashlib
import json
from pathlib import Path


CASE_NAMES = ["unprotected-1", "protected-1", "protected-2", "protected-3"]


def require(condition: bool, message: str) -> None:
    """Raise an explicit validation error, including under Python -O."""
    if not condition:
        raise ValueError(message)


def local_file(root: Path, relative: str) -> Path:
    """Resolve a manifest path only inside the evidence repository."""
    path = Path(relative)
    require(not path.is_absolute() and ".." not in path.parts, "Unsafe manifest path")
    resolved = (root / path).resolve()
    require(resolved.is_relative_to(root.resolve()), "Manifest path leaves repository")
    return resolved


def checked_bytes(root: Path, relative: str, expected_hash: str) -> bytes:
    """Read a local file and check its recorded byte identity."""
    content = local_file(root, relative).read_bytes()
    require(hashlib.sha256(content).hexdigest() == expected_hash, f"File hash mismatch: {relative}")
    return content


def verify_case(data: dict, name: str) -> dict:
    """Cross-check event order, operation identity, effects, and receipts."""
    require(data["case"] == name and data["historical"] is True, f"{name}: wrong evidence identity")
    require(data["initial_exit"] == 86 and data["resume_exit"] == 0, f"{name}: unexpected exits")
    events = data["events"]
    require([e["event"] for e in events] == [
        "worker_start", "tool_enter", "ledger_result", "worker_start",
        "tool_enter", "ledger_result", "tool_return",
    ], f"{name}: unexpected event order")
    require(events[0]["phase"] == "initial" and events[3]["phase"] == "resume", f"{name}: wrong phases")
    first_pid, second_pid = events[0]["pid"], events[3]["pid"]
    require(type(first_pid) is int and type(second_pid) is int and first_pid != second_pid,
            f"{name}: distinct process IDs required")
    require(all(e["pid"] == first_pid for e in events[:3]) and
            all(e["pid"] == second_pid for e in events[3:]), f"{name}: inconsistent process IDs")
    first, second = events[1], events[4]
    require(bool(first["operation_id"]) and first["operation_id"] == second["operation_id"] and
            first["message"] == second["message"], f"{name}: operation changed on resume")
    receipts = [events[2]["receipt"], events[5]["receipt"]]
    for receipt in receipts:
        require(receipt["operation_id"] == first["operation_id"] and
                receipt["message"] == first["message"] and receipt["status"] == "recorded" and
                bool(receipt["receipt_id"]), f"{name}: receipt does not match action")
    require(events[6]["receipt"] == receipts[1], f"{name}: returned receipt differs")
    protected = name.startswith("protected-")
    expected_count = 1 if protected else 2
    require(type(data["expected_effect_count"]) is int and
            data["expected_effect_count"] == expected_count, f"{name}: altered expected count")
    require(events[2]["reused"] is False and events[5]["reused"] is protected,
            f"{name}: incorrect reuse flags")
    require((receipts[0] == receipts[1]) is protected, f"{name}: receipt reuse mismatch")
    if not protected:
        require(receipts[0]["receipt_id"] != receipts[1]["receipt_id"], f"{name}: duplicate receipt IDs")
    expected_rows = receipts[:1] if protected else receipts
    require(data["committed_receipts"] == expected_rows, f"{name}: committed effects disagree with journal")
    return {"case": name, "tool_attempts": 2, "committed_effects": expected_count,
            "original_receipt_reused": protected,
            "interpretation": "protected effect deduplicated" if protected else "expected duplicate-effect control"}


def verify_evidence(root: Path) -> list[dict]:
    """Verify the frozen four-case cohort and extracted receiver identity."""
    manifest = json.loads((root / "results/manifest.json").read_text())
    require(manifest["schema_version"] == 1, "Unsupported evidence schema")
    require([c["case"] for c in manifest["cases"]] == CASE_NAMES, "Incomplete or changed historical cohort")
    results = []
    for case in manifest["cases"]:
        expected = f"results/historical/idempotency/{case['case']}.json"
        require(case["export"] == expected, "Unexpected export path")
        data = json.loads(checked_bytes(root, case["export"], case["sha256"]))
        results.append(verify_case(data, case["case"]))
    extractions = manifest["extractions"]
    require(len(extractions) == 1, "Expected one receiver extraction")
    extraction = extractions[0]
    require(extraction["destination"] == "reliability_lab/receiver.py", "Wrong extracted receiver")
    source = next(s for s in manifest["sources"] if s["source"] == extraction["source"])
    require(source["sha256"] == extraction["source_sha256"], "Receiver source provenance disagrees")
    require(bool(extraction["changes"]), "Extraction changes must be documented")
    checked_bytes(root, extraction["destination"], extraction["destination_sha256"])
    return results
