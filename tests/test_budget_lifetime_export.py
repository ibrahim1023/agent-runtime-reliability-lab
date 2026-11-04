"""Saved checkpoint budget evidence must preserve identity and worker outcomes."""

import hashlib
import json
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
import unittest

from reliability_lab.budget_lifetime_evidence import verify_lifetime

ROOT = Path(__file__).resolve().parents[1]


class LifetimeExportContracts(unittest.TestCase):
    def test_four_saved_invocations_validate_without_restarting_workers(self) -> None:
        report = verify_lifetime(ROOT)
        self.assertEqual(report['worker_invocations_checked'], 4)
        self.assertEqual(report['new_workers'], 0)

    def test_valid_phase_json_does_not_override_nonzero_exit_after_rehash(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary) / 'lab'
            shutil.copytree(ROOT, root, ignore=shutil.ignore_patterns('.git', 'work', '__pycache__'))
            p = root / 'results/manifest.json'; m = json.loads(p.read_text())
            reference = m['budget_lifetime_v1']['execution']; target = root / reference['export']
            data = json.loads(target.read_text()); data['launches'][1]['exit_code'] = 1
            target.write_text(json.dumps(data)); reference['sha256'] = hashlib.sha256(target.read_bytes()).hexdigest()
            p.write_text(json.dumps(m))
            with self.assertRaisesRegex(ValueError, 'Lifetime worker launch'):
                verify_lifetime(root)
