"""Stored CI summaries remain evidence validation, not another reproduction."""

import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from reliability_lab.portable_evidence import verify_portable_reproduction

ROOT = Path(__file__).resolve().parents[1]


class PortableEvidenceContracts(unittest.TestCase):
    def test_saved_linux_observations_validate_without_a_worker(self):
        report = verify_portable_reproduction(ROOT)
        self.assertEqual(report['status'], 'passed')
        self.assertEqual(report['new_workers'], 0)
        self.assertEqual(report['cases_checked'], 5)
        self.assertEqual(report['changed_transitive_versions'], 12)

    def test_rehashed_duplicate_success_or_green_incomplete_run_is_rejected(self):
        for fault in ('duplicate_success', 'missing_phase', 'failed_launch', 'wrong_seed'):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                shutil.copytree(ROOT / 'results', root / 'results')
                shutil.copyfile(ROOT / 'requirements-runtime.txt', root / 'requirements-runtime.txt')
                manifest_path = root / 'results/manifest.json'
                manifest = json.loads(manifest_path.read_text())
                reference = manifest['portable_reproduction_v1']['execution']
                path = root / reference['export']
                result = json.loads(path.read_text())
                if fault == 'duplicate_success':
                    result['cases'][2]['approved_task_completed'] = True
                elif fault == 'missing_phase':
                    result['cases'][0]['phase_exit_codes'].pop()
                elif fault == 'failed_launch':
                    result['runtime_exit_code'] = 1
                else:
                    result['environment']['installed_packages']['deepagents'] = '0.0.0'
                path.write_text(json.dumps(result))
                reference['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
                manifest_path.write_text(json.dumps(manifest))
                with self.assertRaises(ValueError):
                    verify_portable_reproduction(root)
