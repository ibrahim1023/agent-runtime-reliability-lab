"""Validate the reviewed Linux summary without another runtime execution."""

from datetime import datetime
import json
from pathlib import Path
import re

from reliability_lab.evidence import checked_bytes, require
from reliability_lab.recent_evidence import load_section


def verify_portable_reproduction(root: Path) -> dict:
    """Bind hosted observations to their frozen counts, source and comparison."""
    _, data = load_section(root, 'portable_reproduction_v1')
    result, run, comparison, plan = (data[key] for key in ('execution', 'hosted_run', 'comparison', 'plan'))
    require(result['all_contracts_met'] and result['runtime_exit_code'] == 0 and
            result['saved_observations_consistent'] and result['roster_matches'], 'Portable execution status')
    require(str(run['databaseId']) == result['run_id'] and run['headSha'] == result['commit'] and
            result['run_attempt'] == '1' and run['status'] == 'completed' and run['conclusion'] == 'success' and
            run['event'] == 'workflow_dispatch', 'Portable hosted run identity')
    require(len(run['jobs']) == 1 and run['jobs'][0]['conclusion'] == 'success' and
            all(s['conclusion'] == 'success' for s in run['jobs'][0]['steps']), 'Portable job interruption')
    artifact = run['artifact']
    require(artifact['members'] == ['public-summary.json'] and
            artifact['digest'] == 'sha256:' + artifact['downloaded_archive_sha256'], 'Portable artifact identity')
    require(result['worker_phases_observed'] == 19 and result['live_model_calls'] ==
            result['estimated_provider_tokens'] == 0 and result['install_outcome'] == result['runtime_outcome'] == 'success',
            'Portable execution bounds')
    require(result['learner_prediction'] == comparison['learner_prediction'] == plan['learner_prediction'], 'Portable prediction')
    seeds = dict(line.split('==') for line in data['seed_requirements'].splitlines() if line and not line.startswith('#'))
    environment = result['environment']
    require(len(seeds) == 8 and result['seed_versions_match'] and all(environment['installed_packages'].get(k) == v
            for k, v in seeds.items()) and result['runtime_identity']['packages'] == seeds, 'Portable seed versions')
    require(environment['python'] == plan['target']['python'] == '3.14.6' and environment['system'] == 'Linux' and
            environment['virtual_environment'] is True and environment['system_site_packages'] is False and
            environment['deepagents_inside_environment'] is True and environment['deepagents_editable'] is False,
            'Portable environment isolation')
    manifest = json.loads((root / 'results/manifest.json').read_text())
    prior = manifest['clean_install_v1']['execution']
    previous = json.loads(checked_bytes(root, prior['export'], prior['sha256']))
    require(result['runtime_identity']['selected_loaded_module_sha256'] ==
            previous['runtime']['selected_loaded_module_sha256'] and comparison['selected_module_hashes_match'] is True,
            'Portable selected module comparison')
    require([c['case'] for c in result['cases']] == list(plan['expectations']), 'Portable case roster')
    comparisons = []
    for case, old in zip(result['cases'], previous['cases'], strict=True):
        name = case['case']
        attempts, effects = plan['expectations'][name]
        rejected = name == 'protected-reject'
        control = name == 'unprotected-approve-control'
        require(case['contract_met'] and case['graph_completed'] and case['review_policy_handled'] and
                case['fresh_processes'] and case['stable_approved_identity'], 'Portable case contract')
        require([case['tool_entries'], case['committed_effects']] == [attempts, effects] and
                case['approved_task_completed'] is (not rejected and not control) and
                case['report_accounts_for_all_effects'] is (not control) and
                case['exact_receipt_reused'] is (None if rejected else not control), 'Portable effect/task outcome')
        require(case['phase_exit_codes'] == ([0, 0, 0] if rejected else [0, 0, 86, 0]) and
                case['phase_effect_counts'] == ([0, 0, 0] if rejected else [0, 0, 1, effects]) and
                case['phase_tool_entries'] == ([0, 0, 0] if rejected else [0, 0, 1, 2]), 'Portable phase observations')
        same = (attempts == len(old['tool_entries']) and effects == len(old['entries']) and
                case['approved_task_completed'] == old['verdicts']['approved_task_completed'])
        require(same, 'Portable outcome differs from previous case')
        comparisons.append({'case': name, 'tool_entries': attempts, 'committed_effects': effects,
                            'approved_task_completed': case['approved_task_completed'], 'same_attempt_effect_task_outcome': same})
    require(comparison['case_comparison'] == comparisons and comparison['dispatches'] ==
            comparison['installation_attempts'] == comparison['runtime_attempts'] == 1 and
            comparison['worker_phases'] == 19 and comparison['provider_calls'] == comparison['provider_tokens'] == 0,
            'Portable comparison bounds')
    environment_ref = manifest['clean_install_v1']['environment']
    old_environment = json.loads(checked_bytes(root, environment_ref['export'], environment_ref['sha256']))
    normalize = lambda name: re.sub(r'[-_.]+', '-', name).lower()
    old_packages = {normalize(p['name']): p['version'] for p in old_environment['installed_packages']}
    packages = environment['installed_packages']
    changes = {k: {'previous': old_packages[k], 'linux': packages[k]} for k in sorted(old_packages.keys() & packages.keys())
               if old_packages[k] != packages[k]}
    require(comparison['changed_installed_versions'] == changes and
            comparison['added_inventory_entries'] == {k: packages[k] for k in sorted(packages.keys() - old_packages.keys())} and
            comparison['removed_inventory_entries'] == {k: old_packages[k] for k in sorted(old_packages.keys() - packages.keys())},
            'Portable dependency comparison')
    job = run['jobs'][0]
    runtime_step = next(s for s in job['steps'] if s['name'] == 'Execute the existing five cases once')
    seconds = lambda phase: (datetime.fromisoformat(phase['completedAt'].replace('Z', '+00:00')) - datetime.fromisoformat(phase['startedAt'].replace('Z', '+00:00'))).total_seconds()
    require(comparison['job_wall_seconds'] == seconds(job) and comparison['runtime_step_wall_seconds'] == seconds(runtime_step),
            'Portable timing interpretation')
    return {'status': 'passed', 'kind': 'stored hosted summary validation; no installation or graph execution',
            'cases_checked': 5, 'worker_phases_observed': 19, 'new_workers': 0,
            'changed_transitive_versions': len(changes), 'control_task_failed': True}
