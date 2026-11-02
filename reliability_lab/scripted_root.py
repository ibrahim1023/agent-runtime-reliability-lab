"""One opt-in real-runtime fixture with a scripted model and no provider calls."""

from datetime import datetime, timezone
import hashlib
import importlib
import importlib.metadata
import json
from pathlib import Path
import sys
import uuid

from reliability_lab.evidence import checked_bytes, require
from reliability_lab.offline import install_offline_guard


def check_extractions(root: Path) -> None:
    """Check the extracted lab components before loading optional dependencies."""
    manifest = json.loads((root / "results/manifest.json").read_text())
    for entry in manifest["scripted_runtime_extractions"]:
        checked_bytes(root, entry["destination"], entry["destination_sha256"])


def runtime_identity() -> dict:
    """Record installed versions and selected loaded-source bytes, without paths."""
    packages = ("deepagents", "langchain", "langchain-core", "langgraph", "langgraph-prebuilt", "langsmith")
    modules = ("deepagents.graph", "deepagents.backends.state", "deepagents.backends.utils",
               "langchain.agents.factory", "langgraph.prebuilt.tool_node")
    fingerprints = {}
    for name in modules:
        module = importlib.import_module(name)
        fingerprints[name] = hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest()
    return {"python": sys.version.split()[0],
            "packages": {name: importlib.metadata.version(name) for name in packages},
            "selected_loaded_module_sha256": fingerprints,
            "scope": "Selected loaded modules, not a complete dependency lock or historical execution identity"}


def run_condition(directory: Path, *, corrected: bool) -> dict:
    """Run the reused fixture, retaining the original and actual tool requests."""
    from typing import Self
    from deepagents import create_deep_agent
    from deepagents.backends import StateBackend
    from deepagents.backends.utils import create_file_data, file_data_to_string
    from langchain_core.callbacks import BaseCallbackHandler
    from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
    from langchain_core.messages import AIMessage
    from reliability_lab.runtime.conservative_middleware import StateFilesystemRecoveryMiddleware
    from reliability_lab.runtime.recorder import Recorder

    class ScriptedModel(GenericFakeChatModel):
        def bind_tools(self, *args: object, **kwargs: object) -> Self:
            return self

    class ModelInputs(BaseCallbackHandler):
        def __init__(self) -> None:
            self.tool_inputs = []

        def on_chat_model_start(self, serialized, messages, **kwargs) -> None:
            self.tool_inputs.extend(message.content for batch in messages for message in batch if message.type == "tool")

    directory.mkdir()
    recorder, inputs = Recorder(directory), ModelInputs()
    model = ScriptedModel(messages=iter([
        AIMessage(content="", tool_calls=[{"name": "glob", "args": {"path": "", "pattern": "*.txt"}, "id": "root-call"}]),
        AIMessage(content="done"),
    ]))
    middleware = StateFilesystemRecoveryMiddleware() if corrected else None
    agent = create_deep_agent(model=model, backend=StateBackend(), middleware=[middleware] if middleware else [])
    files = {"/incoming/data.txt": "found"}
    result = agent.invoke({"messages": [{"role": "user", "content": "Run the declared contract check."}],
                           "files": {path: create_file_data(value) for path, value in files.items()}},
                          {"callbacks": [recorder, inputs], "recursion_limit": 10})
    proposal = next(message.tool_calls[0] for message in result["messages"] if message.type == "ai" and message.tool_calls)
    require(len(recorder.calls) == len(recorder.results) == 1, "Expected exactly one executed tool")
    tool_result = {key: recorder.results[0][key] for key in ("name", "status", "content")}
    return {"condition": "conservative" if corrected else "baseline",
            "conversation_proposal": {key: proposal[key] for key in ("name", "args")},
            "actual_tool_args": recorder.calls[0]["args"], "tool_result": tool_result,
            "next_model_received_tool_result": tool_result["content"] in inputs.tool_inputs,
            "files_unchanged": {path: file_data_to_string(value) for path, value in result["files"].items()} == files,
            "scripted_model_responses": recorder.steps,
            "middleware_events": middleware.events if middleware else []}


def run_scripted_root(root: Path) -> tuple[dict, int]:
    """Execute two conditions of one fixture; keep them outside verify-offline."""
    install_offline_guard()
    attempt = Path("work/scripted-root") / uuid.uuid4().hex
    directory = root / attempt
    directory.mkdir(parents=True, exist_ok=False)
    report = {"schema_version": 1, "kind": "fresh scripted graph execution; no live-model evaluation",
              "started_at_utc": datetime.now(timezone.utc).isoformat(), "live_model_calls": 0,
              "learner_prediction": "not supplied; learner requested immediate execution",
              "assistant_hypothesis": "Execution arguments can change while the original proposal remains in history.",
              "network": "Tracing disabled and Python socket operations blocked before runtime imports; not an OS sandbox",
              "report_path": str(attempt / "report.json"), "conditions": []}
    code = 1
    try:
        check_extractions(root)
        report["runtime_identity"] = runtime_identity()
        report["conditions"] = [run_condition(directory / label, corrected=corrected)
                                for label, corrected in (("baseline", False), ("conservative", True))]
        baseline, corrected = report["conditions"]
        require(baseline["actual_tool_args"]["path"] == "", "Baseline did not preserve the proposed empty path")
        require(corrected["conversation_proposal"]["args"]["path"] == "", "Original proposal was rewritten")
        require(corrected["actual_tool_args"] == {"path": "/", "pattern": "*.txt"}, "Corrected tool did not receive root")
        require(corrected["tool_result"]["status"] == "success" and
                "/incoming/data.txt" in corrected["tool_result"]["content"], "Corrected search did not find source")
        require(all(c["files_unchanged"] and c["next_model_received_tool_result"] for c in report["conditions"]),
                "Fixture changed files or tool observation did not reach the next model input")
        report["status"] = "passed"
        code = 0
    except (ImportError, OSError, ValueError, TypeError, KeyError, StopIteration) as exc:
        report["status"] = "failed"
        report["error_type"] = type(exc).__name__
        report["error"] = "Runtime fixture failed; verify optional dependencies and the recorded contract."
    report["exit_code"] = code
    report["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
    (directory / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    return report, code
