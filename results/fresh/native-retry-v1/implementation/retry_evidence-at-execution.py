"""Assess native retry/timeout observations without importing optional dependencies."""


def assess_retry_case(case: dict, expected: dict) -> dict:
    """Separate graph completion, attempt count, receiver effects and fixture expectations."""
    attempts = [event for event in case['events'] if event['event'] == 'tool_enter']
    receipts = [event for event in case['events'] if event['event'] == 'receiver_result']
    proposals = [event for event in case['events'] if event['event'] == 'model_proposal']
    identity = all(item['operation_id'] == case['operation_id'] for item in attempts + case['entries'])
    identity = identity and all(item['message'] == 'note' for item in case['entries'])
    receipt_match = [event['receipt'] for event in receipts] == case['entries']
    if case['protected'] and len(receipts) == 2:
        receipt_match = (len(case['entries']) == 1 and receipts[0]['receipt'] == receipts[1]['receipt'] == case['entries'][0]
                         and receipts[0]['reused'] is False and receipts[1]['reused'] is True)
    observations = case['model_observations']
    observation_match = (len(observations) == 1 and observations[0]['status'] == case['tool_status']) if case['graph_outcome'] == 'completed' else not observations
    timeout_order = True
    if expected.get('case') == 'write-sync-step-timeout':
        names = [event['event'] for event in case['events']]
        required = ('tool_enter', 'gate_release', 'receiver_result', 'graph_error')
        timeout_order = all(name in names for name in required)
        if timeout_order:
            times = [next(e['at_s'] for e in case['events'] if e['event'] == name) for name in required]
            timeout_order = times == sorted(times) and times[2] - times[0] >= .05
    contract = (len(attempts) == expected['expected_entries'] and len(case['entries']) == expected['expected_effects'] and
                case['graph_outcome'] == expected['expected_graph'] and case['tool_status'] == expected['expected_tool_status'] and
                identity and receipt_match and observation_match and len(proposals) == 1 and
                case['case_duration_s'] <= 10 and case['controller_joined'] and timeout_order)
    return {'contract_met': contract, 'tool_entries': len(attempts), 'committed_effects': len(case['entries']),
            'graph_completed': case['graph_outcome'] == 'completed', 'single_effect_observed': len(case['entries']) == 1,
            'single_effect_task_completed': case['graph_outcome'] == 'completed' and len(case['entries']) == 1 and identity,
            'checks': {'stable_identity': identity, 'receipt_consistency': receipt_match,
                       'model_observation_consistent': observation_match, 'timeout_event_order': timeout_order}}
