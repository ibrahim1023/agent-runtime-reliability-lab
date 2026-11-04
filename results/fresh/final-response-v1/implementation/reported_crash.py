"""Opt-in crash/resume experiment with reconciled final application responses."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
import uuid

from reliability_lab.crash_resume import run_crash_resume
from reliability_lab.evidence import checked_bytes
from reliability_lab.final_response import final_response
from reliability_lab.offline import install_offline_guard


def deliver_case(receiver: Path, case: dict) -> dict:
    """Route one completed graph record through the application delivery boundary."""
    return final_response(receiver, operation_id=case['operation_id'], approved_message=case['approved_message'],
                          decision=case['decision'], graph_finished=case['graph_completed'], model_answer=case['answer'])


def run_reported_crash(root: Path, *, learner_prediction: str = 'not supplied') -> tuple[dict, int]:
    """Execute five graph cases once, then six final-response checks without retries."""
    install_offline_guard()
    started = time.perf_counter()
    directory = Path('work/final-response') / uuid.uuid4().hex
    (root / directory).mkdir(parents=True)
    manifest = json.loads((root / 'results/manifest.json').read_text())
    reference = manifest['final_response_v1']['plan']
    plan = json.loads(checked_bytes(root, reference['export'], reference['sha256']))
    graph, graph_code = run_crash_resume(root, learner_prediction=learner_prediction)
    graph_directory = root / Path(graph['report_path']).parent
    deliveries = []
    for case in graph['cases']:
        receiver = graph_directory / case['case'] / 'receiver.sqlite'
        before = hashlib.sha256(receiver.read_bytes()).hexdigest()
        delivered = deliver_case(receiver, case)
        after = hashlib.sha256(receiver.read_bytes()).hexdigest()
        deliveries.append({'case': case['case'], 'response': delivered,
                           'receiver_sha256_before': before, 'receiver_sha256_after': after})
    if graph['cases']:
        unavailable = root / directory / 'unavailable-receiver.sqlite'
        delivered = deliver_case(unavailable, graph['cases'][0])
        deliveries.append({'case': 'receiver-unavailable-after-completion', 'response': delivered,
                           'fault': 'missing configured receiver path; actual receiver left intact',
                           'missing_receiver_stayed_missing': not unavailable.exists()})
    matches = len(deliveries) == len(plan['responses'])
    for row, expected in zip(deliveries, plan['responses']):
        result = row['response']
        matches = matches and row['case'] == expected['case'] and result['delivery_source'] == 'receiver_reconciliation'
        matches = matches and result['reconciliation']['outcome'] == expected['expected_outcome']
        matches = matches and result['reconciliation']['task_completed'] is expected['task_completed']
        matches = matches and expected.get('response_must_name', '') in result['user_response']
        if 'receiver_sha256_before' in row:
            matches = matches and row['receiver_sha256_before'] == row['receiver_sha256_after']
        else:
            matches = matches and row['missing_receiver_stayed_missing']
    elapsed = time.perf_counter() - started
    report = {'experiment_id': plan['experiment_id'], 'kind': 'fresh scripted graph recovery with application response integration; no live-model evaluation',
              'executed_at_utc': datetime.now(timezone.utc).isoformat(), 'learner_prediction': learner_prediction,
              'criteria_sha256': reference['sha256'], 'graph_execution': graph, 'deliveries': deliveries,
              'fixture_contracts_met': graph_code == 0 and matches and elapsed <= 600,
              'individual_task_outcomes': [row['response']['reconciliation']['task_completed'] for row in deliveries],
              'worker_processes': graph.get('worker_processes', sum(len(c['phases']) for c in graph['cases'])),
              'live_model_calls': 0, 'provider_tokens': 0, 'duration_s': elapsed,
              'implementation_sha256': {name: hashlib.sha256((root / 'reliability_lab' / name).read_bytes()).hexdigest()
                                       for name in ('final_response.py', 'reported_crash.py', 'outcome_reporting.py')},
              'report_path': str(directory / 'report.json'),
              'limitations': ['Deterministic application response, not a model honesty evaluation or SDK change',
                              'Closed local receiver scope; no concurrent writers',
                              'Embedded graph preflight wording mentions editable environment; this command does not establish installation origin']}
    (root / directory / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    return report, 0 if report['fixture_contracts_met'] else 1
