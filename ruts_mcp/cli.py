import argparse
from collections.abc import Sequence
from importlib.metadata import version

from . import __version__
from .server import mcp
from .settings import Settings


def main(argv: Sequence[str] | None = None) -> None:
    """
    Запуск сервера по stdio

    Описание:
        Настройки проверяются до запуска: неверная переменная окружения
        останавливает команду с ее сообщением

    Аргументы:
        argv (list[str]): Аргументы командной строки; None - sys.argv
    """
    parser = argparse.ArgumentParser(
        prog="ruts-mcp",
        description="MCP-сервер для ruTS: статистики русского текста как инструменты "
        "для LLM-агентов. Работает по stdio; настройки задаются переменными окружения RUTS_MCP_*",
        add_help=False,
    )
    parser.add_argument("-h", "--help", action="help", help="показать эту справку и выйти")
    parser.add_argument(
        "--version",
        action="version",
        version=f"ruts-mcp {__version__}, ruts {version('ruts')}",
        help="показать версии ruts-mcp и ruts и выйти",
    )
    parser.parse_args(argv)
    try:
        Settings.from_env()
    except ValueError as error:
        parser.error(str(error))
    mcp.run(show_banner=False)
