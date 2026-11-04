"""Preserved replay approval and new-request blocking must agree with real events."""

import hashlib
import json
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
import unittest

from reliability_lab.budget_recovery_evidence import verify_budget_recovery

ROOT=Path(__file__).resolve().parents[1]


class BudgetRecoveryExportContracts(unittest.TestCase):
    def test_saved_recovery_needs_no_new_workers(self) -> None:
        result=verify_budget_recovery(ROOT)
        self.assertEqual(result['worker_phases_checked'],12)
        self.assertEqual(result['new_workers'],0)

    def test_approval_resubmitted_on_replay_is_rejected_after_rehash(self) -> None:
        with TemporaryDirectory() as temporary:
            root=Path(temporary)/'lab'
            shutil.copytree(ROOT,root,ignore=shutil.ignore_patterns('.git','work','__pycache__'))
            p=root/'results/manifest.json';m=json.loads(p.read_text());ref=m['budget_recovery_v1']['execution']
            target=root/ref['export'];data=json.loads(target.read_text())
            data['cases'][0]['phases'][3]['observation']['input_kind']='simulated_approval'
            target.write_text(json.dumps(data));ref['sha256']=hashlib.sha256(target.read_bytes()).hexdigest();p.write_text(json.dumps(m))
            with self.assertRaisesRegex(ValueError,'Recovery phase input'):
                verify_budget_recovery(root)
