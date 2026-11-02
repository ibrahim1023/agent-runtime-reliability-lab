"""Conservative application-level recovery context for an unfiltered StateBackend."""

from collections.abc import Callable

from langchain.agents.middleware import AgentMiddleware
from langchain.agents.middleware.types import ToolCallRequest
from langchain_core.messages import ToolMessage
from langgraph.types import Command


class StateFilesystemRecoveryMiddleware(AgentMiddleware):
    """Correct virtual root aliases and report proven empty thread state.

    Only use with an unfiltered StateBackend whose complete files mapping is in
    graph state. Empty graph files do not establish a remote filesystem is empty.
    """

    def __init__(self) -> None:
        self.events: list[dict[str, str]] = []

    def wrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], ToolMessage | Command],
    ) -> ToolMessage | Command:
        """Preserve model guidance and tool access; correct only observations."""
        name = request.tool_call["name"]
        args = request.tool_call["args"]
        if name in {"ls", "glob", "grep"} and args.get("path") in {"", ".", "./", "/."}:
            self.events.append({"event": "root_alias", "tool": name, "original_path": args["path"]})
            request = request.override(tool_call={**request.tool_call, "args": {**args, "path": "/"}})
        result = handler(request)
        if name in {"read_file", "ls", "glob", "grep"} and request.state.get("files") == {} and isinstance(result, ToolMessage):
            note = (
                "Workspace context: this workspace currently contains zero files. "
                "More listing or searching here cannot locate the input until files are provided. "
                "Ask for the source content or a populated source location."
            )
            self.events.append({"event": "empty_workspace", "tool": name})
            return result.model_copy(update={"content": f"{result.content}\n{note}"})
        return result
