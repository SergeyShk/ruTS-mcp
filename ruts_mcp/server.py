from fastmcp import FastMCP

from . import __version__
from .tools import analyze_text

INSTRUCTIONS = (
    "Statistics of Russian texts computed by the ruTS library. Use the tools to measure "
    "a text instead of judging it by eye: every value comes with a description of what it "
    "counts, and the warnings of a result say when the values are not meaningful for the text."
)
READ_ONLY = {"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False}

mcp = FastMCP("ruTS-mcp", instructions=INSTRUCTIONS, version=__version__)
mcp.tool(analyze_text, title="Analyze a Russian text", annotations=READ_ONLY)
