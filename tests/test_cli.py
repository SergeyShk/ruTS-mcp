import importlib
import io
import json
import re
import runpy
import sys
from importlib.metadata import version

import pytest
import spacy
from ruts.datasets import FreqDict, StressDict
from ruts.exceptions import DownloadError

import ruts_mcp
from ruts_mcp.cli import main
from ruts_mcp.data import SPACY_MODEL, SpacyModel
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
    """Загрузка словарей и модели без сети: пишет пустые файлы и запоминает force"""
    calls = []

    def download(self, force=False):
        calls.append((type(self).__name__, force))
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._filepath.touch()

    def download_model(self, force=False):
        calls.append(("SpacyModel", force))
        target = self.data_dir / f"{SPACY_MODEL}-0.0.0"
        target.mkdir(parents=True, exist_ok=True)
        meta = {"spacy_version": f"=={spacy.about.__version__}"}
        (target / "meta.json").write_text(json.dumps(meta), encoding="utf-8")

    monkeypatch.setattr(FreqDict, "download", download)
    monkeypatch.setattr(StressDict, "download", download)
    monkeypatch.setattr(SpacyModel, "download", download_model)
    monkeypatch.setattr(SpacyModel, "installed", property(lambda self: False))
    return calls


def test_download(downloads, runs, capsys, data_dir):
    main(["download"])
    assert capsys.readouterr().out.splitlines() == [
        f"Каталог данных: {data_dir}",
        "Частотный словарь Ляшевской и Шарова: скачивается...",
        "Частотный словарь Ляшевской и Шарова: скачан",
        "Словарь ударений Козиева: скачивается...",
        "Словарь ударений Козиева: скачан",
        "Модель spaCy ru_core_news_sm: скачивается...",
        "Модель spaCy ru_core_news_sm: скачана",
    ]
    main(["download"])
    assert capsys.readouterr().out.splitlines()[1:] == [
        "Частотный словарь Ляшевской и Шарова: уже скачан",
        "Словарь ударений Козиева: уже скачан",
        "Модель spaCy ru_core_news_sm: уже скачана",
    ]
    main(["download", "--force"])
    assert downloads == [
        ("FreqDict", False),
        ("StressDict", False),
        ("SpacyModel", False),
        ("FreqDict", True),
        ("StressDict", True),
        ("SpacyModel", True),
    ]
    assert runs == []


def test_download_installed_model(downloads, monkeypatch, capsys):
    """Установленный пакет модели не скачивается"""
    monkeypatch.setattr(SpacyModel, "installed", property(lambda self: True))
    main(["download"])
    assert capsys.readouterr().out.splitlines()[-1] == (
        "Модель spaCy ru_core_news_sm: установлена пакетом ru_core_news_sm"
    )
    assert ("SpacyModel", False) not in downloads


def test_download_error(downloads, monkeypatch, capsys):
    """Сбой одного словаря не отменяет другой, причина печатается, код выхода 1"""

    def fail(self, force=False):
        url = "http://dict.ruslang.ru/Freq2011.zip"
        raise DownloadError(f"Cannot download the file {url}") from OSError("connection refused")

    monkeypatch.setattr(FreqDict, "download", fail)
    with pytest.raises(SystemExit) as info:
        main(["download"])
    assert info.value.code == 1
    output = capsys.readouterr()
    assert output.err == (
        "Частотный словарь Ляшевской и Шарова: не удалось скачать - Cannot download the file "
        "http://dict.ruslang.ru/Freq2011.zip (connection refused)\n"
    )
    assert output.out.splitlines()[-1] == "Модель spaCy ru_core_news_sm: скачана"
    assert downloads == [("StressDict", False), ("SpacyModel", False)]


def test_download_help(capsys):
    with pytest.raises(SystemExit):
        main(["download", "--help"])
    output = capsys.readouterr().out
    assert output.startswith("использование: ruts-mcp download [-h] [--force]")
    assert "словарь ударений Козиева" in output
    assert "ru_core_news_sm" in output


def test_help_russian(capsys):
    with pytest.raises(SystemExit):
        main(["--help"])
    output = capsys.readouterr().out
    assert output.startswith("использование: ruts-mcp [-h] [--version] [КОМАНДА ...]")
    assert "\nпараметры:\n" in output
    assert "options" not in output


@pytest.mark.parametrize(
    ("argv", "message"),
    [
        (["foo"], r"аргумент КОМАНДА: неизвестное значение 'foo' \(допустимые: '?download'?\)"),
        (["download", "--x"], "неизвестные аргументы: --x"),
        (["--version=1"], "аргумент --version: лишнее значение '1'"),
    ],
    ids=["choice", "unrecognized", "explicit"],
)
def test_errors_russian(capsys, runs, argv, message):
    with pytest.raises(SystemExit) as info:
        main(argv)
    assert info.value.code == 2
    error = capsys.readouterr().err
    assert error.startswith("использование: ruts-mcp")
    assert re.search(f"\nruts-mcp: ошибка: {message}\n$", error)
    assert runs == []


@pytest.mark.parametrize("argv", [[], ["download"]])
def test_interrupted(monkeypatch, capsys, argv):
    """Ctrl+C завершает сервер и загрузку с кодом 130 без трейсбека"""

    def interrupt(*args, **kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr(mcp, "run", interrupt)
    monkeypatch.setattr(FreqDict, "download", interrupt)
    with pytest.raises(SystemExit) as info:
        main(argv)
    assert info.value.code == 130
    assert capsys.readouterr().err == ""


def test_download_os_error(downloads, monkeypatch, capsys):
    def fail(self, force=False):
        raise PermissionError(13, "Permission denied")

    monkeypatch.setattr(StressDict, "download", fail)
    with pytest.raises(SystemExit) as info:
        main(["download"])
    assert info.value.code == 1
    assert capsys.readouterr().err == (
        "Словарь ударений Козиева: не удалось скачать - [Errno 13] Permission denied\n"
    )


def test_output_errors_replace(monkeypatch, runs):
    """Справка печатается и на консоли без кириллицы: символы заменяются, а не роняют команду"""
    buffer = io.BytesIO()
    stdout = io.TextIOWrapper(buffer, encoding="cp1252")
    monkeypatch.setattr(sys, "stdout", stdout)
    monkeypatch.setattr(sys, "stderr", io.StringIO())
    with pytest.raises(SystemExit):
        main(["--help"])
    stdout.flush()
    assert buffer.getvalue().startswith(b"?????????????: ruts-mcp")
