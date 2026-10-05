from pathlib import Path

import pytest
from platformdirs import user_data_dir

from ruts_mcp.settings import DEFAULT_DATA_DIR, Settings


def test_defaults():
    assert Settings.from_env({}) == Settings()
    assert Settings().max_text_length == 500_000
    assert Settings().data_dir == Path(user_data_dir("ruts-mcp", appauthor=False))


@pytest.mark.parametrize(
    ("value", "expected"),
    [("~/ruts_data", Path.home().resolve() / "ruts_data"), ("", DEFAULT_DATA_DIR)],
)
def test_data_dir(value, expected):
    """Каталог данных задает переменная ruTS RUTS_DATA_DIR, пустая - не задает"""
    assert Settings.from_env({"RUTS_DATA_DIR": value}).data_dir == expected


def test_from_os_environ(monkeypatch):
    monkeypatch.setenv("RUTS_MCP_MAX_TEXT_LENGTH", "1000")
    assert Settings.from_env().max_text_length == 1000


@pytest.mark.parametrize("value", ["", "abc", "1.5", "0", "-3"])
def test_invalid(value):
    with pytest.raises(
        ValueError, match=r"^RUTS_MCP_MAX_TEXT_LENGTH должна быть целым положительным числом"
    ):
        Settings.from_env({"RUTS_MCP_MAX_TEXT_LENGTH": value})
