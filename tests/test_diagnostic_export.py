"""Diagnostics evidence must not turn unavailable hashes into an unchanged claim."""

import hashlib
import json
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
import unittest

from reliability_lab.diagnostic_evidence import verify_diagnostics

ROOT = Path(__file__).resolve().parents[1]


class DiagnosticEvidenceContracts(unittest.TestCase):
    def test_six_saved_replays_are_not_new_graph_executions(self) -> None:
        result = verify_diagnostics(ROOT)
        self.assertEqual(result['saved_replay_conditions_checked'], 6)
        self.assertEqual(result['new_graph_workers'], 0)

    def test_missing_hashes_cannot_be_claimed_unchanged_after_rehash(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary) / 'lab'
            shutil.copytree(ROOT, root, ignore=shutil.ignore_patterns('.git', 'work', '__pycache__'))
            path = root / 'results/manifest.json'; manifest = json.loads(path.read_text())
            reference = manifest['receiver_diagnostics_v1']['corrected']; target = root / reference['export']
            data = json.loads(target.read_text())
            data['conditions'][1]['first_delivery']['receiver_bytes_unchanged'] = True
            target.write_text(json.dumps(data)); reference['sha256'] = hashlib.sha256(target.read_bytes()).hexdigest()
            path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, 'Unavailable diagnostic evidence'):
                verify_diagnostics(root)
