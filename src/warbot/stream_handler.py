"""Streaming response handling with thinking/content/tool parsing."""

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any, Callable, Optional


ThinkingCallback = Callable[[str], None]
ContentCallback = Callable[[str], None]
ToolCallCallback = Callable[[dict[str, Any]], None]
FinishCallback = Callable[[Optional[str]], None]


@dataclass
class ToolCallBuilder:
    """Accumulates partial tool call deltas into a full payload."""

    id: str
    index: Optional[int] = None
    type: str = "function"
    function_name: str = ""
    arguments: list[str] = field(default_factory=list)

    def update(self, delta: Any) -> None:
        # Handle both object-like deltas and dict-like deltas
        if isinstance(delta, dict):
            if not self.id and delta.get("id"):
                self.id = delta.get("id") or self.id
            if self.index is None and delta.get("index") is not None:
                self.index = delta.get("index")
            fn = delta.get("function", {}) or {}
            name = fn.get("name")
            args = fn.get("arguments")
            if name:
                self.function_name = name
            if args:
                self.arguments.append(args)
            return

        if getattr(delta, "function", None):
            fn = delta.function
            if not self.id and getattr(delta, "id", None):
                self.id = getattr(delta, "id")
            if self.index is None and getattr(delta, "index", None) is not None:
                self.index = getattr(delta, "index")
            if getattr(fn, "name", None):
                self.function_name = fn.name or self.function_name
            if getattr(fn, "arguments", None):
                self.arguments.append(fn.arguments)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id or "call",
            "type": self.type,
            "function": {
                "name": self.function_name or "unknown_function",
                "arguments": "".join(self.arguments),
            },
        }


class StreamHandler:
    """Parse OpenAI streaming responses, surfacing thinking/content/tool updates."""

    def __init__(
        self,
        on_thinking: ThinkingCallback,
        on_content: ContentCallback,
        on_tool_call: ToolCallCallback,
        on_finish: Optional[FinishCallback] = None,
        on_debug: Optional[Callable[[Any], None]] = None,
    ) -> None:
        self.on_thinking = on_thinking
        self.on_content = on_content
        self.on_tool_call = on_tool_call
        self.on_finish = on_finish
        self.on_debug = on_debug

    def handle_stream(self, stream: Iterable[Any]) -> None:
        """Iterate over streamed chunks and dispatch callbacks."""
        tool_calls: dict[str, ToolCallBuilder] = defaultdict(lambda: ToolCallBuilder(id=""))

        for chunk in stream:
            if not chunk.choices:
                if self.on_debug:
                    self.on_debug("Received chunk with no choices")
                continue
            choice = chunk.choices[0]
            delta = choice.delta

            # Debug: log delta fields and content
            if self.on_debug:
                delta_attrs = [attr for attr in dir(delta) if not attr.startswith("_")]
                delta_dict = {
                    k: getattr(delta, k, None)
                    for k in delta_attrs
                    if not callable(getattr(delta, k, None))
                }

                # Log specific delta content
                if hasattr(delta, "thinking") and delta.thinking:
                    self.on_debug(f"Thinking delta: {delta.thinking}")
                if hasattr(delta, "tool_calls") and delta.tool_calls:
                    self.on_debug(f"Tool calls delta: {len(delta.tool_calls)} call(s)")
                if choice.finish_reason:
                    self.on_debug(f"Finish reason: {choice.finish_reason}")

            # Check for thinking at multiple levels (delta, choice, chunk)
            # Some models may put thinking in different places
            self._emit_thinking(delta, choice, chunk)
            self._emit_content(delta)
            self._collect_tool_calls(delta, tool_calls)

            if choice.finish_reason:
                if choice.finish_reason == "tool_calls":
                    self._emit_tool_calls(tool_calls)
                if self.on_finish:
                    self.on_finish(choice.finish_reason)
                tool_calls.clear()

    def _emit_thinking(self, delta: Any, choice: Any = None, chunk: Any = None) -> None:
        """
        Check multiple possible field names and locations for thinking/reasoning.
        gpt-5-mini and other thinking models may use different field names or locations.
        """
        thinking = None

        # Check delta first (most common location)
        for field_name in ["thinking", "reasoning", "reasoning_content", "internal_monologue"]:
            if hasattr(delta, field_name):
                thinking = getattr(delta, field_name)
                if thinking:
                    break

        # Also check if it's a dict-like object
        if not thinking and isinstance(delta, dict):
            for field_name in ["thinking", "reasoning", "reasoning_content", "internal_monologue"]:
                thinking = delta.get(field_name)
                if thinking:
                    break

        # Check choice level (some models put thinking here)
        if not thinking and choice:
            for field_name in ["thinking", "reasoning", "reasoning_content", "internal_monologue"]:
                if hasattr(choice, field_name):
                    thinking = getattr(choice, field_name)
                    if thinking:
                        break

        # Check chunk level (less common but possible)
        if not thinking and chunk:
            for field_name in ["thinking", "reasoning", "reasoning_content", "internal_monologue"]:
                if hasattr(chunk, field_name):
                    thinking = getattr(chunk, field_name)
                    if thinking:
                        break

        if not thinking:
            return

        # thinking may be str or list; normalize to str
        if isinstance(thinking, list):
            text = "".join([t if isinstance(t, str) else str(t) for t in thinking])
        else:
            text = str(thinking)
        if text:
            self.on_thinking(text)

    def _emit_content(self, delta: Any) -> None:
        content = getattr(delta, "content", None)
        if not content:
            return

        # content can be a list of text parts or a string
        if isinstance(content, list):
            text_parts = []
            for part in content:
                if isinstance(part, str):
                    text_parts.append(part)
                elif isinstance(part, dict):
                    text_parts.append(part.get("text", ""))
                elif hasattr(part, "text"):
                    text_parts.append(getattr(part, "text", ""))
            text = "".join(text_parts)
        else:
            text = str(content)
        if text:
            self.on_content(text)

    def _collect_tool_calls(
        self,
        delta: Any,
        tool_calls: dict[str, ToolCallBuilder],
    ) -> None:
        calls = getattr(delta, "tool_calls", None)
        if not calls:
            return

        for idx, call in enumerate(calls):
            call_id = getattr(call, "id", None)
            call_type = getattr(call, "type", None)
            call_index = getattr(call, "index", None)

            if call_id is None and isinstance(call, dict):
                call_id = call.get("id")
            if call_type is None and isinstance(call, dict):
                call_type = call.get("type")
            if call_index is None and isinstance(call, dict):
                call_index = call.get("index")

            key: Optional[str] = call_id
            if key is None and call_index is not None:
                # Try to merge with existing builder by index
                for existing_key, builder in tool_calls.items():
                    if builder.index == call_index:
                        key = existing_key
                        break
            if key is None:
                key = f"idx_{call_index}" if call_index is not None else f"call_{idx}"

            if key not in tool_calls:
                tool_calls[key] = ToolCallBuilder(
                    id=call_id or key,
                    index=call_index,
                    type=call_type or "function",
                )

            builder = tool_calls[key]
            builder.update(call)

    def _emit_tool_calls(self, tool_calls: dict[str, ToolCallBuilder]) -> None:
        for builder in tool_calls.values():
            self.on_tool_call(builder.to_dict())
