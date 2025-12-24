"""Tool registry for managing and executing tools."""

from collections.abc import Iterable
from typing import Any

from .base import Tool


class ToolRegistry:
    """Registry for tool discovery, schema export, and execution."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Register a tool instance."""
        self._tools[tool.name] = tool

    def list_tools(self) -> Iterable[Tool]:
        return self._tools.values()

    def get_function_schemas(self) -> list[dict[str, Any]]:
        """Return OpenAI function schemas for all registered tools."""
        return [tool.to_function_schema() for tool in self._tools.values()]

    def execute(self, name: str, **kwargs: Any) -> Any:
        """Execute a tool by name."""
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' is not registered.")
        return self._tools[name].execute(**kwargs)
