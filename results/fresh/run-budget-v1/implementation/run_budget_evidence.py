"""Checks for logical requests versus native retry body entries."""

from collections import Counter


def assess_budget_case(case: dict, expected: dict) -> dict:
    """Use request IDs to distinguish retries from newly proposed calls."""
    grouped = Counter(case['entries'])
    messages = case['tool_messages']
    ids_match = set(grouped) <= set(case['proposals'])
    per_call = all(count == 3 for count in grouped.values())
    errors_match = (case['body_errors'] == len(case['entries']) and
                    all(message['status'] == 'error' for message in messages) and
                    all(any(message['tool_call_id'] == call for message in messages) for call in grouped))
    contract = (case['model_calls'] == expected['expected_model_calls'] and
                len(case['proposals']) == expected['expected_proposals'] and
                len(set(case['proposals'])) == len(case['proposals']) and
                len(case['entries']) == expected['expected_tool_entries'] and
                len(grouped) == expected['expected_executed_requests'] and
                ids_match and per_call and errors_match and case['graph_completed'] and bool(case['answer']))
    return {'contract_met': contract, 'model_calls': case['model_calls'], 'proposed_tool_requests': len(case['proposals']),
            'executed_tool_requests': len(grouped), 'tool_body_entries': len(case['entries']),
            'attempts_by_request': dict(grouped), 'task_completed': False,
            'scope': 'All tool entries deliberately fail; graph completion is not read success'}
