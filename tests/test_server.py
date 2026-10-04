import subprocess
import sys

import pytest
from fastmcp import Client
from fastmcp.client.transports import StdioTransport

import ruts_mcp
from ruts_mcp.server import INSTRUCTIONS, mcp
from ruts_mcp.tools import analyze_text

TEXT = "Мама мыла раму. Папа читал газету."

pytestmark = pytest.mark.anyio


async def test_server_info():
    async with Client(mcp) as client:
        assert client.server_info.name == "ruTS-mcp"
        assert client.server_info.version == ruts_mcp.__version__
        assert client.instructions == INSTRUCTIONS


async def test_tools():
    async with Client(mcp) as client:
        (tool,) = await client.list_tools()
    assert tool.name == "analyze_text"
    assert tool.title == "Анализ русского текста"
    assert tool.description.startswith("Измерить русский текст")
    assert tool.annotations.read_only_hint
    assert tool.annotations.idempotent_hint
    assert not tool.annotations.open_world_hint
    assert tool.input_schema["required"] == ["text"]
    groups = tool.input_schema["properties"]["groups"]
    assert groups["items"]["enum"] == ["basic", "readability", "diversity"]
    assert groups["default"] == ["basic", "readability"]
    preset = tool.input_schema["properties"]["readability_preset"]
    assert preset["enum"] == ["plainrussian", "fiction", "academic"]


async def test_call():
    async with Client(mcp) as client:
        result = await client.call_tool("analyze_text", {"text": TEXT, "distributions": True})
    assert result.structured_content == analyze_text(TEXT, distributions=True)


@pytest.mark.parametrize(
    ("arguments", "message"),
    [
        ({"text": ""}, "The data source has no words"),
        ({"text": TEXT, "groups": []}, "at least 1 item"),
        (
            {"text": TEXT, "groups": ["style"]},
            "Input should be 'basic', 'readability' or 'diversity'",
        ),
    ],
)
async def test_call_errors(arguments, message):
    async with Client(mcp) as client:
        result = await client.call_tool("analyze_text", arguments, raise_on_error=False)
    assert result.is_error
    assert message in result.content[0].text


def test_lazy_ruts():
    """Сервер запускается и отдает список инструментов, не импортируя ruTS"""
    code = (
        "import asyncio, sys\n"
        "from fastmcp import Client\n"
        "from ruts_mcp.server import mcp\n"
        "async def main():\n"
        "    async with Client(mcp) as client:\n"
        "        await client.list_tools()\n"
        "asyncio.run(main())\n"
        "print(sorted(name for name in ('ruts', 'anyts', 'spacy') if name in sys.modules))\n"
    )
    run = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True)
    assert run.stdout.strip() == "[]"


async def test_stdio():
    """Клиент старого протокола, как большинство клиентов, запускает сервер его командой"""
    transport = StdioTransport(sys.executable, ["-m", "ruts_mcp"])
    async with Client(transport, mode="legacy") as client:
        assert client.initialize_result.server_info.name == "ruTS-mcp"
        result = await client.call_tool("analyze_text", {"text": TEXT})
    assert result.structured_content["basic"]["n_words"]["value"] == 6
