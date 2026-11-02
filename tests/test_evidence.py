"""Check that evidence validation rejects broken claims, not just stale hashes."""

import hashlib
import json
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
import unittest

from reliability_lab.evidence import verify_evidence

ROOT = Path(__file__).resolve().parents[1]


class EvidenceContracts(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        shutil.copytree(ROOT / "results", self.root / "results")
        shutil.copytree(ROOT / "reliability_lab", self.root / "reliability_lab")
        self.manifest = self.root / "results/manifest.json"
        self.case = self.root / "results/historical/idempotency/protected-1.json"

    def change_case(self, change, *, reseal: bool = True) -> None:
        data = json.loads(self.case.read_text())
        change(data)
        self.case.write_text(json.dumps(data))
        if reseal:
            manifest = json.loads(self.manifest.read_text())
            manifest["cases"][1]["sha256"] = hashlib.sha256(self.case.read_bytes()).hexdigest()
            self.manifest.write_text(json.dumps(manifest))

    def test_original_exports_have_expected_control_and_protected_counts(self) -> None:
        results = verify_evidence(self.root)
        self.assertEqual([r["committed_effects"] for r in results], [2, 1, 1, 1])
        self.assertTrue(all(r["tool_attempts"] == 2 for r in results))

    def test_changed_bytes_fail_hash_validation(self) -> None:
        self.case.write_text(self.case.read_text() + "\n")
        with self.assertRaisesRegex(ValueError, "hash"):
            verify_evidence(self.root)

    def test_extra_protected_effect_fails_even_with_updated_hash(self) -> None:
        self.change_case(lambda d: d["committed_receipts"].append(d["committed_receipts"][0]))
        with self.assertRaises(ValueError):
            verify_evidence(self.root)

    def test_changed_resumed_receipt_fails_even_with_updated_hash(self) -> None:
        self.change_case(lambda d: d["events"][5]["receipt"].update(receipt_id="different"))
        with self.assertRaises(ValueError):
            verify_evidence(self.root)

    def test_same_process_cannot_claim_fresh_process_resume(self) -> None:
        self.change_case(lambda d: [e.update(pid=d["events"][0]["pid"]) for e in d["events"]])
        with self.assertRaises(ValueError):
            verify_evidence(self.root)

    def test_changed_operation_id_fails_even_with_updated_hash(self) -> None:
        self.change_case(lambda d: d["events"][4].update(operation_id="new-operation"))
        with self.assertRaises(ValueError):
            verify_evidence(self.root)

    def test_missing_export_fails(self) -> None:
        self.case.unlink()
        with self.assertRaises((OSError, ValueError)):
            verify_evidence(self.root)

    def test_empty_manifest_cannot_pass(self) -> None:
        data = json.loads(self.manifest.read_text())
        data["cases"] = []
        self.manifest.write_text(json.dumps(data))
        with self.assertRaises(ValueError):
            verify_evidence(self.root)

    def test_export_path_cannot_leave_repository(self) -> None:
        data = json.loads(self.manifest.read_text())
        data["cases"][1]["export"] = "../outside.json"
        self.manifest.write_text(json.dumps(data))
        with self.assertRaises(ValueError):
            verify_evidence(self.root)

    def test_extracted_receiver_modification_fails_provenance_check(self) -> None:
        with (self.root / "reliability_lab/receiver.py").open("a") as stream:
            stream.write("\n# changed\n")
        with self.assertRaisesRegex(ValueError, "hash"):
            verify_evidence(self.root)
