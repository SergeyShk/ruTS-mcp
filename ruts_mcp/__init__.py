# MCP-сервер Russian Texts Statistics (ruTS-mcp)
#
# Copyright (C) 2026
# Автор: Шкарин Сергей <kouki.sergey@gmail.com>
# URL: <https://github.com/SergeyShk/ruTS-mcp>

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("ruts-mcp")
except PackageNotFoundError:
    __version__ = "0.0.0"
__description__ = """MCP-сервер для ruTS: статистики русского текста как инструменты для LLM-агентов.
Требует версию Python 3.11 и выше"""
__author__ = "Шкарин Сергей"
__author_email__ = "kouki.sergey@gmail.com"

__all__ = ["__version__"]
