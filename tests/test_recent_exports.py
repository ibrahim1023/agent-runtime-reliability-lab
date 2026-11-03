"""Reject contradictions even after a recent export's hash is refreshed."""

import hashlib
import json
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
import unittest

from reliability_lab.recent_evidence import verify_clean_install, verify_outcome_reporting

ROOT = Path(__file__).resolve().parents[1]


class RecentEvidenceContracts(unittest.TestCase):
    def setUp(self) -> None:
        temporary = TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name) / 'lab'
        shutil.copytree(ROOT, self.root, ignore=shutil.ignore_patterns('.git', 'work', '__pycache__'))

    def alter(self, section, artifact, change) -> None:
        path = self.root / 'results/manifest.json'; manifest = json.loads(path.read_text())
        reference = manifest[section][artifact]; target = self.root / reference['export']
        data = json.loads(target.read_text()); change(data)
        target.write_text(json.dumps(data)); reference['sha256'] = hashlib.sha256(target.read_bytes()).hexdigest()
        path.write_text(json.dumps(manifest))

    def test_saved_exports_validate_without_runtime_reexecution(self) -> None:
        self.assertEqual(verify_clean_install(self.root)['cases_checked'], 5)
        self.assertEqual(verify_outcome_reporting(self.root)['observations_checked'], 7)

    def test_editable_environment_cannot_be_called_clean(self) -> None:
        self.alter('clean_install_v1', 'environment', lambda d: d.update(deepagents_editable=True))
        with self.assertRaisesRegex(ValueError, 'Environment isolation'):
            verify_clean_install(self.root)

    def test_clean_control_cannot_claim_task_success(self) -> None:
        self.alter('clean_install_v1', 'comparison', lambda d: d['case_comparison'][2].update(approved_task_completed=True))
        with self.assertRaisesRegex(ValueError, 'Clean comparison'):
            verify_clean_install(self.root)

    def test_unknown_reporting_cannot_claim_success_or_zero_effects(self) -> None:
        self.alter('outcome_reporting_v1', 'execution', lambda d: d['observations'][5]['application_report'].update(task_completed=True, observed_effects=0))
        with self.assertRaisesRegex(ValueError, 'Reporting conclusion'):
            verify_outcome_reporting(self.root)

    def test_duplicate_evidence_cannot_be_dropped(self) -> None:
        self.alter('outcome_reporting_v1', 'execution', lambda d: d['observations'][2]['receiver_rows'].pop())
        with self.assertRaisesRegex(ValueError, 'Receiver observations'):
            verify_outcome_reporting(self.root)
