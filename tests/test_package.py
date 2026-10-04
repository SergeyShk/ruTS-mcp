import importlib
import importlib.metadata
import re
import shutil
import subprocess
import zipfile
from pathlib import Path

import pytest

import ruts_mcp

ROOT = Path(__file__).parents[1]


def test_version():
    assert re.fullmatch(r"\d+\.\d+\.\d+(\.dev\d+)?", ruts_mcp.__version__)
    assert ruts_mcp.__version__ != "0.0.0"


def test_metadata():
    assert "Russian" in ruts_mcp.__description__
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


def test_package_data():
    assert (Path(ruts_mcp.__file__).parent / "py.typed").is_file()


@pytest.mark.skipif(shutil.which("uv") is None, reason="the wheel is built by uv")
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
