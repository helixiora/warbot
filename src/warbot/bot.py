"""Core warbot logic with streaming, tools, and conversation history."""

from __future__ import annotations

import json
import logging
import sys
from typing import Any, Dict, List, Optional

from openai import OpenAI
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from .config import Settings, build_client, load_settings
from .stream_handler import StreamHandler
from .tools import get_function_schemas, register_tool, registry
from .tools.location_risks import LocationRisksTool
from .tools.preparation_guidance import PreparationGuidanceTool
from .tools.world_conflicts import WorldConflictsTool


SYSTEM_PROMPT = (
    "You are an assistant that helps users understand major world conflicts, assess risks "
    "for specific locations, and prepare for emergency scenarios such as utilities interruption, "
    "internet loss, and armed conflict. Be concise, clear, and prioritize actionable guidance.\n\n"
    "CRITICAL RULES FOR TOOL USAGE:\n"
    "1. When you receive tool results, interpret the JSON data and present it in a clear, "
    "human-readable format. Do NOT dump raw JSON.\n"
    "2. You MUST ONLY use information from the tool results. NEVER supplement with your own "
    "knowledge or add information not present in the tool results.\n"
    "3. If the tool returns limited data, present ONLY what the tool returned in a formatted way. "
    "Do not add conflicts, details, or information from your training data.\n"
    "4. Format the tool data nicely (use bullet points, clear structure, etc.) but only include "
    "the exact data from the tool results."
)


class Warbot:
    """Warbot with streaming and tool usage."""

    def __init__(
        self,
        settings: Optional[Settings] = None,
        console: Optional[Console] = None,
        debug: bool = False,
    ) -> None:
        self.settings = settings or load_settings()
        self.console = console or Console()
        self.client: OpenAI = build_client(self.settings)
        self.history: List[Dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}]
        self.debug = debug
        
        # Set up logger for debug mode
        self.logger = logging.getLogger("warbot")
        if debug:
            logging.basicConfig(
                level=logging.DEBUG,
                format="[%(levelname)s] %(message)s",
            )
        
        self._register_default_tools()

    def _register_default_tools(self) -> None:
        register_tool(WorldConflictsTool())
        register_tool(LocationRisksTool())
        register_tool(PreparationGuidanceTool())

    def _build_input(self) -> List[Dict[str, Any]]:
        return self.history

    def _log_thinking(self, text: str) -> None:
        if text:
            # Display thinking with a visible prefix and better formatting
            thinking_text = Text(f"💭 {text}", style="dim italic")
            self.console.print(thinking_text, end="")
            sys.stdout.flush()  # Flush to ensure immediate display

    def _log_content(self, text: str) -> None:
        if text:
            self.console.print(text, end="", highlight=False)
            sys.stdout.flush()  # Flush to ensure immediate display

    def _log_tool_call(self, call: Dict[str, Any]) -> None:
        summary = f"[tool] {call.get('function', {}).get('name', '')}"
        self.console.print(Panel(summary, style="cyan"))

    def send_message(self, user_input: str) -> str:
        """Send a user message, handle streaming, and return final assistant content."""
        self.history.append({"role": "user", "content": user_input})

        while True:
            assistant_chunks: List[str] = []
            tool_calls: List[Dict[str, Any]] = []
            finish_reason: Optional[str] = None
            has_tool_calls = False

            def _on_tool_call(call: Dict[str, Any]) -> None:
                nonlocal has_tool_calls
                has_tool_calls = True
                tool_calls.append(call)
                self._log_tool_call(call)

            def _on_finish(reason: Optional[str]) -> None:
                nonlocal finish_reason
                finish_reason = reason

            # Display content as it streams, but stop if tool calls are detected
            def _on_content(text: str) -> None:
                assistant_chunks.append(text)
                # Only display if no tool calls have been detected yet
                if not has_tool_calls:
                    self._log_content(text)

            handler = StreamHandler(
                on_thinking=self._log_thinking,
                on_content=_on_content,
                on_tool_call=_on_tool_call,
                on_finish=_on_finish,
                on_debug=self.logger.debug if self.debug else None,
            )

            if self.debug:
                self.logger.debug(f"Sending request to model: {self.settings.model}")
            
            stream = self.client.chat.completions.create(
                model=self.settings.model,
                messages=self._build_input(),
                tools=get_function_schemas(),
                stream=True,
            )

            handler.handle_stream(stream)

            if tool_calls or finish_reason == "tool_calls":
                if self.debug:
                    self.logger.debug(f"Tool calls detected: {len(tool_calls)} call(s)")
                # Tool calls were made - don't save content from this response
                # The model should generate a new response using tool results
                assistant_tool_message = self._format_assistant_tool_message(tool_calls)
                self.history.append(assistant_tool_message)

                tool_messages = self._execute_tool_calls(tool_calls)
                self.history.extend(tool_messages)
                continue  # ask model again with tool results

            # No tool calls - save the content
            content = "".join(assistant_chunks)
            self.history.append({"role": "assistant", "content": content})
            return content

    def _format_assistant_tool_message(self, tool_calls: List[Dict[str, Any]]) -> Dict[str, Any]:
        formatted_calls = []
        for call in tool_calls:
            formatted_calls.append(
                {
                    "id": call["id"],
                    "type": call.get("type", "function"),
                    "function": {
                        "name": call["function"]["name"],
                        "arguments": call["function"]["arguments"],
                    },
                }
            )
        return {"role": "assistant", "tool_calls": formatted_calls}

    def _execute_tool_calls(self, tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        messages: List[Dict[str, Any]] = []
        for call in tool_calls:
            fn = call["function"]
            name = fn["name"]
            try:
                args = json.loads(fn["arguments"] or "{}")
            except json.JSONDecodeError:
                args = {}
            if self.debug:
                self.logger.debug(f"Executing tool: {name} with args: {args}")
            result = registry.execute(name, **args)
            
            if self.debug:
                self.logger.debug(f"Tool {name} returned: {json.dumps(result, indent=2)}")
            
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call["id"],
                    "name": name,
                    "content": json.dumps(result),
                }
            )
        return messages


