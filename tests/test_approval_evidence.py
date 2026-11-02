"""Validate durable review evidence and reject contradictions in disposable copies."""

import hashlib
import json
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
import unittest

from reliability_lab.approval_evidence import verify_approval_evidence

ROOT = Path(__file__).resolve().parents[1]


class ApprovalEvidenceContracts(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        shutil.copytree(ROOT / 'results', self.root / 'results')

    def modify(self, case: str, change) -> None:
        path = self.root / f'results/historical/approval/{case}.json'
        data = json.loads(path.read_text())
        change(data)
        path.write_text(json.dumps(data))
        path = self.root / 'results/manifest.json'
        manifest = json.loads(path.read_text())
        entry = next(c for c in manifest['approval_cases'] if c['case'] == case)
        entry['sha256'] = hashlib.sha256((self.root / entry['export']).read_bytes()).hexdigest()
        path.write_text(json.dumps(manifest))

    def test_original_approve_reject_edit_evidence(self) -> None:
        results = verify_approval_evidence(self.root)
        self.assertEqual([r['committed_effects'] for r in results], [1, 0, 1])
        self.assertTrue(all(r['effects_before_decision'] == 0 for r in results))
        self.assertTrue(all(r['simulated_reviewer'] for r in results))

    def test_effect_while_pending_is_rejected(self) -> None:
        self.modify('approve', lambda d: d['phases'][1]['ledger'].append(d['committed_receipts'][0]))
        with self.assertRaises(ValueError): verify_approval_evidence(self.root)

    def test_changed_interrupt_after_restore_is_rejected(self) -> None:
        self.modify('approve', lambda d: d['phases'][1]['interrupts'][0].update(id='different'))
        with self.assertRaises(ValueError): verify_approval_evidence(self.root)

    def test_tool_entry_before_decision_is_rejected(self) -> None:
        self.modify('approve', lambda d: d['events'].insert(2, d['events'].pop(4)))
        with self.assertRaises(ValueError): verify_approval_evidence(self.root)

    def test_rejection_with_tool_body_execution_is_rejected(self) -> None:
        self.modify('reject', lambda d: d['events'].append({'event': 'tool_enter', 'pid': d['phases'][2]['pid']}))
        with self.assertRaises(ValueError): verify_approval_evidence(self.root)

    def test_edit_committing_original_proposal_is_rejected(self) -> None:
        def change(data):
            receipt = data['committed_receipts'][0]
            receipt['message'] = 'original-proposal'
            data['phases'][2]['ledger'] = [receipt]
            data['events'][4]['message'] = 'original-proposal'
            data['events'][5]['receipt'] = receipt
        self.modify('edit', change)
        with self.assertRaises(ValueError): verify_approval_evidence(self.root)

    def test_real_reviewer_claim_is_rejected(self) -> None:
        self.modify('edit', lambda d: d.update(decision_source='real_human'))
        with self.assertRaises(ValueError): verify_approval_evidence(self.root)

    def test_mismatched_tool_result_id_is_rejected(self) -> None:
        self.modify('approve', lambda d: d['phases'][2]['messages'][2].update(tool_call_id='other'))
        with self.assertRaises(ValueError): verify_approval_evidence(self.root)

    def test_missing_approval_cohort_is_rejected(self) -> None:
        path = self.root / 'results/manifest.json'
        manifest = json.loads(path.read_text()); manifest['approval_cases'] = []
        path.write_text(json.dumps(manifest))
        with self.assertRaises(ValueError): verify_approval_evidence(self.root)
