import pytest

from ruts_mcp.settings import Settings


def test_defaults():
    assert Settings.from_env({}) == Settings()
    assert Settings().max_text_length == 500_000


def test_from_os_environ(monkeypatch):
    monkeypatch.setenv("RUTS_MCP_MAX_TEXT_LENGTH", "1000")
    assert Settings.from_env().max_text_length == 1000


@pytest.mark.parametrize("value", ["", "abc", "1.5", "0", "-3"])
def test_invalid(value):
    with pytest.raises(ValueError, match=r"^RUTS_MCP_MAX_TEXT_LENGTH must be a positive integer"):
        Settings.from_env({"RUTS_MCP_MAX_TEXT_LENGTH": value})
