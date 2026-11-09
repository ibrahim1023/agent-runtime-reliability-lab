"""Assessor regressions reuse a prior trace only as a negative fixture."""

import copy
import json
from pathlib import Path
import unittest

from reliability_lab.approval_budget_evidence import assess_approval_case

ROOT = Path(__file__).resolve().parents[1]


class ApprovalBudgetEvidenceContracts(unittest.TestCase):
    def test_old_approval_before_block_cannot_claim_the_new_policy(self):
        old = json.loads((ROOT / 'results/fresh/budget-recovery-v1/execution.json').read_text())['cases'][0]
        plan = json.loads((ROOT / 'results/budget-aware-approval-plan-v1.json').read_text())
        expected = plan['conditions'][4]
        case = copy.deepcopy(old)
        case.update(case=expected['case'], mode='candidate', approved_message='note')
        case['phases'] = case['phases'][:5]
        case['verdicts'] = {'contract_met': True}
        self.assertFalse(assess_approval_case(case, expected)['contract_met'])

    def test_missing_worker_output_is_not_success(self):
        plan = json.loads((ROOT / 'results/budget-aware-approval-plan-v1.json').read_text())
        case = {'case': plan['conditions'][0]['case'], 'phases': [], 'verdicts': {'contract_met': True}}
        self.assertFalse(assess_approval_case(case, plan['conditions'][0])['contract_met'])

    def test_approved_edit_trace_is_accepted_but_counting_before_review_is_not(self):
        expected = json.loads((ROOT / 'results/budget-aware-approval-plan-v1.json').read_text())['conditions'][5]
        receipt = {'operation_id': 'first', 'message': 'approved-note', 'receipt_id': 'receipt', 'status': 'recorded'}
        encoded = json.dumps(receipt)
        interrupt = [{'id': 'review', 'value': {'action_requests': [{'name': 'record_action', 'args': {'message': 'note'}}]}}]
        phases = [
            {'phase': 'initial', 'pid': 10, 'exit_code': 0, 'timeout': False, 'duration_s': 0.1, 'effects': 0,
             'observation': {'pid': 10, 'thread_count_after': 0, 'input_kind': 'new_user_message',
                             'interrupts': interrupt}},
            {'phase': 'edit-first', 'pid': 11, 'exit_code': 0, 'timeout': False, 'duration_s': 0.1, 'effects': 1,
             'observation': {'pid': 11, 'thread_count_after': 1, 'input_kind': 'simulated_decision',
                             'interrupts': [], 'checkpoint_next': [], 'final_tool_status': 'success',
                             'answer_source': 'scripted_model', 'answer': encoded, 'final_tool_content': encoded}}]
        attempt = {'event': 'tool_enter', 'phase': 'edit-first', 'operation_id': 'first',
                   'message': 'approved-note', 'thread_count': 1}
        result = {'event': 'receiver_result', 'phase': 'edit-first', 'receipt': receipt, 'reused': False}
        events = [{'event': 'worker_start', 'phase': 'initial', 'pid': 10},
                  {'event': 'worker_start', 'phase': 'edit-first', 'pid': 11},
                  {'event': 'reviewer_decision', 'phase': 'edit-first', 'source': 'simulated_reviewer',
                   'decision': {'type': 'edit'}}, attempt, result]
        case = {'case': 'candidate-edit', 'mode': 'candidate', 'first_operation_id': 'first',
                'next_operation_id': 'next', 'phases': phases, 'events': events,
                'entries': [receipt], 'tool_entries': [attempt], 'receiver_results': [result]}
        self.assertTrue(assess_approval_case(case, expected)['contract_met'])
        case['phases'][0]['observation']['thread_count_after'] = 1
        self.assertFalse(assess_approval_case(case, expected)['contract_met'])
