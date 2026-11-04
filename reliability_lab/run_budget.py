"""Opt-in native per-invocation model/tool limits with a deliberately persistent model."""

from datetime import datetime, timezone
import hashlib
import importlib
import json
from pathlib import Path
import time
import uuid

from reliability_lab.evidence import checked_bytes, require
from reliability_lab.offline import install_offline_guard
from reliability_lab.run_budget_evidence import assess_budget_case
from reliability_lab.scripted_root import runtime_identity


def execute_budget_case(directory: Path, expected: dict) -> dict:
    """Exercise native middleware; every synthetic read entry fails deliberately."""
    from typing import Self
    from deepagents import create_deep_agent
    from langchain.agents.middleware import ModelCallLimitMiddleware, ToolCallLimitMiddleware, ToolRetryMiddleware
    from langchain.tools import ToolRuntime, tool
    from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
    from langchain_core.messages import AIMessage
    from langchain_core.outputs import ChatGeneration, ChatResult

    directory.mkdir()
    started = time.perf_counter()
    entries, proposals, events, generated = [], [], [], []
    model_calls = 0

    def record(event: str, **values: object) -> None:
        entry = {'event': event, 'at_s': time.perf_counter() - started, **values}
        events.append(entry)
        with (directory / 'events.jsonl').open('a') as stream:
            stream.write(json.dumps(entry) + '\n')

    @tool
    def read_probe(runtime: ToolRuntime) -> str:
        """Attempt the controlled read, which always reports a temporary failure."""
        entries.append(runtime.tool_call_id)
        record('tool_body_error', tool_call_id=runtime.tool_call_id, error_type='OSError')
        raise OSError('controlled persistent read failure')

    class PersistentModel(GenericFakeChatModel):
        def bind_tools(self, *args: object, **kwargs: object) -> Self:
            return self

        def _generate(self, messages, stop=None, run_manager=None, **kwargs):
            nonlocal model_calls
            model_calls += 1
            observed = [{'tool_call_id': item.tool_call_id, 'status': item.status, 'content': item.content}
                        for item in messages if item.type == 'tool']
            if model_calls <= 4:
                call_id = f'budget-call-{model_calls}'
                proposals.append(call_id)
                result = AIMessage(content='', id=f'scripted-{model_calls}',
                                   tool_calls=[{'name': 'read_probe', 'args': {}, 'id': call_id}])
            else:
                result = AIMessage(content='The read failed in all requested attempts.', id=f'scripted-{model_calls}')
            generated.append(result.id)
            record('model_generation', model_call=model_calls, observed_tool_messages=observed,
                   generated_id=result.id, tool_calls=result.tool_calls, content=result.content)
            return ChatResult(generations=[ChatGeneration(message=result)])

    middleware = [ToolRetryMiddleware(max_retries=2, retry_on=(OSError,), initial_delay=0,
                                      jitter=False, on_failure='continue')]
    if expected['tool_limit'] is not None:
        middleware.append(ToolCallLimitMiddleware(run_limit=expected['tool_limit'], exit_behavior='end'))
    if expected['model_limit'] is not None:
        middleware.append(ModelCallLimitMiddleware(run_limit=expected['model_limit'], exit_behavior='end'))
    agent = create_deep_agent(model=PersistentModel(messages=iter([])), tools=[read_probe], middleware=middleware)
    result, error = None, None
    try:
        result = agent.invoke({'messages': [{'role': 'user', 'content': 'Attempt the controlled read.'}]},
                              {'recursion_limit': 24})
    except Exception as exc:
        error = {'error_type': type(exc).__name__, 'message': str(exc)}
        record('graph_error', **error)
    messages = result['messages'] if result else []
    final = messages[-1] if messages else None
    case = {'case': expected['case'], 'model_calls': model_calls, 'proposals': proposals, 'entries': entries,
            'body_errors': len([event for event in events if event['event'] == 'tool_body_error']),
            'graph_completed': result is not None, 'graph_error': error,
            'tool_messages': [{'tool_call_id': m.tool_call_id, 'status': m.status, 'content': m.content}
                              for m in messages if m.type == 'tool'],
            'answer': final.content if final else None,
            'final_answer_source': 'scripted_model' if final and final.id in generated else 'native_middleware',
            'duration_s': time.perf_counter() - started, 'events': events}
    case['verdicts'] = assess_budget_case(case, expected)
    (directory / 'record.json').write_text(json.dumps(case, indent=2) + '\n')
    return case


def run_budget_check(root: Path, *, learner_prediction: str = 'not supplied') -> tuple[dict, int]:
    """Run four fresh graphs once; preserve any unexpected result without retries."""
    install_offline_guard()
    directory = Path('work/run-budget') / uuid.uuid4().hex
    (root / directory).mkdir(parents=True)
    ref = json.loads((root / 'results/manifest.json').read_text())['run_budget_v1']['plan']
    plan = json.loads(checked_bytes(root, ref['export'], ref['sha256']))
    report = {'experiment_id': plan['experiment_id'], 'kind': plan['kind'],
              'learner_prediction': learner_prediction, 'started_at_utc': datetime.now(timezone.utc).isoformat(),
              'criteria_sha256': ref['sha256'], 'cases': [], 'live_model_calls': 0, 'provider_tokens': 0,
              'report_path': str(directory / 'report.json')}
    started = time.perf_counter()
    try:
        report['runtime'] = runtime_identity()
        fingerprints = {name: hashlib.sha256(Path(importlib.import_module(name).__file__).read_bytes()).hexdigest()
                        for name in plan['inspected_module_sha256']}
        require(fingerprints == plan['inspected_module_sha256'], 'Inspected native middleware changed')
        report['inspected_module_sha256'] = fingerprints
        for expected in plan['cases']:
            case = execute_budget_case(root / directory / expected['case'], expected)
            report['cases'].append(case)
            (root / directory / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
            if not case['verdicts']['contract_met']:
                break
        report['fixture_contracts_met'] = len(report['cases']) == 4 and all(c['verdicts']['contract_met'] for c in report['cases'])
    except (ImportError, OSError, ValueError, KeyError, TypeError, AttributeError, RuntimeError) as error:
        report['fixture_contracts_met'] = False
        report['interruption_type'] = type(error).__name__
        (root / directory / 'error.txt').write_text(str(error))
    report['duration_s'] = time.perf_counter() - started
    report['implementation_sha256'] = {name: hashlib.sha256((root / 'reliability_lab' / name).read_bytes()).hexdigest()
                                       for name in ('run_budget.py', 'run_budget_evidence.py')}
    (root / directory / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    return report, 0 if report['fixture_contracts_met'] else 1
