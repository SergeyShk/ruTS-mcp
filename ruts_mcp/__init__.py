# MCP server for Russian Texts Statistics (ruTS-mcp)
#
# Copyright (C) 2026
# Author: Sergey Shkarin <kouki.sergey@gmail.com>
# URL: <https://github.com/SergeyShk/ruTS-mcp>

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("ruts-mcp")
except PackageNotFoundError:
    __version__ = "0.0.0"
__description__ = (
    "MCP server for ruTS: statistics of Russian texts as tools for LLM agents. "
    "Requires Python 3.11+"
)
__author__ = "Sergey Shkarin"
__author_email__ = "kouki.sergey@gmail.com"

__all__ = ["__version__"]
