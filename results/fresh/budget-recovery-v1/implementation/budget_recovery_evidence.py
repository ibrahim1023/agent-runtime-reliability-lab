"""Check native budget/approval recovery through receipts, counters and launches."""

import json


def assess_recovery(case: dict) -> dict:
    """Keep logical budget enforcement separate from physical receiver effects."""
    phases=case['phases']
    if len(phases)!=6:
        return {'contract_met':False,'interruption':'incomplete phase sequence'}
    observations=[p['observation'] for p in phases]
    entries=case['entries']; attempts=case['tool_entries']; receipts=case['receiver_results']
    expected_effects=1 if case['protected'] else 2
    launches=([p['phase'] for p in phases]==['initial','restore','approve-first','resume','new-request','approve-next'] and
              [p['exit_code'] for p in phases]==[0,0,86,0,0,0] and len({p['pid'] for p in phases})==6 and
              all(not p['timeout'] for p in phases))
    review=(bool(observations[0].get('interrupts')) and observations[0]['interrupts']==observations[1].get('interrupts') and
            not observations[3].get('interrupts') and observations[3].get('checkpoint_next')==[] and
            bool(observations[4].get('interrupts')) and not observations[5].get('interrupts') and observations[5].get('checkpoint_next')==[])
    identity=(case['first_operation_id']!=case['next_operation_id'] and
              all(p.get('thread_id')==case['thread_id'] for p in observations if p) and
              all(item['operation_id']==case['first_operation_id'] and item['message']=='note' for item in attempts+entries))
    budgets=(all(p['thread_count_after']==0 for p in observations[:2]) and
             all(p['thread_count_before']==p['thread_count_after']==1 for p in observations[3:]) and
             all(item['thread_count']==1 for item in attempts))
    counts=([p['tool_entries'] for p in phases]==[0,0,1,2,2,2] and
            [p['effects'] for p in phases]==[0,0,1,expected_effects,expected_effects,expected_effects] and
            len(attempts)==2 and len(entries)==expected_effects)
    if case['protected']:
        reuse=(len(receipts)==2 and len(entries)==1 and receipts[0]['receipt']==receipts[1]['receipt']==entries[0] and
               receipts[0]['reused'] is False and receipts[1]['reused'] is True)
    else:
        reuse=([r['receipt'] for r in receipts]==entries and len(receipts)==2 and
               all(r['reused'] is False for r in receipts) and receipts[0]['receipt']['receipt_id']!=receipts[1]['receipt']['receipt_id'])
    try:
        replay_answer=(json.loads(observations[3]['answer'])==entries[-1] and
                       observations[3]['answer']==observations[3]['final_tool_content'] and observations[3]['final_tool_status']=='success')
    except (ValueError,KeyError,TypeError,IndexError):
        replay_answer=False
    last=observations[-1]
    blocked=(last.get('final_tool_call_id')=='next-call' and last.get('final_tool_status')=='error' and
             last.get('answer')=='Tool call limit reached: thread limit exceeded (2/1 calls).' and
             last.get('answer_source')=='native_middleware' and not any(e['operation_id']==case['next_operation_id'] for e in entries+attempts))
    contract=all((launches,review,identity,budgets,counts,reuse,replay_answer,blocked))
    return {'contract_met':contract,'pending_tool_replayed':len(attempts)==2,
            'first_action_completed_once':contract and len(entries)==1,'new_action_blocked':blocked,
            'tool_body_entries':len(attempts),'committed_effects':len(entries),
            'checks':{'launches':launches,'review_flow':review,'stable_identity':identity,'budget_counter':budgets,
                      'phase_counts':counts,'receipt_replay':reuse,'replay_answer':replay_answer}}
