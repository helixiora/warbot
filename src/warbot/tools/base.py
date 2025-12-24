"""Base tool interface for warbot tools."""

from abc import ABC, abstractmethod
from typing import Any, Dict


class Tool(ABC):
    """Abstract base class for all tools."""

    name: str
    description: str
    parameters: Dict[str, Any]

    @abstractmethod
    def execute(self, **kwargs: Any) -> Any:  # pragma: no cover - interface
        """Execute the tool with provided arguments."""
        raise NotImplementedError

    def to_function_schema(self) -> Dict[str, Any]:
        """Return OpenAI function tool schema (chat completions shape)."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


