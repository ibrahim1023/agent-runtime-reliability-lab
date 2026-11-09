"""One phase of the frozen baseline/candidate approval policy comparison."""

import hashlib
import importlib
import json
import os
from pathlib import Path
import sys
import time

from reliability_lab.crash_worker import journal
from reliability_lab.evidence import require
from reliability_lab.offline import install_offline_guard
from reliability_lab.receiver import Ledger


def worker(directory: Path, phase: str) -> None:
    """Observe native interrupts, counters, tool results and selected checkpoint state."""
    install_offline_guard()
    from typing import Self
    from deepagents import create_deep_agent
    from langchain.agents.middleware import ToolCallLimitMiddleware
    from langchain.tools import ToolRuntime, tool
    from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
    from langchain_core.messages import AIMessage
    from langchain_core.outputs import ChatGeneration, ChatResult
    from langgraph.checkpoint.sqlite import SqliteSaver
    from langgraph.types import Command
    from reliability_lab.approval_budget import create_budget_aware_agent
    from reliability_lab.scripted_root import runtime_identity

    identity = json.loads((directory / 'identity.json').read_text())
    is_next = phase in ('new-request', 'approve-next')
    operation_id = identity['next_operation_id'] if is_next else identity['first_operation_id']
    journal(directory, {'event': 'worker_start', 'phase': phase, 'operation_id': operation_id})
    fingerprints = {name: hashlib.sha256(Path(importlib.import_module(name).__file__).read_bytes()).hexdigest()
                    for name in identity['inspected_module_sha256']}
    require(fingerprints == identity['inspected_module_sha256'], 'Inspected native source mismatch')
    lab_source = Path(__file__).resolve().parent
    require(all(hashlib.sha256((lab_source / name).read_bytes()).hexdigest() == digest
                for name, digest in identity['implementation_sha256'].items()), 'Lab source changed before graph invocation')
    runtime = runtime_identity()
    journal(directory, {'event': 'worker_preflight', 'phase': phase, 'runtime': runtime,
                        'inspected_module_sha256': fingerprints})
    generated = []

    @tool
    def record_action(message: str, runtime: ToolRuntime) -> str:
        """Record the approved note, optionally crashing after its durable commit."""
        current = runtime.config['configurable']['operation_id']
        count = runtime.state.get('thread_tool_call_count', {}).get('__all__', 0)
        journal(directory, {'event': 'tool_enter', 'phase': phase, 'operation_id': current,
                            'message': message, 'thread_count': count})
        receipt, reused = Ledger(directory / 'receiver.sqlite', protected=True).record(current, message)
        journal(directory, {'event': 'receiver_result', 'phase': phase, 'receipt': json.loads(receipt), 'reused': reused})
        marker = directory / 'crash-consumed'
        if identity['crash'] and not marker.exists():
            with marker.open('x') as stream:
                stream.write('committed; tool has not returned\n'); stream.flush(); os.fsync(stream.fileno())
            os._exit(86)
        return receipt

    class ScriptedModel(GenericFakeChatModel):
        def bind_tools(self, *args: object, **kwargs: object) -> Self:
            return self

        def _generate(self, messages, stop=None, run_manager=None, **kwargs):
            latest = messages[-1]
            if latest.type == 'tool':
                journal(directory, {'event': 'model_observed_tool', 'phase': phase, 'content': latest.content,
                                    'status': latest.status, 'tool_call_id': latest.tool_call_id})
                response = AIMessage(content=latest.content, id=f'{phase}-response')
            else:
                call_id, message = ('next-call', 'next-note') if is_next else ('first-call', 'note')
                journal(directory, {'event': 'model_proposal', 'phase': phase, 'tool_call_id': call_id,
                                    'args': {'message': message}, 'operation_id': operation_id})
                response = AIMessage(content='', id=f'{phase}-proposal',
                                     tool_calls=[{'name': 'record_action', 'args': {'message': message}, 'id': call_id}])
            generated.append(response.id)
            return ChatResult(generations=[ChatGeneration(message=response)])

    config = {'configurable': {'thread_id': identity['thread_id'], 'operation_id': operation_id}, 'recursion_limit': 24}
    inputs, input_kind = None, 'resume_none'
    if phase in ('initial', 'new-request'):
        inputs = {'messages': [{'role': 'user', 'content': 'Record the next note.' if is_next else 'Record the note.'}]}
        input_kind = 'new_user_message'
    elif phase in ('approve-first', 'approve-next', 'reject-first', 'edit-first'):
        decision = {'type': 'reject' if phase == 'reject-first' else 'edit' if phase == 'edit-first' else 'approve'}
        if phase == 'edit-first':
            decision['edited_action'] = {'name': 'record_action', 'args': {'message': 'approved-note'}}
        inputs = Command(resume={'decisions': [decision]}); input_kind = 'simulated_decision'
        journal(directory, {'event': 'reviewer_decision', 'phase': phase, 'decision': decision, 'source': 'simulated_reviewer'})
    with SqliteSaver.from_conn_string(str(directory / 'checkpoints.sqlite')) as saver:
        saver.conn.execute('PRAGMA synchronous=FULL')
        def count():
            saved = saver.get_tuple(config)
            values = saved.checkpoint['channel_values'] if saved else {}
            return values.get('thread_tool_call_count', {}).get('__all__', 0)
        before = count()
        journal(directory, {'event': 'checkpoint_before', 'phase': phase, 'thread_count': before})
        model = ScriptedModel(messages=iter([]))
        if identity['mode'] == 'candidate':
            agent = create_budget_aware_agent(model=model, action=record_action, checkpointer=saver, thread_limit=1)
        else:
            agent = create_deep_agent(model=model, tools=[record_action], checkpointer=saver,
                interrupt_on={'record_action': {'allowed_decisions': ['approve', 'reject', 'edit']}},
                middleware=[ToolCallLimitMiddleware(thread_limit=1, exit_behavior='end')])
        started = time.perf_counter()
        result = agent.invoke(inputs, config, durability='sync')
        snapshot = agent.get_state(config)
        interrupts = [{'id': item.id, 'value': item.value} for item in result.get('__interrupt__', [])]
        tools = [{'tool_call_id': m.tool_call_id, 'name': m.name, 'status': m.status, 'content': m.content}
                 for m in result['messages'] if m.type == 'tool']
        last = tools[-1] if tools else None
        response = result['messages'][-1]
        observation = {'phase': phase, 'pid': os.getpid(), 'operation_id': operation_id, 'thread_id': identity['thread_id'],
            'input_kind': input_kind, 'thread_count_before': before, 'thread_count_after': count(),
            'interrupts': interrupts, 'checkpoint_next': list(snapshot.next), 'tool_messages': tools,
            'final_tool_call_id': last['tool_call_id'] if last else None,
            'final_tool_status': last['status'] if last else None, 'final_tool_content': last['content'] if last else None,
            'answer': None if interrupts else response.content,
            'answer_source': 'scripted_model' if response.id in generated else 'native_middleware',
            'duration_s': time.perf_counter()-started, 'runtime': runtime, 'inspected_module_sha256': fingerprints}
        (directory / f'{phase}.json').write_text(json.dumps(observation, indent=2)+'\n')


if __name__ == '__main__':
    worker(Path(sys.argv[1]), sys.argv[2])
