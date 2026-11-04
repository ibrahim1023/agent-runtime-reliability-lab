"""One native graph invocation in a fresh process using a shared checkpoint thread."""

import hashlib
import importlib
import json
import os
from pathlib import Path
import sys
import time

from reliability_lab.offline import install_offline_guard


def worker(directory: Path, phase: str) -> None:
    """Run a new user turn and publish only allowlisted checkpoint counter values."""
    install_offline_guard()
    from typing import Self
    from deepagents import create_deep_agent
    from langchain.agents.middleware import ToolCallLimitMiddleware, ToolRetryMiddleware
    from langchain.tools import ToolRuntime, tool
    from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
    from langchain_core.messages import AIMessage
    from langchain_core.outputs import ChatGeneration, ChatResult
    from langgraph.checkpoint.sqlite import SqliteSaver
    from reliability_lab.scripted_root import runtime_identity

    identity = json.loads((directory / 'identity.json').read_text())
    model_calls = 0; entries, proposals, events, generated = [], [], [], []

    @tool
    def read_probe(runtime: ToolRuntime) -> str:
        """Always fail the controlled read so native retries exhaust their budget."""
        entries.append(runtime.tool_call_id)
        events.append({'event': 'tool_body_error', 'tool_call_id': runtime.tool_call_id, 'error_type': 'OSError'})
        raise OSError('controlled persistent read failure')

    class PersistentModel(GenericFakeChatModel):
        def bind_tools(self, *args: object, **kwargs: object) -> Self:
            return self

        def _generate(self, messages, stop=None, run_manager=None, **kwargs):
            nonlocal model_calls
            model_calls += 1
            observed = [{'tool_call_id': m.tool_call_id, 'status': m.status, 'content': m.content}
                        for m in messages if m.type == 'tool']
            if model_calls <= 2:
                call_id = f'{phase}-call-{model_calls}'
                proposals.append(call_id)
                message = AIMessage(content='', id=f'{phase}-model-{model_calls}',
                                    tool_calls=[{'name': 'read_probe', 'args': {}, 'id': call_id}])
            else:
                message = AIMessage(content='The controlled read did not succeed.', id=f'{phase}-model-{model_calls}')
            generated.append(message.id)
            events.append({'event': 'model_generation', 'model_call': model_calls, 'tool_calls': message.tool_calls,
                           'observed_tool_messages': observed, 'content': message.content})
            return ChatResult(generations=[ChatGeneration(message=message)])

    config = {'configurable': {'thread_id': identity['thread_id']}, 'recursion_limit': 24}
    with SqliteSaver.from_conn_string(str(directory / 'checkpoints.sqlite')) as saver:
        saver.conn.execute('PRAGMA synchronous=FULL')
        def counters():
            checkpoint = saver.get_tuple(config)
            values = checkpoint.checkpoint['channel_values'] if checkpoint else {}
            return values.get('thread_tool_call_count', {}).get('__all__', 0), 'run_tool_call_count' in values
        before, run_before = counters()
        agent = create_deep_agent(model=PersistentModel(messages=iter([])), tools=[read_probe], checkpointer=saver,
            middleware=[ToolRetryMiddleware(max_retries=2, retry_on=(OSError,), initial_delay=0, jitter=False, on_failure='continue'),
                        ToolCallLimitMiddleware(run_limit=1, thread_limit=identity['thread_limit'], exit_behavior='end')])
        started = time.perf_counter()
        result = agent.invoke({'messages': [{'role': 'user', 'content': f'Controlled read request for {phase}.'}]}, config, durability='sync')
        elapsed = time.perf_counter() - started
        after, run_after = counters()
        snapshot = agent.get_state(config)
        messages = result['messages']
        all_tools = [{'tool_call_id': m.tool_call_id, 'status': m.status, 'content': m.content} for m in messages if m.type == 'tool']
        modules = ('langchain.agents.middleware.tool_call_limit', 'langgraph.channels.untracked_value', 'langchain.agents.middleware.tool_retry')
        report = {'phase': phase, 'pid': os.getpid(), 'thread_id': identity['thread_id'], 'input_kind': 'new_user_message',
                  'model_calls': model_calls, 'entries': entries, 'proposals': proposals,
                  'tool_messages': [m for m in all_tools if m['tool_call_id'] in proposals], 'all_tool_messages': all_tools,
                  'answer': messages[-1].content,
                  'answer_source': 'scripted_model' if messages[-1].id in generated else 'native_middleware',
                  'events': events, 'checkpoint_thread_before': before, 'checkpoint_thread_after': after,
                  'run_counter_checkpointed_before': run_before, 'run_counter_checkpointed_after': run_after,
                  'checkpoint_next': list(snapshot.next), 'graph_completed': not snapshot.next,
                  'duration_s': elapsed, 'runtime': runtime_identity(),
                  'inspected_module_sha256': {name: hashlib.sha256(Path(importlib.import_module(name).__file__).read_bytes()).hexdigest() for name in modules}}
        (directory / f'{phase}.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    worker(Path(sys.argv[1]), sys.argv[2])
