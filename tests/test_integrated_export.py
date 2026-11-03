"""Preserved model output cannot replace evidence-aware application delivery."""

import hashlib
import json
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
import unittest

from reliability_lab.recent_evidence import verify_final_response

ROOT = Path(__file__).resolve().parents[1]


class IntegratedEvidenceContracts(unittest.TestCase):
    def setUp(self) -> None:
        temporary = TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name) / 'lab'
        shutil.copytree(ROOT, self.root, ignore=shutil.ignore_patterns('.git', 'work', '__pycache__'))

    def alter(self, change) -> None:
        p = self.root / 'results/manifest.json'; manifest = json.loads(p.read_text())
        ref = manifest['final_response_v1']['execution']; target = self.root / ref['export']
        data = json.loads(target.read_text()); change(data); target.write_text(json.dumps(data))
        ref['sha256'] = hashlib.sha256(target.read_bytes()).hexdigest(); p.write_text(json.dumps(manifest))

    def test_six_deliveries_validate_without_graph_execution(self) -> None:
        result = verify_final_response(self.root)
        self.assertEqual(result['responses_checked'], 6)
        self.assertEqual(result['graph_cases_checked'], 5)

    def test_unknown_cannot_deliver_preserved_model_success(self) -> None:
        self.alter(lambda d: d['deliveries'][-1]['response'].update(user_response=d['deliveries'][-1]['response']['model_answer']))
        with self.assertRaisesRegex(ValueError, 'Final application response'):
            verify_final_response(self.root)

    def test_edit_cannot_report_original_proposal(self) -> None:
        self.alter(lambda d: d['deliveries'][3]['response'].update(user_response='Recorded original-proposal'))
        with self.assertRaisesRegex(ValueError, 'Final application response'):
            verify_final_response(self.root)
