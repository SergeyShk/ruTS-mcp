import importlib
import importlib.metadata
import json
import re
import shutil
import subprocess
import tomllib
import zipfile
from pathlib import Path

import pytest

import ruts_mcp

ROOT = Path(__file__).parents[1]
PROJECT = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]


def test_version():
    assert re.fullmatch(r"\d+\.\d+\.\d+(\.dev\d+)?", ruts_mcp.__version__)
    assert ruts_mcp.__version__ != "0.0.0"


def test_metadata():
    assert "русского текста" in ruts_mcp.__description__
    assert "__version__" in ruts_mcp.__all__
    assert ruts_mcp.__all__ == sorted(ruts_mcp.__all__)


def test_version_fallback(monkeypatch):
    def missing(name):
        raise importlib.metadata.PackageNotFoundError(name)

    monkeypatch.setattr(importlib.metadata, "version", missing)
    try:
        assert importlib.reload(ruts_mcp).__version__ == "0.0.0"
    finally:
        monkeypatch.undo()
        importlib.reload(ruts_mcp)
    assert ruts_mcp.__version__ != "0.0.0"


def test_entry_point():
    (point,) = importlib.metadata.entry_points(group="console_scripts", name="ruts-mcp")
    assert point.value == "ruts_mcp.cli:main"


def test_package_data():
    assert (Path(ruts_mcp.__file__).parent / "py.typed").is_file()


@pytest.mark.skipif(shutil.which("uv") is None, reason="колесо собирает uv")
def test_wheel_contents(tmp_path):
    subprocess.run(
        ["uv", "build", "--wheel", "--out-dir", str(tmp_path), str(ROOT)],
        capture_output=True,
        check=True,
    )
    (wheel,) = tmp_path.glob("*.whl")
    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())
    assert "ruts_mcp/py.typed" in names
    assert all(name.startswith(("ruts_mcp/", "ruts_mcp-")) for name in names)


def test_registry_server():
    """server.json реестра MCP согласован с pyproject.toml и README, который видит PyPI"""
    server = json.loads((ROOT / "server.json").read_text(encoding="utf-8"))
    (package,) = server["packages"]
    readme = (ROOT / PROJECT["readme"]).read_text(encoding="utf-8")
    assert f"<!-- mcp-name: {server['name']} -->" in readme
    assert server["description"] == PROJECT["description"]
    assert server["repository"]["url"] == PROJECT["urls"]["Repository"]
    assert server["websiteUrl"] == PROJECT["urls"]["Documentation"]
    assert package["identifier"] == PROJECT["name"]
    assert package["version"] == server["version"]


def test_glama():
    assert json.loads((ROOT / "glama.json").read_text(encoding="utf-8"))["maintainers"] == [
        "SergeyShk"
    ]
