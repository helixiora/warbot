"""Tools package initialization and registry helpers."""

from .registry import ToolRegistry

registry = ToolRegistry()

register_tool = registry.register
execute_tool = registry.execute
list_tools = registry.list_tools
get_function_schemas = registry.get_function_schemas


