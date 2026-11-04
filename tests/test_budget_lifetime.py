"""A persisted conversation counter and a new invocation allowance differ."""

import unittest

from reliability_lab.budget_lifetime_evidence import assess_lifetime, successful_launches


class BudgetLifetimeContracts(unittest.TestCase):
    def example(self):
        phases = []
        for index in range(2):
            call = f'phase-{index}-call-1'
            blocked = f'phase-{index}-call-2'
            phases.append({'pid': index+1, 'thread_id': 'thread', 'input_kind': 'new_user_message',
                'model_calls': 2, 'proposals': [call, blocked], 'entries': [call]*3,
                'tool_messages': [{'tool_call_id': call, 'status': 'error'}, {'tool_call_id': blocked, 'status': 'error'}],
                'checkpoint_thread_before': index, 'checkpoint_thread_after': index+1,
                'run_counter_checkpointed_before': False, 'run_counter_checkpointed_after': False,
                'checkpoint_next': [], 'graph_completed': True})
        return {'thread_id': 'thread', 'phases': phases}

    def expected(self):
        return {'expected_entries': [3,3], 'expected_model_calls': [2,2], 'expected_checkpoint_thread_counts': [1,2]}

    def test_run_allowance_can_reset_while_thread_count_persists(self) -> None:
        self.assertTrue(assess_lifetime(self.example(), self.expected())['contract_met'])

    def test_a_new_thread_is_not_evidence_for_same_conversation(self) -> None:
        data = self.example(); data['phases'][1]['thread_id'] = 'different'
        self.assertFalse(assess_lifetime(data, self.expected())['contract_met'])

    def test_missing_checkpoint_counter_or_same_process_fails(self) -> None:
        data = self.example(); data['phases'][1]['checkpoint_thread_before'] = 0
        self.assertFalse(assess_lifetime(data, self.expected())['contract_met'])
        data = self.example(); data['phases'][1]['pid'] = data['phases'][0]['pid']
        self.assertFalse(assess_lifetime(data, self.expected())['contract_met'])

    def test_written_output_cannot_override_failed_worker_exit(self) -> None:
        launches = [{'exit_code': 0, 'timed_out': False}, {'exit_code': 1, 'timed_out': False}]
        self.assertFalse(successful_launches(launches, 2))
        launches[1] = {'exit_code': 0, 'timed_out': True}
        self.assertFalse(successful_launches(launches, 2))
        launches[1] = {'exit_code': 0, 'timed_out': False}
        self.assertTrue(successful_launches(launches, 2))
        self.assertFalse(successful_launches(launches[:1], 2))
