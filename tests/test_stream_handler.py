from warbot.stream_handler import StreamHandler


class Delta:
    def __init__(self, thinking=None, content=None, tool_calls=None):
        self.thinking = thinking
        self.content = content
        self.tool_calls = tool_calls


class Choice:
    def __init__(self, delta, finish_reason=None):
        self.delta = delta
        self.finish_reason = finish_reason


class Chunk:
    def __init__(self, delta, finish_reason=None):
        self.choices = [Choice(delta, finish_reason)]


def test_stream_handler_emits_thinking_and_content():
    thinking_parts = []
    content_parts = []

    handler = StreamHandler(
        on_thinking=lambda t: thinking_parts.append(t),
        on_content=lambda c: content_parts.append(c),
        on_tool_call=lambda _: None,
        on_finish=None,
    )

    stream = [
        Chunk(Delta(thinking="thought", content=["hello "], tool_calls=None)),
        Chunk(Delta(thinking=None, content=["world"], tool_calls=None), finish_reason="stop"),
    ]

    handler.handle_stream(stream)

    assert "".join(thinking_parts) == "thought"
    assert "".join(content_parts) == "hello world"


