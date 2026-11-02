"""Alter disposable historical review copies and exercise the public command."""

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from reliability_lab.evidence import checked_bytes

ROOT = Path(__file__).resolve().parents[1]


class SearchReviewContracts(unittest.TestCase):
    def setUp(self) -> None:
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name) / "lab"
        shutil.copytree(ROOT, self.root, ignore=shutil.ignore_patterns(".git", "work", "__pycache__"))

    def alter(self, change, *, rehash: bool = True) -> None:
        path = self.root / "results/search-recovery-review.json"
        data = json.loads(path.read_text())
        change(data)
        path.write_text(json.dumps(data))
        if rehash:
            manifest = self.root / "results/manifest.json"
            data = json.loads(manifest.read_text())
            data["search_recovery_review"]["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
            manifest.write_text(json.dumps(data))

    def run_command(self):
        result = subprocess.run([sys.executable, "-S", "-m", "reliability_lab", "verify-offline"],
                                cwd=self.root, capture_output=True, text=True)
        return result.returncode, json.loads(result.stdout)

    def rejected(self, message: str) -> None:
        code, report = self.run_command()
        self.assertEqual(code, 1, "Altered review was accepted")
        self.assertEqual(report["search_recovery_review"]["status"], "failed")
        self.assertIn(message, report["search_recovery_review"]["error"])
        self.assertEqual(report["receiver_contracts"]["status"], "not_run")

    def test_unmodified_review_keeps_evidence_counts_separate(self) -> None:
        code, report = self.run_command()
        self.assertEqual(code, 0)
        self.assertEqual(len(report["historical_evidence"]["cases"]), 16)
        self.assertEqual(report["receiver_contracts"]["tests_run"], 6)
        review = report["search_recovery_review"]
        self.assertEqual(review["roster_entries_checked"], 25)
        self.assertEqual(review["detailed_ambiguity_records_checked"], 3)
        self.assertEqual(review["fresh_graph_contracts_executed"], 0)

    def test_relabel_and_rehash_still_conflicts_with_actual_write(self) -> None:
        def relabel(data):
            for item in data["ambiguity_extracts"]:
                if item["label"] == "candidate-ambiguous-1":
                    item["historical_behavior_correct"] = True
            for item in data["historical_run_roster"]:
                if item["label"] == "candidate-ambiguous-1":
                    item["historical_behavior_correct"] = True
            next(row for row in data["seven_case_matrix"] if row["case"] == "ambiguous")["candidate"]["behavior_correct"] = True
        self.alter(relabel)
        entry = json.loads((self.root / "results/manifest.json").read_text())["search_recovery_review"]
        matched = json.loads(checked_bytes(self.root, entry["export"], entry["sha256"]))
        self.assertTrue(matched["ambiguity_extracts"][1]["historical_behavior_correct"])
        self.rejected("ambiguity verdict contradicts recorded effects")

    def test_dropped_rejected_run_cannot_improve_the_roster(self) -> None:
        self.alter(lambda data: data["historical_run_roster"].__setitem__(slice(None),
                   [row for row in data["historical_run_roster"] if row["label"] != "candidate-ambiguous-1"]))
        self.rejected("historical roster")

    def test_successful_write_cannot_claim_unchanged_files(self) -> None:
        self.alter(lambda data: data["ambiguity_extracts"][1]["final_files"].pop("/out.txt"))
        self.rejected("final files disagree with successful writes")

    def test_read_result_must_match_the_declared_source(self) -> None:
        self.alter(lambda data: data["ambiguity_extracts"][1]["tool_results"][2].update(content="@@ lines 1-2 of 2 @@\nwrong\nsource"))
        self.rejected("read result disagrees with initial source")

    def test_changed_bytes_fail_without_rehashing(self) -> None:
        self.alter(lambda data: data.update(rejection_reason="changed"), rehash=False)
        self.rejected("hash mismatch")

    def test_rejected_candidate_cannot_become_the_selected_prototype(self) -> None:
        self.alter(lambda data: data.update(selected_lab_prototype="recovery_middleware.py"))
        self.rejected("selected prototype")

    def test_matrix_cannot_disagree_with_retained_roster(self) -> None:
        self.alter(lambda data: data["seven_case_matrix"][0]["baseline"].update(tool_calls=0))
        self.rejected("matrix disagrees with roster")

    def test_missing_review_manifest_entry_cannot_skip_the_check(self) -> None:
        path = self.root / "results/manifest.json"
        data = json.loads(path.read_text())
        del data["search_recovery_review"]
        path.write_text(json.dumps(data))
        self.rejected("search_recovery_review")
