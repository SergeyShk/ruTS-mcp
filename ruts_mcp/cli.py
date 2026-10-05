import argparse
import sys
from collections.abc import Sequence
from importlib.metadata import version

from . import __version__
from .data import FREQ_DICT_TITLE, STRESS_DICT_TITLE, dicts_dir, freq_dict, stress_dict
from .server import mcp
from .settings import Settings


def main(argv: Sequence[str] | None = None) -> None:
    """
    Запуск сервера по stdio или команды download

    Описание:
        Настройки проверяются до запуска: неверная переменная окружения
        останавливает команду с ее сообщением

    Аргументы:
        argv (list[str]): Аргументы командной строки; None - sys.argv
    """
    parser = argparse.ArgumentParser(
        prog="ruts-mcp",
        usage="%(prog)s [-h] [--version] [КОМАНДА ...]",
        description="MCP-сервер для ruTS: статистики русского текста как инструменты "
        "для LLM-агентов. Без команды запускает сервер по stdio; настройки задаются "
        "переменными окружения RUTS_MCP_*",
        add_help=False,
    )
    parser.add_argument("-h", "--help", action="help", help="показать эту справку и выйти")
    parser.add_argument(
        "--version",
        action="version",
        version=f"ruts-mcp {__version__}, ruts {version('ruts')}",
        help="показать версии ruts-mcp и ruts и выйти",
    )
    commands = parser.add_subparsers(dest="command", title="команды", metavar="КОМАНДА")
    download_parser = commands.add_parser(
        "download",
        help="скачать словари для групп lexical и verse",
        prog="ruts-mcp download",
        description="Скачивает частотный словарь Ляшевской и Шарова (0,5 МБ) для группы lexical "
        "и словарь ударений Козиева (11 МБ) для группы verse в каталог данных: RUTS_DATA_DIR, "
        "если она задана, иначе каталог данных пользователя. Вместе с архивами словари "
        "занимают на диске около 90 МБ",
        add_help=False,
    )
    download_parser.add_argument(
        "-h", "--help", action="help", help="показать эту справку и выйти"
    )
    download_parser.add_argument(
        "--force", action="store_true", help="скачать заново, даже если словари уже скачаны"
    )
    args = parser.parse_args(argv)
    try:
        Settings.from_env()
    except ValueError as error:
        parser.error(str(error))
    if args.command == "download":
        download(force=args.force)
    else:
        mcp.run(show_banner=False)


def download(force: bool = False) -> None:
    """
    Скачивание словарей для групп lexical и verse

    Описание:
        Уже скачанный словарь пропускается, если не задан force. Словари
        скачиваются независимо: ошибка одного печатается с причиной, и команда
        завершается с кодом 1 после попытки скачать оба

    Аргументы:
        force (bool): Скачать заново, даже если словари уже скачаны
    """
    from ruts import RutsError

    print(f"Каталог словарей: {dicts_dir()}")
    failed = False
    for title, dataset in ((FREQ_DICT_TITLE, freq_dict()), (STRESS_DICT_TITLE, stress_dict())):
        if dataset.filepath and not force:
            print(f"{title}: уже скачан")
            continue
        print(f"{title}: скачивается...", flush=True)
        try:
            dataset.download(force=force)
        except RutsError as error:
            cause = f" ({error.__cause__})" if error.__cause__ else ""
            print(f"{title}: не удалось скачать - {error}{cause}", file=sys.stderr)
            failed = True
        else:
            print(f"{title}: скачан")
    if failed:
        sys.exit(1)
