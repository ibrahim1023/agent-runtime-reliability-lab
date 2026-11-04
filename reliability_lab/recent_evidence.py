"""Validate recent saved evidence without graph execution or dependency imports."""

import json
from pathlib import Path

from reliability_lab.crash_evidence import assess_case
from reliability_lab.evidence import checked_bytes, require
from reliability_lab.outcome_reporting import matching_receipts, outcome_report


def load_section(root: Path, name: str) -> tuple[dict, dict]:
    """Check every linked file before interpreting a section's JSON artifacts."""
    manifest = json.loads((root / 'results/manifest.json').read_text())
    references = manifest[name]
    data = {}
    for key, reference in references.items():
        if isinstance(reference, dict):
            raw = checked_bytes(root, reference['export'], reference['sha256'])
            data[key] = json.loads(raw) if reference['export'].endswith('.json') else raw.decode()
    return references, data


def validate_saved_run(run: dict, plan: dict) -> None:
    """Bind stored verdicts to the declared cases, phase journals and final observation."""
    require(run['status'] == 'passed' and run['live_model_calls'] == 0 and
            run['worker_processes'] == 19 and len(run['cases']) == 5 and run['duration_s'] <= 600,
            'Saved runtime bounds or status')
    for case, expected in zip(run['cases'], plan['cases'], strict=True):
        require(all(case[key] == expected[key] for key in ('case', 'decision', 'protected')), 'Saved case roster')
        require(case['approved_message'] == expected.get('approved_message', 'record-once'), 'Saved approved contents')
        require(assess_case(case) == case['verdicts'] and case['verdicts']['contract_met'], 'Saved case verdict')
        phases = case['phases']
        require(len(phases) == expected['phases'] and all(not p['timeout'] and p['duration_s'] <= 30 for p in phases), 'Saved phase bound')
        starts = [e for e in case['events'] if e['event'] == 'worker_start']
        require([(p['phase'], p['pid']) for p in phases] == [(e['phase'], e['pid']) for e in starts], 'Saved worker journal')
        for key, event in (('tool_entries', 'tool_enter'), ('receiver_results', 'receiver_result')):
            require(case[key] == [e for e in case['events'] if e['event'] == event], 'Saved tool journal')
        final = phases[-1]['observation']
        require(case['graph_completed'] == (bool(final) and final.get('checkpoint_next') == [] and not final.get('interrupts')), 'Saved checkpoint completion')
        initial, restored = (p['observation'].get('interrupts') for p in phases[:2])
        require(bool(initial) and initial == restored and case['same_pending_review'] is True, 'Saved pending review')
        require(all(case[key] == phases[-1]['observation'][key] for key in ('answer', 'final_tool_status', 'final_tool_content')), 'Saved final observation')


def verify_clean_install(root: Path) -> dict:
    """Check installed-package provenance claims and five saved runtime outcomes."""
    references, data = load_section(root, 'clean_install_v1')
    run, env, comparison = data['execution'], data['environment'], data['comparison']
    manifest = json.loads((root / 'results/manifest.json').read_text())
    plan_ref = manifest['next_experiment_plan']
    plan = json.loads(checked_bytes(root, plan_ref['export'], plan_ref['sha256']))
    require(env['fresh_environment'] is True and env['deepagents_loaded_within_fresh_venv'] is True and
            env['deepagents_editable'] is False and env['system_site_packages'] is False, 'Environment isolation contradiction')
    require(run['criteria_sha256'] == plan_ref['sha256'] and comparison['plan_sha256'] == references['plan']['sha256'], 'Clean plan identity')
    validate_saved_run(run, plan)
    old_ref = manifest['crash_resume_v1']['execution']
    old = json.loads(checked_bytes(root, old_ref['export'], old_ref['sha256']))
    comparisons = []
    for case, previous in zip(run['cases'], old['cases'], strict=True):
        require(assess_case(case) == assess_case(previous), 'Clean behavior differs')
        verdict = assess_case(case)
        comparisons.append({'case': case['case'], 'same_assessed_behavior': True,
                            'tool_body_entries': verdict['tool_body_entries'], 'committed_effects': verdict['committed_effects'],
                            'approved_task_completed': verdict['approved_task_completed']})
    require(comparison['case_comparison'] == comparisons, 'Clean comparison contradicts observations')
    fingerprints = env['runtime']['selected_loaded_module_sha256']
    require(fingerprints == run['runtime']['selected_loaded_module_sha256'] == old['runtime']['selected_loaded_module_sha256'], 'Clean module identity')
    inventory = {f"{p['name']}=={p['version']}" for p in env['installed_packages']}
    recorded = {line for line in data['installed_version_inventory'].splitlines() if line and not line.startswith('#')}
    seeds = {line for line in data['seed_requirements'].splitlines() if line and not line.startswith('#')}
    require(inventory == recorded and seeds <= inventory, 'Clean installed package inventory')
    require(comparison['installation']['exit_code'] == 0 and comparison['installation']['timed_out'] is False and
            comparison['worker_processes'] == run['worker_processes'] and comparison['live_model_calls'] == 0, 'Clean installation summary')
    return {'status': 'passed', 'kind': 'stored clean-install evidence validation; no new installation or workers', 'cases_checked': 5}


def verify_outcome_reporting(root: Path) -> dict:
    """Check original SQL observations, fixed reporting criteria and unknown cases."""
    references, data = load_section(root, 'outcome_reporting_v1')
    plan, run = data['plan'], data['execution']
    require(run['criteria_sha256'] == references['plan']['sha256'] and
            run['reporter_sha256'] == references['implementation']['sha256'], 'Reporting artifact identity')
    source_ref = plan['source_execution']
    source = json.loads(checked_bytes(root, source_ref['export'], source_ref['sha256']))
    require(run['source_execution_sha256'] == source_ref['sha256'] and run['reporting_checks'] == len(run['observations']) == 7 and
            run['new_graph_workers'] == run['live_model_calls'] == 0, 'Reporting bounds or source')
    for index, (row, expected) in enumerate(zip(run['observations'], plan['cases'], strict=True)):
        require(row['case'] == expected['case'], 'Reporting roster')
        if index < 5:
            case = source['cases'][index]
            require(row['operation_id'] == case['operation_id'] and row['decision'] == case['decision'] and
                    row['approved_message'] == case['approved_message'] and row['original_scripted_answer'] == case['answer'] and
                    row['graph_finished'] is True and case['graph_completed'] is True, 'Reporting source context')
            receipts = [item['receipt'] for item in row['receiver_rows']]
            require(receipts == case['entries'] and row['source_database_unchanged'] is True, 'Receiver observations contradict saved runtime')
            tuples = [(item['operation_id'], item['message'], json.dumps(item['receipt'])) for item in row['receiver_rows']]
            require(matching_receipts(tuples, row['approved_message']), 'Receiver receipt conflict')
        else:
            require(row['receiver_rows'] is None and row['earlier_valid_receipt'] in source['cases'][0]['entries'] and
                    row['fixture_file_created_by_reporter'] is False, 'Reporting failure fixture')
        required_report = outcome_report(expected['expected_outcome'], row['operation_id'], expected['expected_effects'], True)
        require(row['application_report'] == required_report, 'Reporting conclusion contradicts frozen expectations')
    return {'status': 'passed', 'kind': 'stored reporting evidence validation; no new receiver reads or graph workers', 'observations_checked': 7}


def verify_final_response(root: Path) -> dict:
    """Bind final application delivery to fresh graph evidence and frozen criteria."""
    references, data = load_section(root, 'final_response_v1')
    plan, run = data['plan'], data['execution']
    manifest = json.loads((root / 'results/manifest.json').read_text())
    graph_ref = manifest['next_experiment_plan']
    graph_plan = json.loads(checked_bytes(root, graph_ref['export'], graph_ref['sha256']))
    require(run['criteria_sha256'] == references['plan']['sha256'] and
            run['graph_execution']['criteria_sha256'] == graph_ref['sha256'], 'Final response criteria')
    validate_saved_run(run['graph_execution'], graph_plan)
    require(run['fixture_contracts_met'] is True and len(run['deliveries']) == 6 and
            run['worker_processes'] == 19 and run['live_model_calls'] == run['provider_tokens'] == 0 and
            run['duration_s'] <= 600, 'Final response experiment bounds')
    for name, fingerprint in run['implementation_sha256'].items():
        require(name in ('final_response.py', 'reported_crash.py', 'outcome_reporting.py'), 'Unexpected response implementation')
        source = references.get('source_' + name.removesuffix('.py'), {'export': 'reliability_lab/' + name, 'sha256': fingerprint})
        require(source['sha256'] == fingerprint, 'Historical response source identity')
        checked_bytes(root, source['export'], fingerprint)
    outcomes = []
    for index, (row, expected) in enumerate(zip(run['deliveries'], plan['responses'], strict=True)):
        case = run['graph_execution']['cases'][index if index < 5 else 0]
        response = row['response']
        require(row['case'] == expected['case'] and response['model_answer'] == case['answer'] and
                response['delivery_source'] == 'receiver_reconciliation', 'Final delivery source')
        count = len(case['entries']) if index < 5 else None
        required = outcome_report(expected['expected_outcome'], case['operation_id'], count, case['graph_completed'])
        require(response['reconciliation'] == required and required['task_completed'] is expected['task_completed'], 'Final reconciliation')
        text = required['report']
        if required['outcome'] == 'completed_once':
            text += f" Recorded contents: {json.dumps(case['approved_message'])}."
        require(response['user_response'] == text, 'Final application response contradicts reconciliation')
        if index < 5:
            require(row['receiver_sha256_before'] == row['receiver_sha256_after'], 'Final receiver changed')
        else:
            require(row['missing_receiver_stayed_missing'] is True and case['graph_completed'] is True, 'Final unavailable-receiver fixture')
        outcomes.append(required['task_completed'])
    require(run['individual_task_outcomes'] == outcomes, 'Final task summary')
    return {'status': 'passed', 'kind': 'stored integrated-response evidence validation; no graph workers',
            'graph_cases_checked': 5, 'responses_checked': 6,
            'task_outcomes': outcomes, 'fixture_pass_is_not_universal_task_success': True}
