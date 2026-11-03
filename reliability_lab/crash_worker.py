"""Opt-in worker: reuse the agent stack, with no provider or replacement loop."""

import json
import os
from pathlib import Path
import sys
import time

from reliability_lab.offline import install_offline_guard
from reliability_lab.receiver import Ledger


def journal(directory: Path, event: dict) -> None:
    """Persist observations before the intentional process exit."""
    with (directory / "events.jsonl").open("a") as stream:
        stream.write(json.dumps({"pid": os.getpid(), **event}) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def make_agent(directory: Path, identity: dict, saver: object) -> object:
    """Use actual approval middleware and a model that echoes observed results."""
    from typing import Self
    from deepagents import create_deep_agent
    from langchain.tools import ToolRuntime, tool
    from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
    from langchain_core.messages import AIMessage
    from langchain_core.outputs import ChatGeneration, ChatResult

    class ScriptedModel(GenericFakeChatModel):
        def bind_tools(self, *args: object, **kwargs: object) -> Self:
            return self

        def _generate(self, messages, stop=None, run_manager=None, **kwargs):
            latest = messages[-1]
            if latest.type == "tool":
                journal(directory, {"event": "model_observed_tool", "status": latest.status,
                                    "content": latest.content})
                response = AIMessage(content=latest.content)
            else:
                response = AIMessage(content="", tool_calls=[{
                    "name": "record_action", "args": {"message": identity["original_message"]},
                    "id": "record-call"}])
            return ChatResult(generations=[ChatGeneration(message=response)])

    @tool
    def record_action(message: str, runtime: ToolRuntime) -> str:
        """Record the approved note in the external receiver and return its receipt."""
        operation_id = runtime.config["configurable"]["operation_id"]
        journal(directory, {"event": "tool_enter", "operation_id": operation_id, "message": message})
        receipt, reused = Ledger(directory / "receiver.sqlite", protected=identity["protected"]).record(operation_id, message)
        journal(directory, {"event": "receiver_result", "receipt": json.loads(receipt), "reused": reused})
        marker = directory / "crash-consumed"
        if not marker.exists():
            with marker.open("x") as stream:
                stream.write("committed; intentional exit follows\n")
                stream.flush()
                os.fsync(stream.fileno())
            os._exit(86)
        return receipt

    return create_deep_agent(
        model=ScriptedModel(messages=iter([])), tools=[record_action], checkpointer=saver,
        interrupt_on={"record_action": {"allowed_decisions": ["approve", "edit", "reject"]}},
        system_prompt="Execute the single declared tool request, subject to simulated review.")


def worker(directory: Path, phase: str) -> None:
    """Run exactly one invocation in a fresh process, then export its observation."""
    install_offline_guard()
    journal(directory, {"event": "worker_start", "phase": phase})
    from langgraph.checkpoint.sqlite import SqliteSaver
    from langgraph.types import Command

    identity = json.loads((directory / "identity.json").read_text())
    config = {"configurable": {"thread_id": identity["thread_id"], "operation_id": identity["operation_id"]},
              "recursion_limit": 10}
    inputs = None
    if phase == "initial":
        inputs = {"messages": [{"role": "user", "content": "Record the proposed note once."}]}
    elif phase == "decision":
        decision = {"type": identity["decision"]}
        if identity["decision"] == "edit":
            decision["edited_action"] = {"name": "record_action", "args": {"message": identity["approved_message"]}}
        elif identity["decision"] == "reject":
            decision["message"] = "Simulated reviewer rejected this action; it was not executed."
        journal(directory, {"event": "reviewer_decision", "source": "simulated_reviewer", "decision": decision})
        inputs = Command(resume={"decisions": [decision]})
    with SqliteSaver.from_conn_string(str(directory / "checkpoints.sqlite")) as saver:
        saver.conn.execute("PRAGMA synchronous=FULL")
        agent = make_agent(directory, identity, saver)
        started = time.perf_counter()
        result = agent.invoke(inputs, config, durability="sync")
        duration = time.perf_counter() - started
        snapshot = agent.get_state(config)
        interrupts = [{"id": item.id, "value": item.value} for item in result.get("__interrupt__", [])]
        tool_messages = [message for message in result["messages"] if message.type == "tool"]
        final_tool = tool_messages[-1] if tool_messages else None
        payload = {"pid": os.getpid(), "interrupts": interrupts, "checkpoint_next": list(snapshot.next),
                   "agent_duration_s": duration,
                   "final_tool_status": final_tool.status if final_tool else None,
                   "final_tool_content": final_tool.content if final_tool else None,
                   "answer": result["messages"][-1].content if not interrupts else None}
        (directory / f"{phase}.json").write_text(json.dumps(payload, indent=2) + "\n")


if __name__ == "__main__":
    worker(Path(sys.argv[1]), sys.argv[2])
