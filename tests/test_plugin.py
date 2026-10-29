"""Плагин ruts и маркетплейс: манифесты и закрепленная версия сервера"""

import json
import re
import tomllib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).parents[1]
PLUGIN = ROOT / "plugins" / "ruts"
PROJECT = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
VERSION = re.compile(r"(\d+)\.(\d+)\.(\d+)(?:\.dev\d+)?")


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def test_marketplace():
    """Плагин берется из ветки stable, которую publish.yml сдвигает на каждый релиз"""
    (entry,) = load(ROOT / ".claude-plugin" / "marketplace.json")["plugins"]
    manifest = load(PLUGIN / ".claude-plugin" / "plugin.json")
    source = entry["source"]
    assert source["source"] == "git-subdir"
    assert source["url"] == PROJECT["urls"]["Repository"] + ".git"
    assert (ROOT / source["path"]).resolve() == PLUGIN
    assert source["ref"] == "stable"
    for field in ("name", "displayName", "description"):
        assert entry[field] == manifest[field]


def test_manifest():
    manifest = load(PLUGIN / ".claude-plugin" / "plugin.json")
    assert manifest["repository"] == PROJECT["urls"]["Repository"]
    assert manifest["homepage"] == PROJECT["urls"]["Documentation"]
    assert manifest["license"] == PROJECT["license"]
    assert (PLUGIN / manifest["icon"]).is_file()


def test_pinned_server():
    """Плагин запускает выпущенный сервер: в релизе - версию pyproject.toml, между релизами - прошлую"""
    (server,) = load(PLUGIN / ".mcp.json")["mcpServers"].values()
    package, pinned = server["args"][0].split("==")
    assert server["command"] == "uvx"
    assert package == PROJECT["name"]
    assert load(PLUGIN / ".claude-plugin" / "plugin.json")["version"] == pinned
    assert VERSION.fullmatch(pinned) and ".dev" not in pinned
    if ".dev" in PROJECT["version"]:
        current = VERSION.fullmatch(PROJECT["version"])
        assert current
        assert tuple(map(int, pinned.split("."))) < tuple(map(int, current.groups()))
    else:
        assert pinned == PROJECT["version"]
