import pytest
from fastmcp.exceptions import ToolError

from ruts_mcp.stats import basic_stats
from ruts_mcp.tools import analyze_text

TEXT = "Мама мыла раму. Папа читал газету."


def test_analyze_text():
    assert analyze_text(TEXT) == {"basic": basic_stats(TEXT), "warnings": []}
    assert analyze_text(TEXT, ("basic", "basic"), distributions=True) == {
        "basic": basic_stats(TEXT, distributions=True),
        "warnings": [],
    }


def test_analyze_text_warnings():
    assert analyze_text("The text is in English.")["warnings"]


def test_analyze_text_errors(monkeypatch):
    with pytest.raises(ToolError, match=r"^The data source has no words$"):
        analyze_text("...")
    monkeypatch.setenv("RUTS_MCP_MAX_TEXT_LENGTH", "10")
    with pytest.raises(ToolError, match="лимит: 10"):
        analyze_text(TEXT)
