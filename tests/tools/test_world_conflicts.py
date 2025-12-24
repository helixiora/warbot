from warbot.tools.world_conflicts import WorldConflictsTool


def test_world_conflicts_returns_conflicts():
    tool = WorldConflictsTool()
    result = tool.execute()
    assert "conflicts" in result
    assert isinstance(result["conflicts"], list)


