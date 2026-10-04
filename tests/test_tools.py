import pytest
from fastmcp.exceptions import ToolError

from ruts_mcp.analysis import Analysis, Options
from ruts_mcp.groups import GROUPS
from ruts_mcp.tools import analyze_text

TEXT = "Мама мыла раму. Папа читал газету."


def test_analyze_text():
    analysis = Analysis(TEXT)
    basic, _ = GROUPS["basic"](analysis)
    readability, readability_warnings = GROUPS["readability"](analysis)
    assert analyze_text(TEXT) == {
        "basic": basic,
        "readability": readability,
        "warnings": readability_warnings,
    }


def test_analyze_text_options():
    result = analyze_text(
        TEXT, ("diversity", "basic", "basic"), distributions=True, readability_preset="fiction"
    )
    assert list(result) == ["diversity", "basic", "warnings"]
    assert result["basic"] == GROUPS["basic"](Analysis(TEXT, Options(distributions=True)))[0]
    fiction = analyze_text(TEXT, ("readability",), readability_preset="fiction")
    assert (
        fiction["readability"]
        == GROUPS["readability"](Analysis(TEXT, Options(preset="fiction")))[0]
    )


def test_analyze_text_warnings():
    warnings = analyze_text("The text is in English.", ("basic", "diversity"))["warnings"]
    assert warnings[0].startswith("Букв русского алфавита - только 0%")
    assert warnings[1].startswith("Слов в тексте: 5, меньше 50")


def test_analyze_text_errors(monkeypatch):
    with pytest.raises(ToolError, match=r"^The data source has no words$"):
        analyze_text("...")
    monkeypatch.setenv("RUTS_MCP_MAX_TEXT_LENGTH", "10")
    with pytest.raises(ToolError, match="лимит: 10"):
        analyze_text(TEXT)
