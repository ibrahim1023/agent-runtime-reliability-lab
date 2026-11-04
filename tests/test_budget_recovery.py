"""Budgeted pending work and genuinely new requests must remain distinct."""

import copy
import json
import unittest

from reliability_lab.budget_recovery_evidence import assess_recovery


def example(protected=True):
    receipt = {'operation_id': 'first', 'message': 'note', 'receipt_id': 'one', 'status': 'recorded'}
    second = receipt if protected else {**receipt, 'receipt_id': 'two'}
    effects = 1 if protected else 2
    phases = []
    for index, name in enumerate(['initial','restore','approve-first','resume','new-request','approve-next']):
        obs = {'thread_id':'thread', 'thread_count_before':0 if index<3 else 1,
               'thread_count_after':0 if index<2 else 1, 'interrupts':[], 'checkpoint_next':[]}
        if index in (0,1):obs['interrupts']=[{'id':'first-review','value':{'action':'first'}}]
        if index==4:obs['interrupts']=[{'id':'next-review','value':{'action':'next'}}]
        if index==3:obs.update(answer=json.dumps(second),final_tool_content=json.dumps(second),final_tool_call_id='first-call',final_tool_status='success')
        if index==5:obs.update(answer='Tool call limit reached: thread limit exceeded (2/1 calls).',answer_source='native_middleware',final_tool_call_id='next-call',final_tool_status='error')
        if index==2:obs={}
        phases.append({'phase':name,'pid':index+1,'exit_code':86 if index==2 else 0,'timeout':False,
                       'tool_entries':0 if index<2 else 1 if index==2 else 2,
                       'effects':0 if index<2 else 1 if index==2 else effects,'observation':obs})
    return {'protected':protected,'thread_id':'thread','first_operation_id':'first','next_operation_id':'next',
            'phases':phases,'entries':[receipt] if protected else [receipt,second],
            'tool_entries':[{'operation_id':'first','message':'note','thread_count':1}]*2,
            'receiver_results':[{'receipt':receipt,'reused':False},{'receipt':second,'reused':protected}]}


class BudgetRecoveryContracts(unittest.TestCase):
    def test_spent_budget_can_coexist_with_protected_replay(self) -> None:
        result=assess_recovery(example())
        self.assertTrue(result['contract_met'])
        self.assertTrue(result['first_action_completed_once'])
        self.assertTrue(result['new_action_blocked'])

    def test_unprotected_control_is_not_single_effect_success(self) -> None:
        result=assess_recovery(example(False))
        self.assertTrue(result['contract_met'])
        self.assertFalse(result['first_action_completed_once'])

    def test_reapproval_on_replay_or_new_action_entry_fails(self) -> None:
        data=example();data['phases'][3]['observation']['interrupts']=[{'id':'unexpected'}]
        self.assertFalse(assess_recovery(data)['contract_met'])
        data=copy.deepcopy(example());data['tool_entries'].append({'operation_id':'next','message':'next-note','thread_count':1})
        self.assertFalse(assess_recovery(data)['contract_met'])

    def test_valid_output_cannot_hide_a_failed_final_worker(self) -> None:
        data=example();data['phases'][-1]['exit_code']=1
        self.assertFalse(assess_recovery(data)['contract_met'])
