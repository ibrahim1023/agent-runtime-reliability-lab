"""Run the frozen comparison once; optional runtime imports stay in workers."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid

from reliability_lab.approval_budget_evidence import assess_approval_case
from reliability_lab.crash_resume import clean_environment, read_events
from reliability_lab.offline import install_offline_guard
from reliability_lab.receiver import Ledger


def run_approval_budget(root: Path, *, learner_prediction: str = 'not supplied') -> tuple[dict, int]:
    """Keep one bounded attempt, including any unexpected worker failure."""
    install_offline_guard()
    plan_path = root / 'results/budget-aware-approval-plan-v1.json'
    plan = json.loads(plan_path.read_text())
    relative = Path('work/approval-budget') / uuid.uuid4().hex
    directory = root / relative; directory.mkdir(parents=True)
    report = {'experiment_id': plan['experiment_id'], 'kind': plan['kind'], 'learner_prediction': learner_prediction,
              'criteria_sha256': hashlib.sha256(plan_path.read_bytes()).hexdigest(), 'cases': [],
              'provider_calls': 0, 'provider_tokens': 0, 'report_path': str(relative / 'report.json')}
    report['implementation_sha256'] = {name: hashlib.sha256((root / 'reliability_lab' / name).read_bytes()).hexdigest()
        for name in ('approval_budget.py', 'approval_budget_worker.py', 'approval_budget_run.py', 'approval_budget_evidence.py', 'receiver.py')}
    launched_workers = 0
    started = time.perf_counter()
    deadline = started + plan['budget']['max_total_seconds']
    for expected in plan['conditions']:
        case_dir = directory / expected['case']; case_dir.mkdir()
        identity = {'thread_id': str(uuid.uuid4()), 'first_operation_id': str(uuid.uuid4()),
                    'next_operation_id': str(uuid.uuid4()), 'mode': expected['mode'],
                    'crash': expected.get('crash', False), 'inspected_module_sha256': plan['inspected_module_sha256'],
                    'implementation_sha256': report['implementation_sha256']}
        with (case_dir / 'identity.json').open('x') as stream:
            stream.write(json.dumps(identity, indent=2)); stream.flush(); os.fsync(stream.fileno())
        ledger = Ledger(case_dir / 'receiver.sqlite', protected=True)
        case = {'case': expected['case'], **identity, 'phases': []}; report['cases'].append(case)
        for phase, expected_exit in zip(expected['phases'], expected['exits'], strict=True):
            remaining = deadline - time.perf_counter()
            if remaining <= 0 or launched_workers >= plan['budget']['maximum_worker_phases']:
                break
            launched_workers += 1
            launched = time.perf_counter()
            with (case_dir / f'{phase}.log').open('w') as log:
                process = subprocess.Popen([sys.executable, '-m', 'reliability_lab.approval_budget_worker', str(case_dir), phase],
                    cwd=root, env=clean_environment(), stdout=log, stderr=subprocess.STDOUT)
                timeout = False
                try:
                    code = process.wait(timeout=min(20, remaining))
                except subprocess.TimeoutExpired:
                    process.kill(); code = process.wait(); timeout = True
            path = case_dir / f'{phase}.json'
            try:
                observation = json.loads(path.read_text()) if path.exists() else {}
                events = read_events(case_dir)
            except (OSError, ValueError, TypeError) as error:
                case['observation_error_type'] = type(error).__name__
                observation, events = {}, []
            case['phases'].append({'phase': phase, 'pid': process.pid, 'exit_code': code, 'timeout': timeout,
                'duration_s': time.perf_counter()-launched, 'observation': observation,
                'effects': len(ledger.entries()), 'tool_entries': sum(e['event'] == 'tool_enter' for e in events)})
            (directory / 'report.json').write_text(json.dumps(report, indent=2)+'\n')
            if timeout or code != expected_exit or 'observation_error_type' in case:
                break
        try:
            events = read_events(case_dir)
        except (OSError, ValueError, TypeError) as error:
            case['observation_error_type'] = type(error).__name__
            events = []
        case.update(events=events, entries=ledger.entries(),
                    tool_entries=[e for e in events if e['event'] == 'tool_enter'],
                    receiver_results=[e for e in events if e['event'] == 'receiver_result'])
        case['verdicts'] = assess_approval_case(case, expected)
        if not case['verdicts']['contract_met']:
            break
    report['worker_processes'] = sum(len(c['phases']) for c in report['cases'])
    report['duration_s'] = time.perf_counter()-started
    report['sources_unchanged'] = all(hashlib.sha256((root / 'reliability_lab' / name).read_bytes()).hexdigest() == digest
        for name, digest in report['implementation_sha256'].items())
    report['fixture_contracts_met'] = report['sources_unchanged'] and len(report['cases']) == 6 and all(c['verdicts']['contract_met'] for c in report['cases'])
    (directory / 'report.json').write_text(json.dumps(report, indent=2)+'\n')
    return report, 0 if report['fixture_contracts_met'] else 1
