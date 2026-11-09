"""Protect the public export's outcome and data-minimization boundary."""

import copy
import json
from pathlib import Path
import unittest

from reliability_lab.portable_summary import summarize_execution

ROOT = Path(__file__).resolve().parents[1]


class PortableSummaryContracts(unittest.TestCase):
    def setUp(self):
        self.report = json.loads((ROOT / "results/fresh/clean-install-v1/execution.json").read_text())

    def test_control_duplicate_is_not_task_success_and_raw_fields_stay_private(self):
        self.report["secret_debug"] = "/private/credential-marker"
        summary = summarize_execution(self.report, 0)
        self.assertTrue(summary["all_contracts_met"])
        self.assertEqual([(c["tool_entries"], c["committed_effects"]) for c in summary["cases"]],
                         [(2, 1), (2, 1), (2, 2), (2, 1), (0, 0)])
        self.assertFalse(summary["cases"][2]["approved_task_completed"])
        self.assertTrue(summary["cases"][0]["exact_receipt_reused"])
        encoded = json.dumps(summary)
        for value in ("/private/credential-marker", self.report["cases"][0]["operation_id"],
                      self.report["cases"][0]["answer"]):
            self.assertNotIn(value, encoded)

    def test_successful_report_does_not_override_nonzero_process_exit(self):
        summary = summarize_execution(self.report, 1)
        self.assertFalse(summary["all_contracts_met"])
        self.assertEqual(summary["runtime_exit_code"], 1)

    def test_incomplete_or_mismatched_observations_do_not_pass(self):
        for mutation in ("drop_case", "phase_timeout", "receipt", "roster"):
            with self.subTest(mutation=mutation):
                report = copy.deepcopy(self.report)
                if mutation == "drop_case":
                    report["cases"].pop()
                elif mutation == "phase_timeout":
                    report["cases"][0]["phases"][0]["timeout"] = True
                elif mutation == "receipt":
                    report["cases"][0]["receiver_results"][1]["receipt"]["receipt_id"] = "wrong"
                else:
                    report["cases"][0]["case"] = "unexpected"
                self.assertFalse(summarize_execution(report, 0)["all_contracts_met"])

    def test_missing_or_interrupted_report_is_not_an_empty_success(self):
        for report in ({}, {"status": "interrupted", "error": "/private/marker", "cases": []}):
            with self.subTest(report=report):
                summary = summarize_execution(report, 1)
                self.assertFalse(summary["all_contracts_met"])
                self.assertNotIn("/private/marker", json.dumps(summary))
