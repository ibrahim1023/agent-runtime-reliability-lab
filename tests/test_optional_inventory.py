"""Keep optional models, interruptions and unresolved evidence separate."""

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

ROOT = Path(__file__).resolve().parents[1]


class OptionalInventoryContracts(unittest.TestCase):
    def setUp(self):
        tmp = TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)/'lab'
        shutil.copytree(ROOT, self.root, ignore=shutil.ignore_patterns('.git','work','__pycache__'))

    def alter(self, name, change, *, unresolved=False):
        p=self.root/f'results/optional/{name}.json';d=json.loads(p.read_text());change(d);p.write_text(json.dumps(d))
        p=self.root/'results/manifest.json';d=json.loads(p.read_text())
        e=d['unresolved_120b_result'] if unresolved else next(e for e in d['optional_cohorts'] if e['cohort']==name)
        e['sha256']=hashlib.sha256((self.root/e['export']).read_bytes()).hexdigest();p.write_text(json.dumps(d))

    def command(self):
        r=subprocess.run([sys.executable,'-S','-m','reliability_lab','verify-offline'],cwd=self.root,capture_output=True,text=True)
        return r.returncode,json.loads(r.stdout)

    def rejected(self):
        code,report=self.command();self.assertEqual(code,1)
        self.assertEqual(report['optional_cohort_inventory']['status'],'failed')
        self.assertEqual(report['receiver_contracts']['status'],'not_run')

    def test_inventory_is_not_a_new_model_evaluation(self):
        code,report=self.command();self.assertEqual(code,0)
        self.assertIn('optional_cohort_inventory',report)
        self.assertEqual(report['optional_cohort_inventory']['cohort_attempt_counts'],[16,1,8])
        self.assertEqual(report['optional_cohort_inventory']['unresolved_120b'],'preserved')

    def test_twenty_b_cannot_be_relabelled_as_the_120b_reproduction(self):
        self.alter('comparison-20b',lambda d:d.update(model='groq:openai/gpt-oss-120b'))
        self.rejected()

    def test_quota_interruption_does_not_receive_a_behavior_verdict(self):
        self.alter('original-present-followup-120b',lambda d:d['records'][0].update(historical_behavior_correct=False))
        self.rejected()

    def test_unresolved_result_cannot_be_claimed_resolved(self):
        self.alter('unresolved-original-present-120b',lambda d:d.update(resolution='resolved'),unresolved=True)
        self.rejected()
