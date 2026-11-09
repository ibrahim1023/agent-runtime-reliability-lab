"""Behavior of the lab's read-only review eligibility callback."""

import copy
from types import SimpleNamespace
import unittest

from reliability_lab.approval_budget import review_required


def request(count=0, *, calls=1):
    tool_calls = [{'name': 'record_action', 'args': {'message': 'note'}, 'id': f'call-{i}'} for i in range(calls)]
    return SimpleNamespace(state={'thread_tool_call_count': {'__all__': count},
                                 'messages': [SimpleNamespace(type='ai', tool_calls=tool_calls)]},
                           tool_call=tool_calls[0])


class ApprovalBudgetContracts(unittest.TestCase):
    def test_available_allowance_requires_review_without_spending_it(self):
        proposed = request()
        before = copy.deepcopy(proposed.state)
        self.assertTrue(review_required(proposed, thread_limit=1))
        self.assertEqual(proposed.state, before)

    def test_exhaustion_skips_only_review_and_does_not_change_counter(self):
        proposed = request(1)
        self.assertFalse(review_required(proposed, thread_limit=1))
        self.assertEqual(proposed.state['thread_tool_call_count'], {'__all__': 1})

    def test_initial_absent_counter_is_zero(self):
        proposed = request()
        proposed.state.pop('thread_tool_call_count')
        self.assertTrue(review_required(proposed, thread_limit=1))

    def test_bad_counters_limits_or_batches_fail_before_autoapproval(self):
        for count in (-1, True, '1'):
            with self.subTest(count=count), self.assertRaises(ValueError):
                review_required(request(count), thread_limit=1)
        for limit in (0, -1, True):
            with self.subTest(limit=limit), self.assertRaises(ValueError):
                review_required(request(), thread_limit=limit)
        with self.assertRaises(ValueError):
            review_required(request(calls=2), thread_limit=1)
