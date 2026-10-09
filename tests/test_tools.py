import unicodedata

import pytest
from fastmcp.exceptions import ToolError
from ruts.utils import strip_marks

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
        TEXT,
        groups=("diversity", "basic", "basic"),
        distributions=True,
        readability_preset="fiction",
    )
    assert list(result) == ["diversity", "basic", "warnings"]
    assert result["basic"] == GROUPS["basic"](Analysis(TEXT, Options(distributions=True)))[0]
    fiction = analyze_text(TEXT, groups=("readability",), readability_preset="fiction")
    assert (
        fiction["readability"]
        == GROUPS["readability"](Analysis(TEXT, Options(preset="fiction")))[0]
    )


def test_analyze_text_warnings():
    warnings = analyze_text("The text is in English.", groups=("basic", "diversity"))["warnings"]
    assert warnings[0].startswith("Букв русского алфавита - только 0%")
    assert warnings[1].startswith("Слов в тексте: 5, меньше 50")


def test_analyze_text_errors(monkeypatch):
    with pytest.raises(ToolError, match=r"^The data source has no words$"):
        analyze_text("...")
    monkeypatch.setenv("RUTS_MCP_MAX_TEXT_LENGTH", "10")
    with pytest.raises(ToolError, match="лимит: 10"):
        analyze_text(TEXT)


def test_analyze_text_descriptions():
    result = analyze_text(TEXT, groups=("basic", "style"), descriptions=False)
    full = analyze_text(TEXT, groups=("basic", "style"))
    for group in ("basic", "style"):
        assert all("description" not in item for item in result[group].values())
        assert {
            name: item | {"description": full[group][name]["description"]}
            for name, item in result[group].items()
        } == full[group]


def test_analyze_text_path(tmp_path):
    path = tmp_path / "text.txt"
    path.write_text(TEXT, encoding="utf-8")
    assert analyze_text(path=str(path)) == analyze_text(TEXT)


@pytest.mark.parametrize(
    "text",
    [
        "Ма\u0301ма мы\u0301ла ра\u00adму. Па\u0301па чита\u0301л газе\u0301ту.",
        unicodedata.normalize("NFD", "Мой ёжик. Папа читал газету."),
    ],
    ids=["marks", "nfd"],
)
def test_analyze_text_accents(dicts, text):
    """Ударения, мягкие переносы и NFD не меняют статистик, кроме стиха"""
    groups = tuple(group for group in GROUPS if group != "verse")
    assert analyze_text(text, groups=groups) == analyze_text(strip_marks(text), groups=groups)


def test_analyze_text_no_letters():
    warnings = analyze_text("123 456 7.89 2024", groups=("basic",))["warnings"]
    assert warnings[0].startswith("В тексте нет букв")
