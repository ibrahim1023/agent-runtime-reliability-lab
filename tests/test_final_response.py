"""Application delivery must follow receiver evidence, not a successful model answer."""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from reliability_lab.final_response import final_response
from reliability_lab.receiver import Ledger


class FinalResponseContracts(unittest.TestCase):
    def setUp(self) -> None:
        temporary = TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        self.path = Path(temporary.name) / 'receiver.sqlite'

    def deliver(self, *, decision='approve', message='approved', finished=True) -> dict:
        return final_response(self.path, operation_id='op', approved_message=message,
                              decision=decision, graph_finished=finished, model_answer='MODEL SUCCESS RECEIPT')

    def test_unknown_never_falls_back_to_model_success(self) -> None:
        result = self.deliver()
        self.assertEqual(result['model_answer'], 'MODEL SUCCESS RECEIPT')
        self.assertEqual(result['reconciliation']['outcome'], 'outcome_unknown')
        self.assertIn('unknown', result['user_response'])
        self.assertNotIn('MODEL SUCCESS RECEIPT', result['user_response'])
        self.assertFalse(self.path.exists())

    def test_duplicate_is_disclosed_in_final_response(self) -> None:
        ledger = Ledger(self.path, protected=False)
        ledger.record('op', 'approved'); ledger.record('op', 'approved')
        result = self.deliver()
        self.assertEqual(result['reconciliation']['outcome'], 'duplicate_detected')
        self.assertIn('Duplicate detected', result['user_response'])
        self.assertFalse(result['reconciliation']['task_completed'])

    def test_confirmed_edit_names_the_approved_contents(self) -> None:
        Ledger(self.path, protected=True).record('op', 'reviewer-approved')
        result = self.deliver(decision='edit', message='reviewer-approved')
        self.assertTrue(result['reconciliation']['task_completed'])
        self.assertIn('reviewer-approved', result['user_response'])

    def test_reject_and_unfinished_execution_do_not_claim_completion(self) -> None:
        Ledger(self.path, protected=True)
        result = self.deliver(decision='reject')
        self.assertEqual(result['reconciliation']['outcome'], 'rejected')
        self.assertFalse(result['reconciliation']['task_completed'])
        self.assertIsNone(self.deliver(finished=False)['reconciliation']['task_completed'])
