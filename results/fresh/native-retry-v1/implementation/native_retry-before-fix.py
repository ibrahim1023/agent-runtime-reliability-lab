"""Opt-in real agent graphs using native retry middleware and synchronous deadlines."""

from datetime import datetime, timezone
import hashlib
import importlib
import importlib.metadata
import json
from pathlib import Path
import threading
import time
import uuid

from reliability_lab.evidence import checked_bytes, require
from reliability_lab.offline import install_offline_guard
from reliability_lab.receiver import Ledger
from reliability_lab.retry_evidence import assess_retry_case
from reliability_lab.scripted_root import runtime_identity


class ResponseLost(TimeoutError):
    """Controlled failure after the receiver committed, before returning a result."""


def execute_case(directory: Path, expected: dict) -> dict:
    """Run one real Deep Agents graph; the scripted model proposes exactly one call."""
    from typing import Self
    from deepagents import create_deep_agent
    from langchain.agents.middleware import ToolRetryMiddleware
    from langchain.tools import ToolRuntime, tool
    from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
    from langchain_core.messages import AIMessage
    from langchain_core.outputs import ChatGeneration, ChatResult

    started = time.perf_counter()
    directory.mkdir()
    name = expected['case']; is_read = name.startswith('read-')
    protected = name == 'write-protected-retry'
    native_timeout = name == 'write-sync-step-timeout'
    operation_id = str(uuid.uuid4())
    ledger = Ledger(directory / 'receiver.sqlite', protected=protected)
    (directory / 'source.txt').write_text('north\nsouth')
    events, observations = [], []
    lock = threading.Lock(); entered = threading.Event(); release = threading.Event()
    attempts = 0

    def record(event: str, **values: object) -> None:
        with lock:
            entry = {'event': event, 'at_s': time.perf_counter() - started, **values}
            events.append(entry)
            with (directory / 'events.jsonl').open('a') as stream:
                stream.write(json.dumps(entry) + '\n')

    def probe(message: str, runtime: ToolRuntime) -> str:
        """Read the local fixture or record its declared note in the receiver."""
        nonlocal attempts
        attempts += 1
        operation = runtime.config['configurable']['operation_id']
        record('tool_enter', operation_id=operation, attempt=attempts)
        entered.set()
        if is_read:
            if name == 'read-exhausted' or attempts == 1:
                record('controlled_tool_error', error_type='OSError')
                raise OSError('controlled temporary read failure')
            return (directory / 'source.txt').read_text()
        if native_timeout and not release.wait(timeout=2):
            record('release_guard_failed')
            raise RuntimeError('controlled release gate did not open')
        receipt, reused = ledger.record(operation, message)
        record('receiver_result', receipt=json.loads(receipt), reused=reused)
        if not native_timeout and attempts == 1:
            record('controlled_tool_error', error_type='ResponseLost')
            raise ResponseLost('controlled response lost after receiver commit')
        return receipt

    tool_name = 'read_probe' if is_read else 'write_probe'
    executable = tool(tool_name)(probe)

    class ScriptedModel(GenericFakeChatModel):
        def bind_tools(self, *args: object, **kwargs: object) -> Self:
            return self

        def _generate(self, messages, stop=None, run_manager=None, **kwargs):
            latest = messages[-1]
            if latest.type == 'tool':
                observation = {'status': latest.status, 'content': latest.content}
                observations.append(observation)
                record('model_observed_tool', **observation)
                message = AIMessage(content=latest.content)
            else:
                record('model_proposal', name=tool_name, args={'message': 'note'})
                message = AIMessage(content='', tool_calls=[{'name': tool_name, 'args': {'message': 'note'}, 'id': 'retry-call'}])
            return ChatResult(generations=[ChatGeneration(message=message)])

    scope = ['read_probe'] if name == 'write-unprotected-read-scoped-retry' else None
    middleware = [] if native_timeout else [ToolRetryMiddleware(
        max_retries=expected['max_retries'], tools=scope, retry_on=(OSError,),
        initial_delay=0, jitter=False, on_failure='continue')]
    agent = create_deep_agent(model=ScriptedModel(messages=iter([])), tools=[executable], middleware=middleware)
    if native_timeout:
        agent.bound.step_timeout = .05

    def controller() -> None:
        if entered.wait(timeout=2):
            time.sleep(.2)
            record('gate_release')
            release.set()
        else:
            record('controller_no_tool_start')

    thread = threading.Thread(target=controller, name='controlled-tool-release') if native_timeout else None
    if thread:
        thread.start()
    outcome, error_message, result = 'completed', None, None
    invoke_started = time.perf_counter()
    try:
        result = agent.invoke({'messages': [{'role': 'user', 'content': 'Execute the one declared local operation.'}]},
                              {'configurable': {'operation_id': operation_id}, 'recursion_limit': 10})
        record('graph_return')
    except Exception as error:
        outcome, error_message = type(error).__name__, str(error)
        record('graph_error', error_type=outcome)
    finally:
        release.set()
        if thread:
            thread.join(timeout=3)
    elapsed = time.perf_counter() - invoke_started
    messages = result['messages'] if result else []
    tools = [message for message in messages if message.type == 'tool']
    case = {'case': name, 'operation_id': operation_id, 'protected': protected,
            'graph_outcome': outcome, 'graph_error': error_message, 'duration_s': elapsed,
            'case_duration_s': time.perf_counter() - started,
            'tool_status': tools[-1].status if tools else None,
            'tool_content': tools[-1].content if tools else None,
            'answer': messages[-1].content if messages else None,
            'events': events, 'entries': ledger.entries(), 'model_observations': observations,
            'controller_joined': thread is None or not thread.is_alive(),
            'step_timeout_s': .05 if native_timeout else None}
    case['verdicts'] = assess_retry_case(case, expected)
    (directory / 'record.json').write_text(json.dumps(case, indent=2) + '\n')
    return case


def run_native_retry(root: Path, *, learner_prediction: str = 'not supplied') -> tuple[dict, int]:
    """Run the frozen native-runtime cases once, preserving interruptions without retry."""
    install_offline_guard()
    directory = Path('work/native-retry') / uuid.uuid4().hex
    (root / directory).mkdir(parents=True)
    reference = json.loads((root / 'results/manifest.json').read_text())['native_retry_v1']['plan']
    plan = json.loads(checked_bytes(root, reference['export'], reference['sha256']))
    report = {'experiment_id': plan['experiment_id'], 'kind': plan['kind'], 'learner_prediction': learner_prediction,
              'started_at_utc': datetime.now(timezone.utc).isoformat(), 'criteria_sha256': reference['sha256'],
              'cases': [], 'live_model_calls': 0, 'provider_tokens': 0, 'report_path': str(directory / 'report.json')}
    started = time.perf_counter()
    try:
        report['runtime'] = runtime_identity()
        fingerprints = {name: hashlib.sha256(Path(importlib.import_module(name).__file__).read_bytes()).hexdigest()
                        for name in plan['inspected_module_sha256']}
        require(fingerprints == plan['inspected_module_sha256'], 'Installed runtime source differs from frozen inspection')
        report['inspected_module_sha256'] = fingerprints
        for expected in plan['cases']:
            case = execute_case(root / directory / expected['case'], expected)
            report['cases'].append(case)
            (root / directory / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
            if not case['verdicts']['contract_met'] or time.perf_counter() - started > 90:
                break
        report['fixture_contracts_met'] = len(report['cases']) == 6 and all(c['verdicts']['contract_met'] for c in report['cases'])
    except (ImportError, OSError, ValueError, KeyError, TypeError) as error:
        report['fixture_contracts_met'] = False
        report['interruption_type'] = type(error).__name__
        (root / directory / 'error.txt').write_text(str(error))
    report['duration_s'] = time.perf_counter() - started
    report['implementation_sha256'] = {name: hashlib.sha256((root / 'reliability_lab' / name).read_bytes()).hexdigest()
                                       for name in ('native_retry.py', 'retry_evidence.py', 'receiver.py')}
    (root / directory / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    return report, 0 if report['fixture_contracts_met'] else 1
