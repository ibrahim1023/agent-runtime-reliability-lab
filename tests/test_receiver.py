"""Receiver contracts adapted from the original idempotency lab local_checks."""

from concurrent.futures import ThreadPoolExecutor
import gc
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
import warnings

from reliability_lab.receiver import Ledger


class ReceiverContracts(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "ledger.sqlite"

    def test_conflicting_payload_is_rejected_without_another_effect(self) -> None:
        ledger = Ledger(self.path, protected=True)
        first, _ = ledger.record("operation-1", "original")
        before = ledger.entries()
        with self.assertRaises(ValueError):
            ledger.record("operation-1", "changed")
        self.assertEqual(ledger.entries(), before)
        receipt, reused = ledger.record("operation-1", "original")
        self.assertEqual(receipt, first)
        self.assertTrue(reused)
        self.assertEqual(len(ledger.entries()), 1)

    def test_reopened_receiver_returns_original_receipt(self) -> None:
        first, reused = Ledger(self.path, protected=True).record("operation-1", "note")
        self.assertFalse(reused)
        reopened = Ledger(self.path, protected=True)
        second, reused = reopened.record("operation-1", "note")
        self.assertTrue(reused)
        self.assertEqual(first, second)
        self.assertEqual(len(reopened.entries()), 1)

    def test_distinct_id_permits_a_new_action_with_same_contents(self) -> None:
        ledger = Ledger(self.path, protected=True)
        first, _ = ledger.record("operation-1", "note")
        second, reused = ledger.record("operation-2", "note")
        self.assertFalse(reused)
        self.assertNotEqual(first, second)
        self.assertEqual(len(ledger.entries()), 2)

    def test_eight_concurrent_duplicates_commit_once(self) -> None:
        ledger = Ledger(self.path, protected=True)
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(lambda _: ledger.record("operation-1", "note"), range(8)))
        self.assertEqual(len(ledger.entries()), 1)
        self.assertEqual(len({receipt for receipt, _ in results}), 1)
        self.assertEqual(sum(not reused for _, reused in results), 1)

    def test_unprotected_control_records_two_effects(self) -> None:
        ledger = Ledger(self.path, protected=False)
        first, first_reused = ledger.record("operation-1", "note")
        second, second_reused = ledger.record("operation-1", "note")
        self.assertFalse(first_reused)
        self.assertFalse(second_reused)
        self.assertNotEqual(first, second)
        self.assertEqual(len(ledger.entries()), 2)

    @unittest.skipUnless(__import__("sys").version_info >= (3, 13), "SQLite close warnings require Python 3.13+")
    def test_database_connections_are_closed(self) -> None:
        gc.collect()
        with warnings.catch_warnings(record=True) as captured:
            warnings.simplefilter("always", ResourceWarning)
            ledger = Ledger(self.path, protected=True)
            ledger.record("operation-1", "note")
            ledger.record("operation-1", "note")
            ledger.entries()
            gc.collect()
        self.assertEqual([w for w in captured if issubclass(w.category, ResourceWarning)], [])


if __name__ == "__main__":
    unittest.main()
