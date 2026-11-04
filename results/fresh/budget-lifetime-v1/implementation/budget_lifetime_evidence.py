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
