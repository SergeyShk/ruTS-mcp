from fastmcp import FastMCP

from . import __version__
from .tools import analyze_text

INSTRUCTIONS = (
    "Статистики русских текстов, которые считает библиотека ruTS. Инструменты измеряют текст, "
    "чтобы не оценивать его на глаз: у каждого значения есть описание того, что оно считает, "
    "а предупреждения результата говорят, когда значения не имеют смысла для текста."
)
READ_ONLY = {"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False}

mcp = FastMCP("ruTS-mcp", instructions=INSTRUCTIONS, version=__version__)
mcp.tool(analyze_text, title="Анализ русского текста", annotations=READ_ONLY)
