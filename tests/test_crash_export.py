"""Stored crash observations must support the separately recorded reassessment."""

import hashlib
import json
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
import unittest

from reliability_lab.crash_evidence import verify_crash_export

ROOT = Path(__file__).resolve().parents[1]


class CrashExportContracts(unittest.TestCase):
    def setUp(self) -> None:
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name) / "lab"
        shutil.copytree(ROOT, self.root, ignore=shutil.ignore_patterns(".git", "work", "__pycache__"))

    def alter(self, change) -> None:
        path = self.root / "results/fresh/crash-resume-v1/execution.json"
        record = json.loads(path.read_text())
        change(record)
        path.write_text(json.dumps(record))
        manifest_path = self.root / "results/manifest.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["crash_resume_v1"]["execution"]["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        assessment_path = self.root / "results/fresh/crash-resume-v1/reassessment-a1.json"
        assessment = json.loads(assessment_path.read_text())
        assessment["execution_sha256"] = manifest["crash_resume_v1"]["execution"]["sha256"]
        assessment_path.write_text(json.dumps(assessment))
        manifest["crash_resume_v1"]["reassessment"]["sha256"] = hashlib.sha256(assessment_path.read_bytes()).hexdigest()
        manifest_path.write_text(json.dumps(manifest))

    def test_saved_reassessment_is_not_another_runtime_execution(self) -> None:
        report = verify_crash_export(self.root)
        self.assertEqual(report["cases_checked"], 5)
        self.assertEqual(report["original_execution_status"], "failed")
        self.assertEqual(report["worker_processes_observed"], 19)
        self.assertEqual(report["approved_tasks_completed"], 3)

    def test_control_cannot_be_relabelled_task_success_after_rehash(self) -> None:
        self.alter(lambda record: record["cases"][2]["verdicts"].update(approved_task_completed=True))
        with self.assertRaisesRegex(ValueError, "Original task verdict relabelled"):
            verify_crash_export(self.root)

    def test_changed_approved_payload_is_rejected_after_rehash(self) -> None:
        self.alter(lambda record: record["cases"][3]["tool_entries"][1].update(message="original-proposal"))
        with self.assertRaisesRegex(ValueError, "Tool journal mismatch"):
            verify_crash_export(self.root)

    def test_missing_worker_or_forged_final_report_is_rejected(self) -> None:
        self.alter(lambda record: record["cases"][0].update(answer="done"))
        with self.assertRaisesRegex(ValueError, "Final observation mismatch"):
            verify_crash_export(self.root)
