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

INSTRUCTIONS = """Статистики русских текстов, которые считает библиотека ruTS. Инструменты измеряют текст, чтобы не оценивать его на глаз: у каждого значения есть описание того, что оно считает, а предупреждения результата говорят, когда значения не имеют смысла для текста.

Для каких задач вызывать:
- для какого возраста и класса текст, насколько он труден - analyze_text с группами basic и readability (и syntax);
- канцелярит и бюрократический стиль - analyze_text с группами style и syntax;
- метр, размер, рифма, окончания строк и звукопись стихотворения - analyze_text с группами verse и phon;
- морфология, лексическое разнообразие, связность, частотность лексики - analyze_text с группами morph, diversity, cohesion, lexical;
- SEO-метрики текста для сайта (тошнота, водность, заспамленность) - analyze_text с группой style;
- ключевые слова текста относительно языка или другого текста - keyness;
- как употребляется слово, цитаты с контекстом - kwic;
- устойчивые сочетания и сочетаемость слова - collocations; равномерность слова по тексту - dispersion;
- чем различаются два текста или корпуса по стилю, авторство, текст человека или модели - compare_texts.

Текст из файла передавайте через path, а не пересылайте целиком. Шкалы прочтения - в ресурсах ruts://scales/readability и ruts://scales/style, скачаны ли словари и модель - в ruts://data."""
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
