from fastmcp import FastMCP

from . import __version__
from .compare import compare_texts, keyness
from .corpus import collocations, dispersion, kwic
from .prompts import (
    compare_review,
    officialese_review,
    readability_review,
    seo_review,
    verse_review,
)
from .resources import data_status, readability_scales, style_norms
from .tools import analyze_text

INSTRUCTIONS = (
    "Статистики русских текстов, которые считает библиотека ruTS. Инструменты измеряют текст, "
    "чтобы не оценивать его на глаз: у каждого значения есть описание того, что оно считает, "
    "а предупреждения результата говорят, когда значения не имеют смысла для текста."
)
READ_ONLY = {"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False}

mcp = FastMCP("ruTS-mcp", instructions=INSTRUCTIONS, version=__version__)
mcp.tool(analyze_text, title="Анализ русского текста", annotations=READ_ONLY)
mcp.tool(kwic, title="Конкорданс", annotations=READ_ONLY)
mcp.tool(collocations, title="Коллокации", annotations=READ_ONLY)
mcp.tool(dispersion, title="Дисперсия слов", annotations=READ_ONLY)
mcp.tool(keyness, title="Ключевые слова", annotations=READ_ONLY)
mcp.tool(compare_texts, title="Сравнение корпусов", annotations=READ_ONLY)

mcp.resource(
    "ruts://scales/readability",
    title="Шкалы удобочитаемости",
    description="Классы и возраст читателя для формул класса, полосы индекса Флеша и LIX, "
    "классы RIX",
    mime_type="text/markdown",
)(readability_scales)
mcp.resource(
    "ruts://scales/style",
    title="Нормы стиля",
    description="Нормы SEO-сервисов для тошноты, водности, заспамленности и естественности "
    "по Ципфу",
    mime_type="text/markdown",
)(style_norms)
mcp.resource(
    "ruts://data",
    title="Данные сервера",
    description="Каталог данных и состояние словарей и модели spaCy: что скачано и как скачать",
    mime_type="text/markdown",
)(data_status)

mcp.prompt(readability_review, title="Удобочитаемость текста")
mcp.prompt(officialese_review, title="Канцелярит")
mcp.prompt(verse_review, title="Разбор стихотворения")
mcp.prompt(seo_review, title="SEO-проверка текста")
mcp.prompt(compare_review, title="Сравнение двух текстов")
