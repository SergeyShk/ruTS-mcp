import subprocess
import sys

import pytest
from fastmcp import Client
from fastmcp.client.transports import StdioTransport

import ruts_mcp
from ruts_mcp.corpus import kwic
from ruts_mcp.prompts import verse_review
from ruts_mcp.resources import data_status
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
        tools = {tool.name: tool for tool in await client.list_tools()}
    assert {name: tool.title for name, tool in tools.items()} == {
        "analyze_text": "Анализ русского текста",
        "kwic": "Конкорданс",
        "collocations": "Коллокации",
        "dispersion": "Дисперсия слов",
        "keyness": "Ключевые слова",
        "compare_texts": "Сравнение корпусов",
    }
    for tool in tools.values():
        assert tool.annotations.read_only_hint
        assert tool.annotations.idempotent_hint
        assert not tool.annotations.open_world_hint
    assert tools["kwic"].input_schema["required"] == ["text", "keyword"]
    measure = tools["collocations"].input_schema["properties"]["measure"]
    assert measure["enum"][0] == measure["default"] == "logdice"
    tool = tools["analyze_text"]
    assert tool.description.startswith("Измерить русский текст")
    assert tool.input_schema["required"] == ["text"]
    groups = tool.input_schema["properties"]["groups"]
    assert groups["items"]["enum"] == [
        "basic",
        "readability",
        "diversity",
        "morph",
        "phon",
        "cohesion",
        "style",
        "lexical",
        "verse",
        "syntax",
    ]
    assert groups["default"] == ["basic", "readability"]
    preset = tool.input_schema["properties"]["readability_preset"]
    assert preset["enum"] == ["plainrussian", "fiction", "academic"]


async def test_call():
    async with Client(mcp) as client:
        result = await client.call_tool("analyze_text", {"text": TEXT, "distributions": True})
    assert result.structured_content == analyze_text(TEXT, distributions=True)


async def test_dispersion_words_limit():
    async with Client(mcp) as client:
        result = await client.call_tool(
            "dispersion", {"text": TEXT, "words": ["мама"] * 201}, raise_on_error=False
        )
    assert result.is_error
    assert "at most 200 items" in result.content[0].text


async def test_resources():
    async with Client(mcp) as client:
        resources = {str(item.uri): item for item in await client.list_resources()}
        data = await client.read_resource("ruts://data")
    assert {uri: item.title for uri, item in resources.items()} == {
        "ruts://scales/readability": "Шкалы удобочитаемости",
        "ruts://scales/style": "Нормы стиля",
        "ruts://data": "Данные сервера",
    }
    assert all(item.mime_type == "text/markdown" for item in resources.values())
    assert data[0].text == data_status()


async def test_prompts():
    async with Client(mcp) as client:
        prompts = {item.name: item for item in await client.list_prompts()}
        result = await client.get_prompt("verse_review", {"text": TEXT})
    assert {name: item.title for name, item in prompts.items()} == {
        "readability_review": "Удобочитаемость текста",
        "officialese_review": "Канцелярит",
        "verse_review": "Разбор стихотворения",
        "seo_review": "SEO-проверка текста",
        "compare_review": "Сравнение двух текстов",
    }
    assert [argument.name for argument in prompts["compare_review"].arguments] == [
        "text_a",
        "text_b",
    ]
    (message,) = result.messages
    assert message.role == "user"
    assert message.content.text == verse_review(TEXT)


async def test_call_kwic():
    async with Client(mcp) as client:
        result = await client.call_tool("kwic", {"text": TEXT, "keyword": "раму", "window": 1})
    assert result.structured_content == kwic(TEXT, "раму", window=1)


@pytest.mark.parametrize(
    ("arguments", "message"),
    [
        ({"text": ""}, "The data source has no words"),
        ({"text": TEXT, "groups": []}, "at least 1 item"),
        (
            {"text": TEXT, "groups": ["unknown"]},
            "Input should be 'basic', 'readability', 'diversity', 'morph', 'phon', "
            "'cohesion', 'style', 'lexical', 'verse' or 'syntax'",
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
