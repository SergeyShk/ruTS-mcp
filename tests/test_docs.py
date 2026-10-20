"""Страницы документации: английские пары русских, сигнатуры и параметры по схемам, примеры"""

import asyncio
import json
import re
from pathlib import Path
from textwrap import dedent
from typing import Any

import pytest
from fastmcp import Client

from ruts_mcp.server import mcp

DOCS = Path(__file__).parents[1] / "docs"
PAGES = sorted(path for path in DOCS.rglob("*.md") if not path.name.endswith(".en.md"))
ALL_PAGES = sorted(DOCS.rglob("*.md"))
# Блок сигнатуры: ``` {.python .signature} с одним вызовом в одной строке
SIGNATURE = re.compile(r"^``` \{\.python \.signature\}\n(\w+)\((.*)\)\n```$", re.MULTILINE)
# Пример: вкладка вызова с JSON tools/call и вкладка результата с JSON ответа
EXAMPLE = re.compile(
    r'^=== "(?:Вызов|Call)"\n\n    ``` json\n(.*?)\n    ```\n\n'
    r'=== "(?:Результат|Result)"\n\n    ``` json\n(.*?)\n    ```$',
    re.MULTILINE | re.DOTALL,
)
PARAMETER = re.compile(r"^\| `(\w+)` \| `([\w\[\]]+)` \| (`[^|]+`|-) \|", re.MULTILINE)


def anchors(text: str) -> set[str]:
    return set(re.findall(r"\{ #([\w-]+) \}", text))


def links(text: str) -> set[str]:
    return set(re.findall(r"\]\(([^)#\s]+\.md)", text))


def page_id(page: Path) -> str:
    return str(page.relative_to(DOCS))


@pytest.fixture(scope="module")
def schemas() -> dict[str, dict[str, Any]]:
    """Схемы параметров инструментов сервера"""

    async def listing() -> dict[str, dict[str, Any]]:
        async with Client(mcp) as client:
            return {tool.name: tool.input_schema for tool in await client.list_tools()}

    return asyncio.run(listing())


def type_label(schema: dict[str, Any]) -> str:
    """Тип параметра так, как его пишет таблица: без null, у массива - с типом элементов"""
    (option,) = [item for item in schema.get("anyOf", [schema]) if item.get("type") != "null"]
    if option["type"] == "array":
        return f"array[{option['items']['type']}]"
    return str(option["type"])


def default_text(schema: dict[str, Any]) -> str | None:
    """Значение по умолчанию в JSON; None - параметр обязателен"""
    return json.dumps(schema["default"], ensure_ascii=False) if "default" in schema else None


@pytest.mark.parametrize("page", PAGES, ids=list(map(page_id, PAGES)))
def test_english_page(page):
    english = page.with_name(page.name[:-3] + ".en.md")
    assert english.is_file(), f"нет английской версии {english.relative_to(DOCS)}"
    russian_text = page.read_text(encoding="utf-8")
    english_text = english.read_text(encoding="utf-8")
    assert anchors(english_text) == anchors(russian_text)
    assert links(english_text) == links(russian_text)
    assert russian_text.count("\n## ") == english_text.count("\n## ")
    assert SIGNATURE.findall(english_text) == SIGNATURE.findall(russian_text)
    assert EXAMPLE.findall(english_text) == EXAMPLE.findall(russian_text)


def test_no_orphan_english_pages():
    english = {path.relative_to(DOCS) for path in DOCS.rglob("*.en.md")}
    assert english == {page.relative_to(DOCS).with_suffix(".en.md") for page in PAGES}


@pytest.mark.parametrize("page", ALL_PAGES, ids=list(map(page_id, ALL_PAGES)))
def test_signatures_and_parameters(page, schemas):
    """Сигнатура и таблица параметров страницы инструмента совпадают с его схемой"""
    text = page.read_text(encoding="utf-8")
    for name, written in SIGNATURE.findall(text):
        assert name in schemas, f"{name}: нет такого инструмента"
        properties = schemas[name]["properties"]
        expected = ", ".join(
            param if default_text(schema) is None else f"{param}={default_text(schema)}"
            for param, schema in properties.items()
        )
        assert written == expected
        section = next(
            part for part in text.split("\n## ") if part.startswith(("Параметры", "Parameters"))
        )
        rows = {param: (kind, default) for param, kind, default in PARAMETER.findall(section)}
        assert rows == {
            param: (
                type_label(schema),
                f"`{default_text(schema)}`" if "default" in schema else "-",
            )
            for param, schema in properties.items()
        }


def test_tool_pages(schemas):
    """У каждого инструмента своя страница с сигнатурой"""
    names = {name for page in ALL_PAGES for name, _ in SIGNATURE.findall(page.read_text("utf-8"))}
    assert names == set(schemas)


@pytest.mark.parametrize("page", ALL_PAGES, ids=list(map(page_id, ALL_PAGES)))
def test_examples(page):
    """Результат примера - ответ сервера на вызов из примера"""
    examples = EXAMPLE.findall(page.read_text(encoding="utf-8"))

    async def responses() -> list[Any]:
        async with Client(mcp) as client:
            return [
                (await client.call_tool(**json.loads(dedent(call)))).structured_content
                for call, _ in examples
            ]

    if examples:
        expected = [json.loads(dedent(result)) for _, result in examples]
        assert asyncio.run(responses()) == expected
