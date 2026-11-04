"""Attempt budgets and side effects must agree with actual native-runtime evidence."""

import copy
import json
import unittest

from reliability_lab.retry_evidence import assess_retry_case


def write_case(protected=False):
    receipt = {'operation_id': 'op', 'message': 'note', 'receipt_id': 'one', 'status': 'recorded'}
    second = receipt if protected else {**receipt, 'receipt_id': 'two'}
    return {'operation_id': 'op', 'protected': protected, 'graph_outcome': 'completed', 'tool_status': 'success',
            'tool_content': json.dumps(second), 'answer': json.dumps(second),
            'duration_s': .1, 'case_duration_s': .2, 'controller_joined': True,
            'entries': [receipt] if protected else [receipt, second],
            'events': [{'event': 'model_proposal'}, {'event': 'tool_enter', 'operation_id': 'op'},
                       {'event': 'receiver_result', 'receipt': receipt, 'reused': False},
                       {'event': 'tool_enter', 'operation_id': 'op'},
                       {'event': 'receiver_result', 'receipt': second, 'reused': protected},
                       {'event': 'model_observed_tool', 'status': 'success', 'content': json.dumps(second)}],
            'model_observations': [{'status': 'success', 'content': json.dumps(second)}]}


class RetryEvidenceContracts(unittest.TestCase):
    def test_expected_duplicate_control_is_not_task_success(self) -> None:
        expected = {'expected_entries': 2, 'expected_effects': 2, 'expected_graph': 'completed', 'expected_tool_status': 'success'}
        result = assess_retry_case(write_case(), expected)
        self.assertTrue(result['contract_met'])
        self.assertFalse(result['single_effect_task_completed'])

    def test_protected_replay_must_reuse_exact_receipt(self) -> None:
        expected = {'expected_entries': 2, 'expected_effects': 1, 'expected_graph': 'completed', 'expected_tool_status': 'success'}
        case = write_case(True)
        self.assertTrue(assess_retry_case(case, expected)['contract_met'])
        [event for event in case['events'] if event['event'] == 'receiver_result'][-1]['receipt'] = {**case['entries'][0], 'receipt_id': 'invented'}
        self.assertFalse(assess_retry_case(case, expected)['contract_met'])

    def test_attempts_beyond_budget_and_changed_operation_fail(self) -> None:
        expected = {'expected_entries': 2, 'expected_effects': 2, 'expected_graph': 'completed', 'expected_tool_status': 'success'}
        case = write_case(); case['events'].append({'event': 'tool_enter', 'operation_id': 'op'})
        self.assertFalse(assess_retry_case(case, expected)['contract_met'])
        case = copy.deepcopy(write_case()); case['events'][3]['operation_id'] = 'different'
        self.assertFalse(assess_retry_case(case, expected)['contract_met'])

    def test_timeout_requires_late_commit_before_caller_error(self) -> None:
        expected = {'case': 'write-sync-step-timeout', 'expected_entries': 1, 'expected_effects': 1,
                    'expected_graph': 'TimeoutError', 'expected_tool_status': None}
        case = write_case(True)
        case.update(graph_outcome='TimeoutError', tool_status=None, tool_content=None, answer=None, model_observations=[])
        case['events'] = [case['events'][0], {**case['events'][1], 'at_s': 0},
                          {'event': 'gate_release', 'at_s': .2},
                          {**case['events'][2], 'at_s': .21}, {'event': 'graph_error', 'at_s': .22}]
        self.assertTrue(assess_retry_case(case, expected)['contract_met'])
        case['events'][3]['at_s'] = .01
        self.assertFalse(assess_retry_case(case, expected)['contract_met'])

    def test_invented_receipt_text_cannot_match_actual_committed_receipt(self) -> None:
        expected = {'expected_entries': 2, 'expected_effects': 1, 'expected_graph': 'completed', 'expected_tool_status': 'success'}
        case = write_case(True)
        case.update(tool_content='invented receipt', answer='invented receipt')
        case['model_observations'][0]['content'] = 'invented receipt'
        case['events'][-1]['content'] = 'invented receipt'
        self.assertFalse(assess_retry_case(case, expected)['contract_met'])

    def test_answer_cannot_differ_from_observed_tool_result(self) -> None:
        expected = {'expected_entries': 2, 'expected_effects': 2, 'expected_graph': 'completed', 'expected_tool_status': 'success'}
        case = write_case()
        case['answer'] = 'success without the actual receipt'
        self.assertFalse(assess_retry_case(case, expected)['contract_met'])
