"""Bounded approval/budget/crash phases in separate native-runtime worker processes."""

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import uuid

from reliability_lab.budget_recovery_evidence import assess_recovery
from reliability_lab.crash_resume import clean_environment, read_events
from reliability_lab.evidence import checked_bytes
from reliability_lab.offline import install_offline_guard
from reliability_lab.receiver import Ledger


def run_budget_recovery(root: Path, *, learner_prediction: str = 'not supplied') -> tuple[dict, int]:
    """Run each frozen phase once and keep unexpected exits as failures."""
    install_offline_guard()
    relative = Path('work/budget-recovery') / uuid.uuid4().hex
    directory = root / relative; directory.mkdir(parents=True)
    reference = json.loads((root / 'results/manifest.json').read_text())['budget_recovery_v1']['plan']
    plan = json.loads(checked_bytes(root, reference['export'], reference['sha256']))
    report = {'experiment_id': plan['experiment_id'], 'kind': plan['kind'], 'criteria_sha256': reference['sha256'],
              'learner_prediction': learner_prediction, 'cases': [], 'live_model_calls': 0, 'provider_tokens': 0}
    started = time.perf_counter()
    for expected in plan['conditions']:
        case_dir = directory / expected['case']; case_dir.mkdir()
        identity = {'thread_id': str(uuid.uuid4()), 'first_operation_id': str(uuid.uuid4()),
                    'next_operation_id': str(uuid.uuid4()), 'protected': expected['protected'],
                    'inspected_module_sha256': plan['inspected_module_sha256']}
        with (case_dir / 'identity.json').open('x') as stream:
            stream.write(json.dumps(identity, indent=2)); stream.flush()
        ledger = Ledger(case_dir / 'receiver.sqlite', protected=identity['protected'])
        case = {'case': expected['case'], **identity, 'phases': []}; report['cases'].append(case)
        for phase, expected_exit in zip(plan['phases'], plan['expected_exit_codes'], strict=True):
            launched = time.perf_counter()
            with (case_dir / f'{phase}.log').open('w') as log:
                process = subprocess.Popen([sys.executable, '-m', 'reliability_lab.budget_recovery_worker', str(case_dir), phase],
                    cwd=root, env=clean_environment(), stdout=log, stderr=subprocess.STDOUT)
                timeout = False
                try:code = process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill(); code = process.wait(); timeout = True
            observation = case_dir / f'{phase}.json'
            events = read_events(case_dir)
            row = {'phase': phase, 'pid': process.pid, 'exit_code': code, 'timeout': timeout,
                   'duration_s': time.perf_counter()-launched, 'observation': json.loads(observation.read_text()) if observation.exists() else {},
                   'tool_entries': sum(e['event']=='tool_enter' for e in events), 'effects': len(ledger.entries())}
            case['phases'].append(row)
            (directory / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
            if timeout or code != expected_exit or time.perf_counter()-started > 120:break
        events = read_events(case_dir)
        case.update(events=events, entries=ledger.entries(),
                    tool_entries=[e for e in events if e['event']=='tool_enter'],
                    receiver_results=[e for e in events if e['event']=='receiver_result'])
        case['verdicts'] = assess_recovery(case)
        if not case['verdicts']['contract_met']:break
    report['fixture_contracts_met'] = len(report['cases'])==2 and all(c['verdicts']['contract_met'] for c in report['cases'])
    report['duration_s'] = time.perf_counter()-started
    report['worker_processes'] = sum(len(c['phases']) for c in report['cases'])
    report['implementation_sha256'] = {name: hashlib.sha256((root/'reliability_lab'/name).read_bytes()).hexdigest()
        for name in ('budget_recovery.py','budget_recovery_worker.py','budget_recovery_evidence.py','receiver.py')}
    report['report_path'] = str(relative/'report.json')
    (directory/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    return report, 0 if report['fixture_contracts_met'] else 1
