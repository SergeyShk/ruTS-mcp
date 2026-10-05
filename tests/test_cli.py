import importlib
import runpy
import sys
from importlib.metadata import version

import pytest
from ruts.datasets import FreqDict, StressDict
from ruts.exceptions import DownloadError

import ruts_mcp
from ruts_mcp.cli import main
from ruts_mcp.server import mcp


@pytest.fixture
def runs(monkeypatch):
    calls = []
    monkeypatch.setattr(mcp, "run", lambda **kwargs: calls.append(kwargs))
    return calls


def test_version(capsys):
    with pytest.raises(SystemExit) as info:
        main(["--version"])
    assert info.value.code == 0
    assert capsys.readouterr().out == f"ruts-mcp {ruts_mcp.__version__}, ruts {version('ruts')}\n"


def test_run(runs):
    main([])
    assert runs == [{"show_banner": False}]


def test_invalid_settings(monkeypatch, runs, capsys):
    monkeypatch.setenv("RUTS_MCP_MAX_TEXT_LENGTH", "many")
    with pytest.raises(SystemExit) as info:
        main([])
    assert info.value.code == 2
    assert (
        "RUTS_MCP_MAX_TEXT_LENGTH должна быть целым положительным числом, получено 'many'"
        in capsys.readouterr().err
    )
    assert runs == []


def test_module(monkeypatch, runs):
    monkeypatch.setattr(sys, "argv", ["ruts_mcp"])
    monkeypatch.delitem(sys.modules, "ruts_mcp.__main__", raising=False)
    runpy.run_module("ruts_mcp", run_name="__main__")
    assert runs == [{"show_banner": False}]


def test_module_import(runs):
    importlib.import_module("ruts_mcp.__main__")
    assert runs == []


@pytest.fixture
def downloads(monkeypatch):
    """Загрузка словарей без сети: записывает пустой файл словаря и запоминает force"""
    calls = []

    def download(self, force=False):
        calls.append((type(self).__name__, force))
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._filepath.touch()

    monkeypatch.setattr(FreqDict, "download", download)
    monkeypatch.setattr(StressDict, "download", download)
    return calls


def test_download(downloads, runs, capsys, data_dir):
    main(["download"])
    assert capsys.readouterr().out.splitlines() == [
        f"Каталог словарей: {data_dir / 'dicts'}",
        "Частотный словарь Ляшевской и Шарова: скачивается...",
        "Частотный словарь Ляшевской и Шарова: скачан",
        "Словарь ударений Козиева: скачивается...",
        "Словарь ударений Козиева: скачан",
    ]
    main(["download"])
    assert capsys.readouterr().out.splitlines()[1:] == [
        "Частотный словарь Ляшевской и Шарова: уже скачан",
        "Словарь ударений Козиева: уже скачан",
    ]
    main(["download", "--force"])
    assert downloads == [
        ("FreqDict", False),
        ("StressDict", False),
        ("FreqDict", True),
        ("StressDict", True),
    ]
    assert runs == []


def test_download_error(monkeypatch, capsys):
    def fail(self, force=False):
        raise DownloadError("Cannot download the file http://dict.ruslang.ru/Freq2011.zip")

    monkeypatch.setattr(FreqDict, "download", fail)
    with pytest.raises(SystemExit) as info:
        main(["download"])
    assert info.value.code == (
        "Частотный словарь Ляшевской и Шарова: не удалось скачать - "
        "Cannot download the file http://dict.ruslang.ru/Freq2011.zip"
    )
    assert capsys.readouterr().out.splitlines()[-1].endswith("скачивается...")


def test_download_help(capsys):
    with pytest.raises(SystemExit):
        main(["download", "--help"])
    assert "словарь ударений Козиева" in capsys.readouterr().out
