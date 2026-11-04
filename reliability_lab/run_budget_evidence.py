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
                    [message['tool_call_id'] for message in messages] == case['proposals'])
    tool_limit, model_limit = expected.get('tool_limit'), expected.get('model_limit')
    if tool_limit is not None and len(case['proposals']) > tool_limit:
        final_text = f"Tool call limit reached: run limit exceeded ({len(case['proposals'])}/{tool_limit} calls)."
        final_source = 'native_middleware'
    elif model_limit is not None and case['model_calls'] >= model_limit:
        final_text = f"Model call limits exceeded: run limit ({case['model_calls']}/{model_limit})"
        final_source = 'native_middleware'
    else:
        final_text = 'The read failed in all requested attempts.'
        final_source = 'scripted_model'
    final_matches = case['answer'] == final_text and case['final_answer_source'] == final_source
    contract = (case['model_calls'] == expected['expected_model_calls'] and
                len(case['proposals']) == expected['expected_proposals'] and
                len(set(case['proposals'])) == len(case['proposals']) and
                len(case['entries']) == expected['expected_tool_entries'] and
                len(grouped) == expected['expected_executed_requests'] and
                ids_match and per_call and errors_match and case['graph_completed'] and final_matches)
    return {'contract_met': contract, 'model_calls': case['model_calls'], 'proposed_tool_requests': len(case['proposals']),
            'executed_tool_requests': len(grouped), 'tool_body_entries': len(case['entries']),
            'attempts_by_request': dict(grouped), 'task_completed': False,
            'scope': 'All tool entries deliberately fail; graph completion is not read success'}


def verify_run_budget(root) -> dict:
    """Check recorded request/attempt traces without optional runtime imports."""
    from reliability_lab.evidence import require
    from reliability_lab.recent_evidence import load_section
    refs, data = load_section(root, 'run_budget_v1')
    plan, run, launch = data['plan'], data['execution'], data['launch']
    require(run['criteria_sha256'] == refs['plan']['sha256'] and run['fixture_contracts_met'] is True,
            'Run budget criteria identity')
    require(run['implementation_sha256']['run_budget.py'] == refs['driver_at_execution']['sha256'] and
            run['implementation_sha256']['run_budget_evidence.py'] == refs['assessor_at_execution']['sha256'], 'Run budget source identity')
    require(launch['exit_code'] == 0 and launch['timed_out'] is False and launch['duration_s'] <= 60 and
            run['live_model_calls'] == run['provider_tokens'] == 0 and len(run['cases']) == 4, 'Run budget execution bound')
    require(run['inspected_module_sha256'] == plan['inspected_module_sha256'], 'Run budget runtime identity')
    total = 0
    for case, expected in zip(run['cases'], plan['cases'], strict=True):
        require(case['case'] == expected['case'], 'Run budget roster')
        verdict = assess_budget_case(case, expected)
        require(verdict == case['verdicts'] and verdict['contract_met'], 'Run budget case contradiction')
        generation = [event for event in case['events'] if event['event'] == 'model_generation']
        errors = [event for event in case['events'] if event['event'] == 'tool_body_error']
        require([event['model_call'] for event in generation] == list(range(1, case['model_calls'] + 1)), 'Run budget model trace')
        require([call['id'] for event in generation for call in event['tool_calls']] == case['proposals'], 'Run budget proposal trace')
        require([event['tool_call_id'] for event in errors] == case['entries'] and
                all(event['error_type'] == 'OSError' for event in errors), 'Run budget attempt trace')
        messages = {message['tool_call_id']: message for message in case['tool_messages']}
        require(len(messages) == len(case['tool_messages']), 'Run budget duplicate tool result')
        for event in generation:
            require(all(message == messages.get(message['tool_call_id']) for message in event['observed_tool_messages']),
                    'Run budget model observation')
        if case['final_answer_source'] == 'scripted_model':
            require(generation[-1]['content'] == case['answer'] and generation[-1]['tool_calls'] == [], 'Run budget final model answer')
        else:
            require(bool(generation[-1]['tool_calls']), 'Run budget native termination source')
        total += len(case['entries'])
    require(total == 27 and total <= plan['budget']['max_tool_entries'], 'Run budget total attempts')
    return {'status': 'passed', 'kind': 'stored native run-limit evidence validation; no graphs executed',
            'graph_cases_checked': 4, 'body_entries_observed': total, 'new_graph_workers': 0,
            'task_completion': 'All controlled reads failed; limits stopped further work'}
