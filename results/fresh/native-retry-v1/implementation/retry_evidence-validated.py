"""Assess native retry/timeout observations without importing optional dependencies."""


import json


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
    observed_events = [{'status': event['status'], 'content': event['content']} for event in case['events']
                       if event['event'] == 'model_observed_tool']
    if case['graph_outcome'] == 'completed':
        observation_match = (observations == observed_events == [{'status': case['tool_status'], 'content': case['tool_content']}]
                             and case['answer'] == case['tool_content'])
        if case['entries'] and case['tool_status'] == 'success':
            try:
                observation_match = observation_match and json.loads(case['tool_content']) == case['entries'][-1]
            except (ValueError, TypeError):
                observation_match = False
    else:
        observation_match = not observations and not observed_events and case['tool_content'] is case['answer'] is None
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


def verify_native_retry(root) -> dict:
    """Check preserved partial/continuation evidence without importing the runtime."""
    from reliability_lab.evidence import require
    from reliability_lab.recent_evidence import load_section
    references, data = load_section(root, 'native_retry_v1')
    plan, setup, partial, continuation, coverage = (data[key] for key in
        ('plan', 'setup_interruption', 'partial_attempt', 'continuation', 'coverage'))
    require(setup['cases'] == [] and setup['fixture_contracts_met'] is False and
            setup['interruption_type'] == 'ModuleNotFoundError', 'Native setup interruption missing')
    require(coverage['single_uninterrupted_successful_attempt'] is False and
            coverage['setup_or_fixture_interruptions'] == 2 and coverage['worker_processes_including_interruptions'] == 3,
            'Native attempt accounting contradicts amendments')
    require(len(partial['cases']) == 5 and coverage['cases'] == partial['cases'] + [continuation['case']],
            'Native coverage differs from retained attempts')
    require(coverage['criteria_sha256'] == partial['criteria_sha256'] == setup['criteria_sha256'] == references['plan']['sha256'],
            'Native frozen criteria identity')
    require(setup['implementation_sha256']['native_retry.py'] == references['original_implementation']['sha256'] and
            setup['implementation_sha256']['retry_evidence.py'] == references['assessor_at_execution']['sha256'],
            'Native original execution source identity')
    require(continuation['implementation_sha256'] == references['corrected_implementation']['sha256'] and
            data['timeout_amendment']['original_implementation_sha256'] == references['original_implementation']['sha256'],
            'Native source identity')
    require(coverage['fresh_graph_invocations'] == len(coverage['cases']) == len(plan['cases']) == 6 and
            coverage['live_model_calls'] == coverage['provider_tokens'] == 0 and coverage['coverage_complete'] is True,
            'Native coverage bounds')
    require(coverage['inspected_module_sha256'] == partial['inspected_module_sha256'] == plan['inspected_module_sha256'],
            'Native inspected runtime identity')
    require([launch['exit_code'] for launch in coverage['launch_observations']] == [1, 1, 0] and
            all(not launch['timed_out'] for launch in coverage['launch_observations']) and
            sum(launch['duration_s'] for launch in coverage['launch_observations']) <= 90, 'Native launch outcomes')
    total = 0
    for case, expected in zip(coverage['cases'], plan['cases'], strict=True):
        require(case['case'] == expected['case'], 'Native case roster')
        verdict = assess_retry_case(case, expected)
        require(verdict == case['verdicts'] and verdict['contract_met'], 'Native saved case contradiction')
        attempts = [event for event in case['events'] if event['event'] == 'tool_enter']
        require([event['attempt'] for event in attempts] == list(range(1, len(attempts) + 1)), 'Native attempt sequence')
        require(not any(event['event'] == 'release_guard_failed' for event in case['events']), 'Native gate guard failed')
        if case['case'] == 'read-transient':
            require(case['tool_content'] == 'north\nsouth', 'Native successful read contents')
        total += verdict['tool_entries']
    require(total == coverage['actual_tool_entries'] == 11 and total <= plan['budget']['max_tool_entries'], 'Native tool budget')
    return {'status': 'passed', 'kind': 'stored native retry/timeout evidence validation; no graph or provider calls',
            'graph_cases_checked': 6, 'tool_entries_observed': total, 'new_graph_workers': 0,
            'single_uninterrupted_attempt': False, 'preserved_attempt_interruptions': 2}
