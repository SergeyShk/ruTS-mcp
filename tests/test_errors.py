import pytest
from fastmcp.exceptions import ToolError
from ruts import BasicStats, SourceError

from ruts_mcp.errors import check_text, ruts_errors


def test_ruts_errors():
    with pytest.raises(ToolError, match=r"^The data source has no words$") as info, ruts_errors():
        BasicStats("")
    assert isinstance(info.value.__cause__, SourceError)


def test_other_errors_pass():
    with pytest.raises(ZeroDivisionError), ruts_errors():
        _ = 1 / 0


def test_check_text(monkeypatch):
    monkeypatch.setenv("RUTS_MCP_MAX_TEXT_LENGTH", "1000")
    check_text("а" * 1000)
    with pytest.raises(
        ToolError, match=r"^Текст длиннее лимита сервера \(символов: 1001, лимит: 1000\)"
    ):
        check_text("а" * 1001)
