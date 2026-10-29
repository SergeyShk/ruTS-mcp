"""Скилл ruts: метаданные и полнота относительно сервера"""

from pathlib import Path

import pytest
import yaml
from fastmcp import Client

from ruts_mcp.groups import GROUPS
from ruts_mcp.server import mcp

ROOT = Path(__file__).parents[1]
SKILL = ROOT / "skills" / "ruts" / "SKILL.md"
TEXT = SKILL.read_text(encoding="utf-8")

pytestmark = pytest.mark.anyio


def test_frontmatter():
    empty, header, _ = TEXT.split("---\n", 2)
    meta = yaml.safe_load(header)
    assert not empty
    assert meta["name"] == SKILL.parent.name
    assert 0 < len(meta["description"]) <= 1024


async def test_server_coverage():
    """Скилл называет каждый инструмент, группу, ресурс и промпт сервера"""
    async with Client(mcp) as client:
        names = [tool.name for tool in await client.list_tools()]
        names += [str(resource.uri) for resource in await client.list_resources()]
        names += [f"/mcp__ruts__{prompt.name}" for prompt in await client.list_prompts()]
    names += list(GROUPS)
    assert [name for name in names if f"`{name}`" not in TEXT] == []


def test_install_commands():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for command in ("claude mcp add ruts -- uvx ruts-mcp", "uvx ruts-mcp download"):
        assert command in TEXT
        assert command in readme
