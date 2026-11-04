"""Bounded two-turn budget experiments across fresh processes and shared checkpoints."""

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import uuid

from reliability_lab.budget_lifetime_evidence import assess_lifetime, successful_launches
from reliability_lab.crash_resume import clean_environment
from reliability_lab.evidence import checked_bytes
from reliability_lab.offline import install_offline_guard


def run_lifetime(root: Path, *, learner_prediction: str = 'not supplied') -> tuple[dict, int]:
    """Launch each phase once, preserving any setup or runtime interruption."""
    install_offline_guard()
    relative = Path('work/budget-lifetime') / uuid.uuid4().hex
    directory = root / relative; directory.mkdir(parents=True)
    reference = json.loads((root / 'results/manifest.json').read_text())['budget_lifetime_v1']['plan']
    plan = json.loads(checked_bytes(root, reference['export'], reference['sha256']))
    report = {'experiment_id': plan['experiment_id'], 'kind': plan['kind'], 'learner_prediction': learner_prediction,
              'criteria_sha256': reference['sha256'], 'cases': [], 'launches': [], 'live_model_calls': 0, 'provider_tokens': 0}
    for expected in plan['conditions']:
        case_dir = directory / expected['case']; case_dir.mkdir()
        identity = {'thread_id': str(uuid.uuid4()), 'thread_limit': expected['thread_limit']}
        (case_dir / 'identity.json').write_text(json.dumps(identity))
        case = {'case': expected['case'], 'thread_id': identity['thread_id'], 'phases': [], 'launches': []}
        report['cases'].append(case)
        for phase in plan['phases']:
            started = time.perf_counter()
            with (case_dir / f'{phase}.log').open('w') as log:
                try:
                    process = subprocess.run([sys.executable, '-m', 'reliability_lab.budget_lifetime_worker', str(case_dir), phase],
                        cwd=root, env=clean_environment(), stdout=log, stderr=subprocess.STDOUT, timeout=10)
                    launch = {'case': expected['case'], 'phase': phase, 'exit_code': process.returncode, 'timed_out': False}
                except subprocess.TimeoutExpired:
                    launch = {'case': expected['case'], 'phase': phase, 'exit_code': None, 'timed_out': True}
            launch['duration_s'] = time.perf_counter() - started; report['launches'].append(launch); case['launches'].append(launch)
            path = case_dir / f'{phase}.json'
            if path.exists():case['phases'].append(json.loads(path.read_text()))
            (directory / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
            if launch['exit_code'] != 0 or launch['timed_out']:break
        case['verdicts'] = assess_lifetime(case, expected) if len(case['phases']) == 2 else {'contract_met': False, 'interruption': True}
        case['verdicts']['contract_met'] = case['verdicts']['contract_met'] and successful_launches(case['launches'], 2)
        if not case['verdicts']['contract_met']:break
    report['fixture_contracts_met'] = len(report['cases']) == 2 and all(c['verdicts']['contract_met'] for c in report['cases']) and successful_launches(report['launches'], 4)
    report['implementation_sha256'] = {name: hashlib.sha256((root / 'reliability_lab' / name).read_bytes()).hexdigest()
        for name in ('budget_lifetime.py', 'budget_lifetime_worker.py', 'budget_lifetime_evidence.py')}
    report['report_path'] = str(relative / 'report.json')
    (directory / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    return report, 0 if report['fixture_contracts_met'] else 1
