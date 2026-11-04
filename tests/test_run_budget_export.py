"""Saved run caps must retain blocked requests and actual attempts."""

import hashlib
import json
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
import unittest

from reliability_lab.run_budget_evidence import verify_run_budget

ROOT = Path(__file__).resolve().parents[1]


class RunBudgetExportContracts(unittest.TestCase):
    def test_stored_budget_evidence_needs_no_graph_execution(self) -> None:
        result = verify_run_budget(ROOT)
        self.assertEqual(result['graph_cases_checked'], 4)
        self.assertEqual(result['body_entries_observed'], 27)
        self.assertEqual(result['new_graph_workers'], 0)

    def test_missing_blocked_response_is_rejected_after_rehash(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary) / 'lab'
            shutil.copytree(ROOT, root, ignore=shutil.ignore_patterns('.git', 'work', '__pycache__'))
            p = root / 'results/manifest.json'; manifest = json.loads(p.read_text())
            reference = manifest['run_budget_v1']['execution']; target = root / reference['export']
            data = json.loads(target.read_text()); data['cases'][1]['tool_messages'].pop()
            target.write_text(json.dumps(data)); reference['sha256'] = hashlib.sha256(target.read_bytes()).hexdigest()
            p.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, 'Run budget case contradiction'):
                verify_run_budget(root)
