"""Narrow, serial approval policy paired with the native thread limiter."""

from collections.abc import Mapping
from functools import partial
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel
    from langchain_core.tools import BaseTool
    from langgraph.checkpoint.base import BaseCheckpointSaver
    from langgraph.graph.state import CompiledStateGraph


def review_required(request: object, *, thread_limit: int) -> bool:
    """Request review only for an eligible single action; never spend allowance.

    False skips approval, not execution enforcement: the paired native limiter
    must remain configured with this same thread limit. Invalid counter or batch
    shapes raise instead of allowing an unsupported action through this policy.
    """
    if type(thread_limit) is not int or thread_limit < 1:
        raise ValueError('A positive integer thread limit is required')
    state = getattr(request, 'state', None)
    if not isinstance(state, Mapping):
        raise ValueError('Review requires native graph state')
    counts = state.get('thread_tool_call_count', {})
    if not isinstance(counts, Mapping):
        raise ValueError('Malformed native thread counter')
    count = counts.get('__all__', 0)
    if type(count) is not int or count < 0:
        raise ValueError('Malformed native thread counter')
    latest = next((m for m in reversed(state.get('messages', [])) if getattr(m, 'type', None) == 'ai'), None)
    calls = getattr(latest, 'tool_calls', [])
    if (len(calls) != 1 or calls[0].get('name') != 'record_action' or
            calls[0] != getattr(request, 'tool_call', None)):
        raise ValueError('Only one record_action proposal is supported')
    return count < thread_limit


def create_budget_aware_agent(*, model: 'BaseChatModel', action: 'BaseTool',
                              checkpointer: 'BaseCheckpointSaver', thread_limit: int = 1) -> 'CompiledStateGraph':
    """Pair review eligibility and enforcement for the lab's one-action fixture."""
    from deepagents import create_deep_agent
    from langchain.agents.middleware import ToolCallLimitMiddleware

    if action.name != 'record_action' or type(thread_limit) is not int or thread_limit < 1:
        raise ValueError('Expected record_action and a positive integer thread limit')
    return create_deep_agent(
        model=model, tools=[action], checkpointer=checkpointer,
        interrupt_on={'record_action': {'allowed_decisions': ['approve', 'reject', 'edit'],
                                       'when': partial(review_required, thread_limit=thread_limit)}},
        middleware=[ToolCallLimitMiddleware(thread_limit=thread_limit, exit_behavior='end')],
    )
