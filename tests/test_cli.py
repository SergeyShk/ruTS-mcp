import importlib
import runpy
import sys
from importlib.metadata import version

import pytest

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
        "RUTS_MCP_MAX_TEXT_LENGTH must be a positive integer, got 'many'"
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
