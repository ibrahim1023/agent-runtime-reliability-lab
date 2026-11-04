"""Validate the saved diagnostic-failure replay without executing the orchestration."""

import json
from pathlib import Path

from reliability_lab.evidence import require
from reliability_lab.recent_evidence import load_section
from reliability_lab.outcome_reporting import outcome_report


def verify_diagnostics(root: Path) -> dict:
    """Keep original exceptions, corrected reports and unavailable hashes explicit."""
    references, data = load_section(root, 'receiver_diagnostics_v1')
    plan, baseline, corrected = data['plan'], data['baseline'], data['corrected']
    source = data['source_execution']['graph_execution']['cases'][0]
    for phase, run in (('baseline', baseline), ('corrected', corrected)):
        require(run['phase'] == phase and run['criteria_sha256'] == references['plan']['sha256'], 'Diagnostic criteria')
        require(run['implementation_sha256'] == references[phase + '_implementation']['sha256'], 'Diagnostic implementation identity')
        require(run['new_graph_workers'] == run['live_model_calls'] == run['provider_tokens'] == 0, 'Diagnostic replay relabelled')
        require([row['condition'] for row in run['conditions']] == plan['conditions'], 'Diagnostic replay roster')
        for row in run['conditions']:
            require(row['new_graph_workers'] == 0 and row['reused_source_worker_count'] == 19 and
                    row['original_model_answer'] == source['answer'], 'Diagnostic source context')
    require([row.get('exception_type') for row in baseline['conditions']] == [None, 'FileNotFoundError', 'PermissionError'], 'Baseline diagnostic failures')
    require([row['returned_report'] for row in baseline['conditions']] == [True, False, False] and
            [row['report_saved'] for row in baseline['conditions']] == [True, False, False], 'Baseline reporting outcome')
    for index, row in enumerate(corrected['conditions']):
        require(row['returned_report'] is True and row['report_saved'] is True, 'Corrected report missing')
        delivery = row['first_delivery']; response = delivery['response']
        require(response['model_answer'] == source['answer'] and response['delivery_source'] == 'receiver_reconciliation', 'Corrected delivery source')
        expected = 'outcome_unknown' if index == 1 else 'completed_once'
        result = response['reconciliation']
        require(result['outcome'] == expected and result['operation_id'] == source['operation_id'], 'Corrected reconciliation')
        require(result['task_completed'] is (None if index == 1 else True) and
                result['observed_effects'] == (None if index == 1 else 1), 'Corrected task conclusion')
        required = outcome_report(expected, source['operation_id'], None if index == 1 else 1, True)
        require(result == required, 'Corrected receiver report')
        text = required['report']
        if index != 1:
            text += f" Recorded contents: {json.dumps(source['approved_message'])}."
        require(response['user_response'] == text, 'Corrected final response')
        require(row['receiver_exists_after'] is (index != 1), 'Replay created missing receiver')
        require(row['fixture_contracts_met'] is (index == 0) and row['exit_code'] == (0 if index == 0 else 1), 'Faulted fixture relabelled')
        if index:
            require(delivery['receiver_sha256_before'] is None and delivery['receiver_sha256_after'] is None and
                    delivery['receiver_bytes_unchanged'] is None, 'Unavailable diagnostic evidence claimed as unchanged')
            error = 'FileNotFoundError' if index == 1 else 'PermissionError'
            diagnostic = {'sha256': None, 'error_type': error}
            require(delivery['receiver_diagnostics'] == {'before': diagnostic, 'after': diagnostic}, 'Diagnostic failure metadata')
        else:
            require(delivery['receiver_sha256_before'] == delivery['receiver_sha256_after'] and
                    isinstance(delivery['receiver_sha256_before'], str) and delivery['receiver_bytes_unchanged'] is True, 'Available diagnostic evidence')
    return {'status': 'passed', 'kind': 'stored application-replay evidence validation; no graph or replay executed',
            'saved_replay_conditions_checked': 6, 'new_graph_workers': 0,
            'faulted_fixture_contracts_remain_unmet': True}
