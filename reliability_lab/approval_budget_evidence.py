"""Closed-fixture checks keep review, budget and receiver outcomes separate."""

import json

from reliability_lab.crash_evidence import receipt_from_message


def _phases_match(case: dict, expected: dict) -> bool:
    phases, events = case['phases'], case['events']
    starts = [e for e in events if e['event'] == 'worker_start']
    return (case['case'] == expected['case'] and case['mode'] == expected['mode'] and
        [p['phase'] for p in phases] == expected['phases'] and
        [p['exit_code'] for p in phases] == expected['exits'] and
        [(p['phase'], p['pid']) for p in phases] == [(e['phase'], e['pid']) for e in starts] and
        len({p['pid'] for p in phases}) == len(phases) and
        all(not p['timeout'] and 0 <= p['duration_s'] <= 20 for p in phases) and
        [p['effects'] for p in phases] == expected['effects'] and
        [p['observation'].get('thread_count_after') for p in phases] == expected['counts'] and
        [bool(p['observation']['interrupts']) if p['observation'] else None for p in phases] == expected['reviews'])


def _effects_match(case: dict, expected: dict) -> bool:
    attempts, results, entries = case['tool_entries'], case['receiver_results'], case['entries']
    target = case['next_operation_id'] if 'reject-first' in expected['phases'] else case['first_operation_id']
    message = 'next-note' if 'reject-first' in expected['phases'] else expected.get('approved_message', 'note')
    return (case['first_operation_id'] != case['next_operation_id'] and len(entries) == 1 and
        len(attempts) == len(results) == expected['tool_entries'] and
        all(a['operation_id'] == target and a['message'] == message and a['thread_count'] == 1 for a in attempts) and
        entries[0]['operation_id'] == target and entries[0]['message'] == message and
        [r['receipt'] for r in results] == [entries[0]] * len(results) and
        [r['reused'] for r in results] == ([False, True] if expected.get('crash') else [False]) and
        all(case[key] == [e for e in case['events'] if e['event'] == event]
            for key, event in (('tool_entries', 'tool_enter'), ('receiver_results', 'receiver_result'))))


def _review_matches(case: dict, expected: dict) -> bool:
    phases = case['phases']
    first = phases[0]['observation']['interrupts']
    if 'restore' in expected['phases'] and first != phases[1]['observation']['interrupts']:
        return False
    decisions = [e for e in case['events'] if e['event'] == 'reviewer_decision']
    expected_decisions = [(p, 'reject' if p == 'reject-first' else 'edit' if p == 'edit-first' else 'approve')
                          for p in expected['phases'] if p in ('approve-first', 'approve-next', 'reject-first', 'edit-first')]
    if [(e['phase'], e['decision']['type']) for e in decisions] != expected_decisions:
        return False
    for row in phases:
        observation = row['observation']
        if not observation:
            continue
        expected_kind = ('new_user_message' if row['phase'] in ('initial', 'new-request') else
                         'simulated_decision' if row['phase'] in dict(expected_decisions) else 'resume_none')
        if observation['input_kind'] != expected_kind or observation['pid'] != row['pid']:
            return False
        if observation['interrupts']:
            note = 'next-note' if row['phase'] == 'new-request' else 'note'
            request = observation['interrupts'][0]['value']['action_requests']
            if len(request) != 1 or request[0]['name'] != 'record_action' or request[0]['args'] != {'message': note}:
                return False
    return bool(first) and all(e['source'] == 'simulated_reviewer' for e in decisions)


def _final_matches(case: dict, expected: dict) -> bool:
    final = case['phases'][-1]['observation']
    if expected['reviews'][-1]:
        return final['answer'] is None and bool(final['checkpoint_next'])
    if final['checkpoint_next'] or final['interrupts']:
        return False
    blocked = expected['phases'][-1] == 'new-request'
    if blocked:
        return (final['final_tool_call_id'] == 'next-call' and final['final_tool_status'] == 'error' and
                final['answer_source'] == 'native_middleware' and
                final['answer'] == 'Tool call limit reached: thread limit exceeded (2/1 calls).' and
                final['final_tool_content'] == 'Tool call limit exceeded. Do not make additional tool calls.')
    record = {'decision': 'edit' if expected['phases'][-1] == 'edit-first' else 'approve',
              'approved_message': expected.get('approved_message', 'note'),
              'final_tool_content': final['final_tool_content']}
    return (final['final_tool_status'] == 'success' and final['answer_source'] == 'scripted_model' and
            final['answer'] == final['final_tool_content'] and receipt_from_message(record) == case['entries'][0])


def assess_approval_case(case: dict, expected: dict) -> dict:
    """Evaluate phase evidence without accepting a stored success verdict."""
    try:
        checks = {'phases': _phases_match(case, expected), 'effects': _effects_match(case, expected),
                  'review': _review_matches(case, expected), 'final': _final_matches(case, expected)}
    except (KeyError, ValueError, TypeError, IndexError):
        return {'contract_met': False, 'classification': 'incomplete or contradictory observations'}
    return {'contract_met': all(checks.values()), 'checks': checks,
            'tool_entries': len(case['tool_entries']), 'committed_effects': len(case['entries']),
            'final_review_pending': bool(case['phases'][-1]['observation'].get('interrupts'))}
