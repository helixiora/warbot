from warbot.tools.preparation_guidance import PreparationGuidanceTool


def test_preparation_guidance_has_sections():
    tool = PreparationGuidanceTool()
    result = tool.execute("utilities interruption", location="Test City")
    assert "immediate_actions" in result
    assert "short_term" in result
    assert "long_term" in result


