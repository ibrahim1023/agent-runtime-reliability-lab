"""Original lab Recorder class, extracted without executing the live runner."""

import json
from pathlib import Path
from typing import Any

from langchain_core.callbacks import BaseCallbackHandler


class Recorder(BaseCallbackHandler):
    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self.calls = []
        self.results = []
        self.steps = 0
        self.input_tokens = 0
        self.output_tokens = 0

    def save(self, event: dict[str, Any]) -> None:
        with (self.directory / "events.jsonl").open("a") as stream:
            stream.write(json.dumps(event, default=str) + "\n")
            stream.flush()

    def on_tool_start(self, serialized: dict[str, Any], input_str: str, **kwargs: Any) -> None:
        record = {"name": serialized.get("name"), "input": input_str, "args": kwargs.get("inputs"), "run_id": str(kwargs.get("run_id"))}
        self.calls.append(record)
        self.save({"event": "tool_start", **record})

    def on_tool_end(self, output: Any, **kwargs: Any) -> None:
        record = {"name": getattr(output, "name", None), "status": getattr(output, "status", None), "content": getattr(output, "content", str(output)), "tool_call_id": getattr(output, "tool_call_id", None), "run_id": str(kwargs.get("run_id"))}
        self.results.append(record)
        self.save({"event": "tool_result", **record})

    def on_llm_end(self, response: Any, **kwargs: Any) -> None:
        self.steps += 1
        for group in response.generations:
            for generation in group:
                message = generation.message
                usage = message.usage_metadata or {}
                self.input_tokens += usage.get("input_tokens", 0)
                self.output_tokens += usage.get("output_tokens", 0)
                self.save({"event": "model_response", "text": message.content, "tool_calls": message.tool_calls, "usage": usage, "finish_reason": message.response_metadata.get("finish_reason")})
