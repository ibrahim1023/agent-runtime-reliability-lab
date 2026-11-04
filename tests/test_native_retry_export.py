"""Saved coverage must preserve interruptions and actual tool/effect outcomes."""

import hashlib
import json
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
import unittest

from reliability_lab.retry_evidence import verify_native_retry

ROOT = Path(__file__).resolve().parents[1]


class NativeRetryExportContracts(unittest.TestCase):
    def altered(self, change):
        temporary = TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        root = Path(temporary.name) / 'lab'
        shutil.copytree(ROOT, root, ignore=shutil.ignore_patterns('.git', 'work', '__pycache__'))
        path = root / 'results/manifest.json'; manifest = json.loads(path.read_text())
        ref = manifest['native_retry_v1']['coverage']; target = root / ref['export']
        data = json.loads(target.read_text()); change(data); target.write_text(json.dumps(data))
        ref['sha256'] = hashlib.sha256(target.read_bytes()).hexdigest(); path.write_text(json.dumps(manifest))
        return root

    def test_coverage_checks_saved_cases_without_runtime_imports(self) -> None:
        result = verify_native_retry(ROOT)
        self.assertEqual(result['graph_cases_checked'], 6)
        self.assertEqual(result['new_graph_workers'], 0)
        self.assertFalse(result['single_uninterrupted_attempt'])

    def test_interrupted_attempts_cannot_be_relabelled_as_one_clean_pass(self) -> None:
        root = self.altered(lambda d: d.update(single_uninterrupted_successful_attempt=True))
        with self.assertRaisesRegex(ValueError, 'Native attempt accounting'):
            verify_native_retry(root)

    def test_duplicate_control_cannot_be_relabelled_task_success(self) -> None:
        root = self.altered(lambda d: d['cases'][2]['verdicts'].update(single_effect_task_completed=True))
        with self.assertRaisesRegex(ValueError, 'Native coverage differs'):
            verify_native_retry(root)
