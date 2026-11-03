"""Exercise truthful local reports at real SQLite receiver boundaries."""

from contextlib import closing
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest

from reliability_lab.outcome_reporting import reconcile_action
from reliability_lab.receiver import Ledger


class OutcomeReportingContracts(unittest.TestCase):
    def setUp(self) -> None:
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.path = Path(temporary.name) / 'receiver.sqlite'

    def report(self, *, decision='approve', finished=True, message='approved') -> dict:
        return reconcile_action(self.path, operation_id='op', approved_message=message,
                                decision=decision, graph_finished=finished)

    def test_single_effect_is_scoped_to_operation_and_read_only(self) -> None:
        ledger = Ledger(self.path, protected=False)
        ledger.record('other', 'unrelated')
        ledger.record('op', 'approved')
        before = self.path.read_bytes()
        result = self.report()
        self.assertEqual(result['outcome'], 'completed_once')
        self.assertEqual(result['observed_effects'], 1)
        self.assertTrue(result['task_completed'])
        self.assertEqual(self.path.read_bytes(), before)

    def test_two_valid_receipts_are_reported_as_duplicate(self) -> None:
        ledger = Ledger(self.path, protected=False)
        ledger.record('op', 'approved')
        ledger.record('op', 'approved')
        result = self.report()
        self.assertEqual(result['outcome'], 'duplicate_detected')
        self.assertEqual(result['observed_effects'], 2)
        self.assertFalse(result['task_completed'])
        self.assertIn('2', result['report'])

    def test_unreadable_evidence_is_unknown_and_missing_file_stays_missing(self) -> None:
        for invalid in (False, True):
            if invalid:
                self.path.write_text('not a SQLite database')
            result = self.report()
            self.assertEqual(result['outcome'], 'outcome_unknown')
            self.assertIsNone(result['observed_effects'])
            self.assertIsNone(result['task_completed'])
            self.assertEqual(self.path.exists(), invalid)

    def test_rejection_is_not_a_completed_task_and_rows_violate_it(self) -> None:
        ledger = Ledger(self.path, protected=True)
        result = self.report(decision='reject')
        self.assertEqual(result['outcome'], 'rejected')
        self.assertFalse(result['task_completed'])
        ledger.record('op', 'approved')
        self.assertEqual(self.report(decision='reject')['outcome'], 'policy_violation')

    def test_edit_is_compared_with_approved_replacement(self) -> None:
        Ledger(self.path, protected=True).record('op', 'approved')
        self.assertEqual(self.report(decision='edit')['outcome'], 'completed_once')
        self.assertEqual(self.report(decision='edit', message='original')['outcome'], 'payload_conflict')

    def test_finished_graph_without_receiver_row_did_not_complete_task(self) -> None:
        Ledger(self.path, protected=True)
        result = self.report()
        self.assertEqual(result['outcome'], 'not_recorded')
        self.assertEqual(result['observed_effects'], 0)
        self.assertFalse(result['task_completed'])

    def test_unfinished_graph_cannot_be_reported_complete(self) -> None:
        Ledger(self.path, protected=True).record('op', 'approved')
        self.assertEqual(self.report(finished=False)['outcome'], 'outcome_unknown')

    def test_inconsistent_receipt_cannot_support_completion(self) -> None:
        Ledger(self.path, protected=True).record('op', 'approved')
        with closing(sqlite3.connect(self.path)) as conn, conn:
            conn.execute('UPDATE entries SET receipt = ?', ('{"operation_id":"other"}',))
        result = self.report()
        self.assertNotEqual(result['outcome'], 'completed_once')
        self.assertFalse(result['task_completed'])
