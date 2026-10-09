import threading
from types import SimpleNamespace

import pytest
from fastmcp.exceptions import ToolError

from ruts_mcp import inputs
from ruts_mcp.inputs import (
    check_length,
    load_ruts,
    normalize,
    prepare_text,
    read_file,
    read_source,
)


def test_load_ruts_concurrent(monkeypatch):
    monkeypatch.setattr(inputs, "_imported", False)
    calls = []
    monkeypatch.setattr(inputs, "importlib", SimpleNamespace(import_module=calls.append))
    threads = [threading.Thread(target=load_ruts) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert calls == list(inputs.RUTS_MODULES)
    load_ruts()
    assert len(calls) == len(inputs.RUTS_MODULES)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Моро́з", "Мороз"),
        ("со­лнце", "солнце"),
        ("ёж", "ёж"),
        ("Да\r\nнет\rда", "Да\nнет\nда"),
        ("Мороз и солнце", "Мороз и солнце"),
    ],
    ids=["accent", "soft-hyphen", "combining-yo", "newlines", "plain"],
)
def test_normalize(text, expected):
    assert normalize(text) == expected


def test_check_length(monkeypatch):
    monkeypatch.setenv("RUTS_MCP_MAX_TEXT_LENGTH", "1000")
    check_length(1000, "Корпус A")
    with pytest.raises(
        ToolError, match=r"^Корпус A длиннее лимита сервера \(символов: 1001, лимит: 1000\)"
    ):
        check_length(1001, "Корпус A")


def test_prepare_text(monkeypatch):
    monkeypatch.setenv("RUTS_MCP_MAX_TEXT_LENGTH", "10")
    assert prepare_text("Моро́з") == "Мороз"
    with pytest.raises(ToolError, match=r"^Эталон длиннее лимита"):
        prepare_text("а" * 11, "Эталон")
    assert prepare_text("а" * 11, check=False) == "а" * 11


def test_prepare_text_surrogate():
    with pytest.raises(ToolError, match=r"^Текст поврежден: в нем есть одиночные суррогатные"):
        prepare_text("Привет \ud800 мир")


def test_read_file(tmp_path, monkeypatch):
    path = tmp_path / "text.txt"
    path.write_text("Мама мыла раму", encoding="utf-8")
    assert read_file(str(path)) == "Мама мыла раму"
    monkeypatch.setenv("HOME", str(tmp_path))
    assert read_file("~/text.txt") == "Мама мыла раму"


@pytest.mark.parametrize(
    ("name", "content", "message"),
    [
        ("missing.txt", None, r"^Текст: не удалось прочитать файл .*missing\.txt - "),
        (
            "cp1251.txt",
            "Мама".encode("cp1251"),
            r"^Текст: файл .*cp1251\.txt не в кодировке UTF-8$",
        ),
        (
            "big.txt",
            b"a" * 41,
            r"^Текст: файл .*big\.txt больше лимита сервера \(41 байт при лимите 10",
        ),
    ],
    ids=["missing", "not-utf8", "too-big"],
)
def test_read_file_errors(tmp_path, monkeypatch, name, content, message):
    monkeypatch.setenv("RUTS_MCP_MAX_TEXT_LENGTH", "10")
    path = tmp_path / name
    if content is not None:
        path.write_bytes(content)
    with pytest.raises(ToolError, match=message):
        read_file(str(path))


def test_read_file_relative():
    with pytest.raises(ToolError, match=r"^Эталон: путь text\.txt относительный"):
        read_file("text.txt", "Эталон")


def test_read_source(tmp_path):
    path = tmp_path / "text.txt"
    path.write_text("Моро́з\r\n", encoding="utf-8")
    assert read_source("", str(path)) == "Мороз\n"
    assert read_source("Мороз", None) == "Мороз"


@pytest.mark.parametrize(
    ("text", "path", "message"),
    [
        ("Мороз", "/tmp/text.txt", r"^Текст: задайте или текст, или путь к файлу, но не оба$"),
        ("", None, r"^Текст не задан: передайте текст или путь к файлу$"),
    ],
    ids=["both", "none"],
)
def test_read_source_errors(text, path, message):
    with pytest.raises(ToolError, match=message):
        read_source(text, path)
