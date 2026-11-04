"""A diagnostic read must not prevent the application from reporting an outcome."""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from delivery_replay_fixture import prepare_replay
from reliability_lab.reported_crash import run_reported_crash

ROOT = Path(__file__).resolve().parents[1]


class DeliveryDiagnosticsContracts(unittest.TestCase):
    def setUp(self) -> None:
        temporary = TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name) / 'lab'
        self.graph = prepare_replay(ROOT, self.root)
        self.receiver = self.root / 'work/replayed-graph/protected-approve-1/receiver.sqlite'

    def replay(self):
        with patch('reliability_lab.reported_crash.run_crash_resume', return_value=(self.graph, 0)):
            return run_reported_crash(self.root)

    def test_available_receiver_keeps_existing_contract(self) -> None:
        report, code = self.replay()
        self.assertEqual(code, 0)
        self.assertEqual(report['deliveries'][0]['response']['reconciliation']['outcome'], 'completed_once')

    def test_missing_ordinary_receiver_still_delivers_unknown(self) -> None:
        self.receiver.unlink()
        report, code = self.replay()
        self.assertEqual(code, 1)  # Frozen once-completion criterion is genuinely unmet.
        first = report['deliveries'][0]
        self.assertEqual(first['response']['reconciliation']['outcome'], 'outcome_unknown')
        self.assertEqual(first['response']['model_answer'], self.graph['cases'][0]['answer'])
        self.assertIsNone(first['receiver_sha256_before'])
        self.assertIsNone(first['receiver_bytes_unchanged'])
        self.assertFalse(self.receiver.exists())
        self.assertTrue((self.root / report['report_path']).is_file())

    def test_diagnostic_hash_failure_does_not_override_readable_sql(self) -> None:
        original = Path.read_bytes
        def diagnostic_failure(path):
            if path == self.receiver:
                raise PermissionError('controlled diagnostic read failure')
            return original(path)
        with patch.object(Path, 'read_bytes', diagnostic_failure):
            report, code = self.replay()
        self.assertEqual(code, 1)  # We cannot prove the frozen byte-identity invariant.
        first = report['deliveries'][0]
        self.assertEqual(first['response']['reconciliation']['outcome'], 'completed_once')
        self.assertIsNone(first['receiver_sha256_before'])
        self.assertIsNone(first['receiver_bytes_unchanged'])
        self.assertEqual(first['receiver_diagnostics']['before']['error_type'], 'PermissionError')
