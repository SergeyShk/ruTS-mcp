import argparse
import io
import re
import sys
from collections.abc import Iterable, Sequence
from importlib.metadata import version
from typing import Any, NoReturn

from . import __version__
from .data import (
    FREQ_DICT_TITLE,
    SPACY_MODEL,
    SPACY_MODEL_TITLE,
    STRESS_DICT_TITLE,
    SpacyModel,
    freq_dict,
    models_dir,
    stress_dict,
)
from .server import mcp
from .settings import Settings

INTERRUPTED = 130
# Сообщения argparse, которые может получить команда; остальные печатаются как есть
ARGPARSE_ERRORS = (
    (re.compile(r"unrecognized arguments: (.*)"), "неизвестные аргументы: {0}"),
    (
        re.compile(r"argument (\S+): invalid choice: (.*?) \(choose from (.*)\)"),
        "аргумент {0}: неизвестное значение {1} (допустимые: {2})",
    ),
    (
        re.compile(r"argument (\S+): ignored explicit argument (.*)"),
        "аргумент {0}: лишнее значение {1}",
    ),
)


class HelpFormatter(argparse.HelpFormatter):
    """Справка с русской строкой использования"""

    def add_usage(
        self,
        usage: str | None,
        actions: Iterable[argparse.Action],
        groups: Iterable[Any],
        prefix: str | None = None,
    ) -> None:
        super().add_usage(usage, actions, groups, "использование: " if prefix is None else prefix)


class ArgumentParser(argparse.ArgumentParser):
    """Разбор аргументов с русскими справкой и сообщениями об ошибках"""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(formatter_class=HelpFormatter, add_help=False, **kwargs)
        options = self.add_argument_group("параметры")
        options.add_argument("-h", "--help", action="help", help="показать эту справку и выйти")
        self.options = options

    def error(self, message: str) -> NoReturn:
        for pattern, template in ARGPARSE_ERRORS:
            if match := pattern.fullmatch(message):
                message = template.format(*match.groups())
                break
        self.print_usage(sys.stderr)
        self.exit(2, f"{self.prog}: ошибка: {message}\n")


def main(argv: Sequence[str] | None = None) -> None:
    """
    Запуск сервера по stdio или команды download

    Описание:
        Настройки проверяются до запуска: неверная переменная окружения
        останавливает команду с ее сообщением. Ctrl+C завершает команду
        с кодом 130 без трейсбека

    Аргументы:
        argv (list[str]): Аргументы командной строки; None - sys.argv
    """
    # Справка и ошибки по-русски не должны падать на консоли с однобайтной кодировкой
    for stream in (sys.stdout, sys.stderr):
        if isinstance(stream, io.TextIOWrapper):
            stream.reconfigure(errors="replace")
    parser = ArgumentParser(
        prog="ruts-mcp",
        usage="%(prog)s [-h] [--version] [КОМАНДА ...]",
        description="MCP-сервер для ruTS: статистики русского текста как инструменты "
        "для LLM-агентов. Без команды запускает сервер по stdio; настройки задаются "
        "переменными окружения RUTS_MCP_*",
    )
    parser.options.add_argument(
        "--version",
        action="version",
        version=f"ruts-mcp {__version__}, ruts {version('ruts')}",
        help="показать версии ruts-mcp и ruts и выйти",
    )
    commands = parser.add_subparsers(dest="command", title="команды", metavar="КОМАНДА")
    download_parser = commands.add_parser(
        "download",
        help="скачать словари для групп lexical и verse и модель spaCy для группы syntax",
        prog="ruts-mcp download",
        description="Скачивает частотный словарь Ляшевской и Шарова (0,5 МБ) для группы lexical, "
        "словарь ударений Козиева (11 МБ) для группы verse и модель spaCy ru_core_news_sm (15 МБ) "
        "для группы syntax в каталог данных: RUTS_DATA_DIR, если она задана, иначе каталог "
        "данных пользователя. На диске они занимают около 130 МБ. Установленный пакет модели "
        "не скачивается",
    )
    download_parser.options.add_argument(
        "--force",
        action="store_true",
        help="скачать заново, даже если словари и модель уже скачаны",
    )
    args = parser.parse_args(argv)
    try:
        Settings.from_env()
    except ValueError as error:
        parser.error(str(error))
    try:
        if args.command == "download":
            download(force=args.force)
        else:
            mcp.run(show_banner=False)
    except KeyboardInterrupt:
        sys.exit(INTERRUPTED)


def download(force: bool = False) -> None:
    """
    Скачивание словарей для групп lexical и verse и модели spaCy для группы syntax

    Описание:
        Уже скачанные словари и модель пропускаются, если не задан force;
        установленный пакет модели не скачивается. Загрузки независимы: ошибка
        печатается с причиной, и команда завершается с кодом 1 после попытки
        скачать все

    Аргументы:
        force (bool): Скачать заново, даже если словари и модель уже скачаны
    """
    from ruts import RutsError

    print(f"Каталог данных: {Settings.from_env().data_dir}")
    model = SpacyModel(models_dir())
    failed = False
    for title, done, item in (
        (FREQ_DICT_TITLE, "скачан", freq_dict()),
        (STRESS_DICT_TITLE, "скачан", stress_dict()),
        (SPACY_MODEL_TITLE, "скачана", model),
    ):
        if item is model and model.installed:
            print(f"{title}: установлена пакетом {SPACY_MODEL}")
            continue
        if item.filepath and not force:
            print(f"{title}: уже {done}")
            continue
        print(f"{title}: скачивается...", flush=True)
        try:
            item.download(force=force)
        except (RutsError, OSError) as error:
            cause = f" ({error.__cause__})" if error.__cause__ else ""
            print(f"{title}: не удалось скачать - {error}{cause}", file=sys.stderr)
            failed = True
        else:
            print(f"{title}: {done}")
    if failed:
        sys.exit(1)
