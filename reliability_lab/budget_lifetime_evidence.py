"""Validate budget scope across completed turns and fresh worker processes."""

from collections import Counter


def assess_lifetime(case: dict, expected: dict) -> dict:
    """Check preserved thread identity, checkpoint counters and actual retry entries."""
    phases = case['phases']; counts = []
    valid = len(phases) == 2 and len({p['pid'] for p in phases}) == 2
    previous = 0
    for index, phase in enumerate(phases):
        entries = phase['entries']; proposals = phase['proposals']; grouped = Counter(entries)
        valid = valid and (phase['thread_id'] == case['thread_id'] and phase['input_kind'] == 'new_user_message' and
                phase['checkpoint_thread_before'] == previous and
                phase['checkpoint_thread_after'] == expected['expected_checkpoint_thread_counts'][index] and
                phase['run_counter_checkpointed_before'] is False and phase['run_counter_checkpointed_after'] is False and
                len(entries) == expected['expected_entries'][index] and phase['model_calls'] == expected['expected_model_calls'][index] and
                len(proposals) == phase['model_calls'] and len(set(proposals)) == len(proposals) and
                set(grouped) <= set(proposals) and all(n == 3 for n in grouped.values()) and
                [m['tool_call_id'] for m in phase['tool_messages']] == proposals and
                all(m['status'] == 'error' for m in phase['tool_messages']) and
                phase['graph_completed'] and phase['checkpoint_next'] == [])
        previous = phase['checkpoint_thread_after']; counts.append(len(entries))
    return {'contract_met': valid, 'tool_entries_by_turn': counts,
            'same_thread': all(p['thread_id'] == case['thread_id'] for p in phases),
            'fresh_process_per_turn': len({p['pid'] for p in phases}) == 2,
            'task_completed': False, 'scope': 'new user turns after clean process restart, not pending-work crash resume'}


def successful_launches(launches: list[dict], expected_count: int) -> bool:
    """Require every expected worker to exit successfully, even when output exists."""
    return len(launches) == expected_count and all(
        launch['exit_code'] == 0 and launch['timed_out'] is False for launch in launches)


def verify_lifetime(root) -> dict:
    """Validate saved new-turn evidence without reading private checkpoint databases."""
    from reliability_lab.evidence import require
    from reliability_lab.recent_evidence import load_section
    refs, data = load_section(root, 'budget_lifetime_v1')
    plan, run, launch = data['plan'], data['execution'], data['launch']
    require(run['criteria_sha256'] == refs['plan']['sha256'] and run['fixture_contracts_met'] is True, 'Lifetime criteria')
    require(successful_launches(run['launches'], 4) and launch['exit_code'] == 0 and not launch['timed_out'] and
            launch['duration_s'] <= 60 and all(p['duration_s'] <= 10 for p in run['launches']), 'Lifetime worker launch failure')
    require(run['live_model_calls'] == run['provider_tokens'] == 0 and len(run['cases']) == 2, 'Lifetime execution bound')
    for name, key in (('budget_lifetime.py', 'driver_at_execution'), ('budget_lifetime_worker.py', 'worker_at_execution'),
                      ('budget_lifetime_evidence.py', 'assessor_at_execution')):
        require(run['implementation_sha256'][name] == refs[key]['sha256'], 'Lifetime execution source')
    total, pids, threads = 0, [], []
    for case, expected in zip(run['cases'], plan['conditions'], strict=True):
        require(case['case'] == expected['case'] and len(case['phases']) == 2, 'Lifetime case roster')
        require(assess_lifetime(case, expected) == case['verdicts'] and case['verdicts']['contract_met'], 'Lifetime saved verdict')
        require([p['phase'] for p in case['phases']] == plan['phases'], 'Lifetime phase order')
        previous_tools, seen_proposals = [], set()
        for phase in case['phases']:
            pids.append(phase['pid']); threads.append(phase['thread_id'])
            require(phase['inspected_module_sha256'] == plan['inspected_module_sha256'], 'Lifetime native module identity')
            require(not seen_proposals.intersection(phase['proposals']), 'Lifetime reused proposal identity')
            seen_proposals.update(phase['proposals'])
            generations = [event for event in phase['events'] if event['event'] == 'model_generation']
            errors = [event for event in phase['events'] if event['event'] == 'tool_body_error']
            require([g['model_call'] for g in generations] == list(range(1, phase['model_calls'] + 1)) and
                    [call['id'] for g in generations for call in g['tool_calls']] == phase['proposals'], 'Lifetime model trace')
            require([e['tool_call_id'] for e in errors] == phase['entries'] and
                    all(e['error_type'] == 'OSError' for e in errors), 'Lifetime actual tool entries')
            require(phase['all_tool_messages'] == previous_tools + phase['tool_messages'] and
                    generations[0]['observed_tool_messages'] == previous_tools, 'Lifetime checkpoint message history')
            by_id = {m['tool_call_id']: m for m in phase['all_tool_messages']}
            require(len(by_id) == len(phase['all_tool_messages']), 'Lifetime duplicate tool response')
            require(all(m == by_id.get(m['tool_call_id']) for g in generations for m in g['observed_tool_messages']), 'Lifetime model observation')
            exceeded = []
            if expected['thread_limit'] is not None and phase['checkpoint_thread_after'] + 1 > expected['thread_limit']:
                exceeded.append(f"thread limit exceeded ({phase['checkpoint_thread_after'] + 1}/{expected['thread_limit']} calls)")
            if len(phase['proposals']) > expected['run_limit']:
                exceeded.append(f"run limit exceeded ({len(phase['proposals'])}/{expected['run_limit']} calls)")
            require(bool(exceeded) and phase['answer_source'] == 'native_middleware' and
                    phase['answer'] == 'Tool call limit reached: ' + ' and '.join(exceeded) + '.', 'Lifetime final limit answer')
            previous_tools = phase['all_tool_messages']; total += len(phase['entries'])
        require(case['thread_id'] == threads[-1], 'Lifetime application thread')
    require(len(set(pids)) == 4 and len(set(threads)) == 2 and total == 9, 'Lifetime process/thread accounting')
    require([(p['case'], p['phase']) for p in run['launches']] == [(c['case'], p) for c in plan['conditions'] for p in plan['phases']], 'Lifetime launch order')
    return {'status': 'passed', 'kind': 'stored budget-lifetime evidence validation; no worker restart or graph execution',
            'worker_invocations_checked': 4, 'actual_tool_entries_observed': total, 'new_workers': 0,
            'scope': 'completed new user turns across clean restarts on persistent thread IDs'}
