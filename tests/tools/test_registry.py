from warbot.tools.base import Tool
from warbot.tools.registry import ToolRegistry


class DummyTool(Tool):
    name = "dummy"
    description = "A dummy tool"
    parameters = {"type": "object", "properties": {}}

    def execute(self, **kwargs):
        return {"ok": True, "kwargs": kwargs}


def test_registry_register_and_execute():
    registry = ToolRegistry()
    tool = DummyTool()
    registry.register(tool)

    result = registry.execute("dummy", value=1)
    assert result["ok"] is True
    assert result["kwargs"]["value"] == 1


def test_registry_schema():
    registry = ToolRegistry()
    tool = DummyTool()
    registry.register(tool)

    schemas = registry.get_function_schemas()
    assert schemas[0]["type"] == "function"
    assert schemas[0]["function"]["name"] == "dummy"


