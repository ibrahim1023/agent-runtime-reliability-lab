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


def verify_budget_recovery(root) -> dict:
    """Bind saved recovery results to native phase inputs, approvals and counter evidence."""
    from reliability_lab.evidence import require
    from reliability_lab.recent_evidence import load_section
    refs,data=load_section(root,'budget_recovery_v1')
    plan,run,launch=data['plan'],data['execution'],data['launch']
    require(run['criteria_sha256']==refs['plan']['sha256'] and run['fixture_contracts_met'] is True,'Recovery criteria')
    require(launch['exit_code']==0 and launch['timed_out'] is False and launch['duration_s']<=120 and
            run['worker_processes']==12 and run['live_model_calls']==run['provider_tokens']==0 and len(run['cases'])==2,'Recovery execution budget')
    for name,key in [('budget_recovery.py','driver_at_execution'),('budget_recovery_worker.py','worker_at_execution'),
                     ('budget_recovery_evidence.py','assessor_at_execution'),('receiver.py','receiver_at_execution')]:
        require(run['implementation_sha256'][name]==refs[key]['sha256'],'Recovery source identity')
    pids=[];threads=[];total=0
    for case,expected in zip(run['cases'],plan['conditions'],strict=True):
        require(case['case']==expected['case'] and case['protected'] is expected['protected'],'Recovery condition roster')
        require(assess_recovery(case)==case['verdicts'] and case['verdicts']['contract_met'],'Recovery saved verdict')
        phases,events=case['phases'],case['events'];threads.append(case['thread_id'])
        starts=[e for e in events if e['event']=='worker_start']
        require([(p['phase'],p['pid']) for p in phases]==[(e['phase'],e['pid']) for e in starts],'Recovery worker journal')
        preflights=[e for e in events if e['event']=='worker_preflight']
        require([e['phase'] for e in preflights]==plan['phases'] and
                all(e['inspected_module_sha256']==plan['inspected_module_sha256'] for e in preflights),'Recovery runtime preflight')
        reviews=[e for e in events if e['event']=='reviewer_decision']
        require([e['phase'] for e in reviews]==['approve-first','approve-next'] and
                all(e['decision']=='approve' and e['source']=='simulated_reviewer' for e in reviews),'Recovery review decisions')
        checkpoints=[e for e in events if e['event']=='checkpoint_before']
        require([e['phase'] for e in checkpoints]==plan['phases'] and
                [e['thread_count'] for e in checkpoints]==[0,0,0,1,1,1],'Recovery checkpoint counter')
        proposals=[e for e in events if e['event']=='model_proposal']
        require([(e['phase'],e['tool_call_id'],e['args'],e['operation_id']) for e in proposals]==[
            ('initial','first-call',{'message':'note'},case['first_operation_id']),
            ('new-request','next-call',{'message':'next-note'},case['next_operation_id'])],'Recovery new versus pending request')
        for key,event in [('tool_entries','tool_enter'),('receiver_results','receiver_result')]:
            require(case[key]==[e for e in events if e['event']==event],'Recovery receiver journal')
        require([e['phase'] for e in case['tool_entries']]==['approve-first','resume'],'Recovery replay phase')
        for index,phase in enumerate(phases):
            pids.append(phase['pid']);obs=phase['observation']
            require(phase['duration_s']<=10 and starts[index]['thread_id']==case['thread_id'],'Recovery phase bounds')
            operation=case['next_operation_id'] if index>=4 else case['first_operation_id']
            require(starts[index]['operation_id']==operation,'Recovery operation configuration')
            if index==2:
                require(obs=={},'Recovery crash returned unexpected result')
                continue
            kind=['new_user_message','resume_none','simulated_approval','resume_none','new_user_message','simulated_approval'][index]
            require(obs['input_kind']==kind and obs['operation_id']==operation and obs['pid']==phase['pid'],'Recovery phase input')
            tools=obs['tool_messages']
            if tools:
                require(all(obs[key]==tools[-1][tool_key] for key,tool_key in
                    [('final_tool_call_id','tool_call_id'),('final_tool_status','status'),('final_tool_content','content')]),'Recovery raw tool result')
        for index,message in [(0,'note'),(4,'next-note')]:
            requests=phases[index]['observation']['interrupts'][0]['value']['action_requests']
            require(len(requests)==1 and requests[0]['name']=='record_action' and requests[0]['args']=={'message':message},'Recovery approval request')
        observed=[e for e in events if e['event']=='model_observed_tool']
        resumed=phases[3]['observation']
        require(len(observed)==1 and observed[0]['phase']=='resume' and observed[0]['tool_call_id']=='first-call' and
                observed[0]['status']==resumed['final_tool_status'] and observed[0]['content']==resumed['final_tool_content'],'Recovery model receipt observation')
        require(phases[-1]['observation']['final_tool_content']=='Tool call limit exceeded. Do not make additional tool calls.','Recovery raw budget-block message')
        total+=len(case['tool_entries'])
    require(len(set(pids))==12 and len(set(threads))==2 and total==4,'Recovery process accounting')
    return {'status':'passed','kind':'stored budget/crash evidence validation; no new workers or graphs',
            'worker_phases_checked':12,'tool_entries_observed':total,'new_workers':0,
            'first_action_effects':[1,2],'new_action_effects':[0,0]}
