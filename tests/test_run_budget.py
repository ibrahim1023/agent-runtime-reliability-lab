"""Logical call caps and body-attempt caps are different observable limits."""

import unittest

from reliability_lab.run_budget_evidence import assess_budget_case


class RunBudgetContracts(unittest.TestCase):
    def example(self):
        return {'model_calls': 2, 'proposals': ['one', 'two'], 'entries': ['one'] * 3,
                'body_errors': 3, 'graph_completed': True, 'duration_s': .1,
                'tool_messages': [{'tool_call_id': 'one', 'status': 'error', 'content': 'read failed'},
                                  {'tool_call_id': 'two', 'status': 'error', 'content': 'blocked'}],
                'answer': 'Tool call limit reached: run limit exceeded (2/1 calls).',
                'final_answer_source': 'native_middleware'}

    def expected(self):
        return {'tool_limit': 1, 'model_limit': None, 'expected_model_calls': 2, 'expected_proposals': 2,
                'expected_tool_entries': 3, 'expected_executed_requests': 1}

    def test_one_logical_call_can_have_three_body_entries(self) -> None:
        result = assess_budget_case(self.example(), self.expected())
        self.assertTrue(result['contract_met'])
        self.assertEqual(result['executed_tool_requests'], 1)
        self.assertFalse(result['task_completed'])

    def test_extra_body_attempt_or_unproposed_id_fails(self) -> None:
        data = self.example(); data['entries'].append('one'); data['body_errors'] += 1
        self.assertFalse(assess_budget_case(data, self.expected())['contract_met'])
        data = self.example(); data['entries'][0] = 'unproposed'
        self.assertFalse(assess_budget_case(data, self.expected())['contract_met'])

    def test_failed_tool_messages_cannot_be_relabelled_success(self) -> None:
        data = self.example(); data['tool_messages'][0]['status'] = 'success'
        self.assertFalse(assess_budget_case(data, self.expected())['contract_met'])

    def test_blocked_request_must_have_its_own_error_message(self) -> None:
        data = self.example(); data['tool_messages'].pop()
        self.assertFalse(assess_budget_case(data, self.expected())['contract_met'])

    def test_limit_stop_cannot_be_relabelled_as_model_success(self) -> None:
        data = self.example(); data.update(answer='The read succeeded.', final_answer_source='scripted_model')
        self.assertFalse(assess_budget_case(data, self.expected())['contract_met'])
