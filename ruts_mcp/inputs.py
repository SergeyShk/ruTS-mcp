import importlib
import threading
from pathlib import Path

from fastmcp.exceptions import ToolError

from .settings import Settings

UTF8_MAX_BYTES = 4
TEXT = "Текст на русском языке; вместо него можно задать path"
PATH = (
    "Абсолютный путь к текстовому файлу в UTF-8 на машине, где запущен сервер, вместо text: "
    "длинный текст не нужно пересылать в аргументе"
)

RUTS_MODULES = (
    "anyts.constants",
    "anyts.datasets",
    "ruts",
    "ruts.constants",
    "ruts.corpus",
    "ruts.datasets",
    "ruts.datasets.freq2011",
    "ruts.exceptions",
    "ruts.lexical_stats",
    "ruts.style_stats",
    "ruts.utils",
)

_import_lock = threading.Lock()
_imported = False


def load_ruts() -> None:
    """
    Импорт ruTS и anyTS один раз на процесс, под блокировкой

    Описание:
        Инструменты выполняются в пуле потоков, а одновременный первый импорт
        ruTS из нескольких потоков ломается; модули, которые сервер
        импортирует внутри функций, загружаются здесь, и последующие импорты
        берут их из sys.modules
    """
    global _imported
    with _import_lock:
        if not _imported:
            for module in RUTS_MODULES:
                importlib.import_module(module)
            _imported = True


def normalize(text: str) -> str:
    """
    Текст с переводами строк «\\n»

    Описание:
        Знаки ударения и мягкие переносы остаются: их снимает ruTS, а стих
        берет из знака ударение

    Аргументы:
        text (str): Текст

    Вывод:
        str: Текст, где «\\r\\n» и «\\r» заменены на «\\n»

    Пример использования:
        >>> normalize("Моро\\u0301з и солнце\\r\\nДень")
        'Моро́з и солнце\\nДень'
    """
    return text.replace("\r\n", "\n").replace("\r", "\n")


def check_length(length: int, label: str) -> None:
    """
    Проверка, что текст или корпус не длиннее лимита сервера

    Аргументы:
        length (int): Число символов
        label (str): Что проверяется: «Текст», «Эталон», «Корпус A»

    Исключения:
        ToolError: Если символов больше Settings.max_text_length
    """
    limit = Settings.from_env().max_text_length
    if length > limit:
        raise ToolError(
            f"{label} длиннее лимита сервера (символов: {length}, лимит: {limit}): "
            "передайте текст короче или его часть; лимит задает переменная RUTS_MCP_MAX_TEXT_LENGTH"
        )


def prepare_text(text: str, label: str = "Текст", check: bool = True) -> str:
    """
    Проверка и нормализация текста, переданного инструменту

    Аргументы:
        text (str): Текст
        label (str): Что это за текст, для сообщений об ошибках
        check (bool): Проверить лимит длины; False - лимит проверяется для корпуса целиком

    Вывод:
        str: Нормализованный текст (normalize)

    Исключения:
        ToolError: Если в тексте есть одиночные суррогаты UTF-16 или он длиннее лимита
    """
    try:
        text.encode("utf-8")
    except UnicodeEncodeError:
        raise ToolError(
            f"{label} поврежден: в нем есть одиночные суррогатные символы UTF-16 - "
            "так бывает, если строку обрезали посреди эмодзи; передайте текст заново"
        ) from None
    if check:
        check_length(len(text), label)
    return normalize(text)


def read_file(path: str, label: str = "Текст") -> str:
    """
    Чтение текста из файла на машине сервера

    Аргументы:
        path (str): Абсолютный путь к текстовому файлу в UTF-8, допускается «~»
        label (str): Что это за текст, для сообщений об ошибках

    Вывод:
        str: Содержимое файла

    Исключения:
        ToolError: Если путь относительный, файл не читается, длиннее лимита
            или не в UTF-8
    """
    file = Path(path).expanduser()
    if not file.is_absolute():
        raise ToolError(f"{label}: путь {path} относительный, нужен абсолютный путь к файлу")
    limit = Settings.from_env().max_text_length
    try:
        size = file.stat().st_size
        if size > limit * UTF8_MAX_BYTES:
            raise ToolError(
                f"{label}: файл {path} больше лимита сервера ({size} байт при лимите {limit} "
                "символов); лимит задает переменная RUTS_MCP_MAX_TEXT_LENGTH"
            )
        return file.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raise ToolError(f"{label}: файл {path} не в кодировке UTF-8") from None
    except OSError as error:
        raise ToolError(f"{label}: не удалось прочитать файл {path} - {error.strerror}") from None


def read_source(text: str, path: str | None, label: str = "Текст") -> str:
    """
    Текст инструмента: из аргумента text или из файла path, проверенный и нормализованный

    Аргументы:
        text (str): Текст из аргумента
        path (str): Путь к файлу с текстом или None
        label (str): Что это за текст, для сообщений об ошибках

    Вывод:
        str: Нормализованный текст (prepare_text)

    Исключения:
        ToolError: Если заданы и текст, и файл, или не задано ни то, ни другое,
            или текст не проходит проверки prepare_text и read_file
    """
    if path is not None and text:
        raise ToolError(f"{label}: задайте или текст, или путь к файлу, но не оба")
    if path is not None:
        text = read_file(path, label)
    elif not text:
        raise ToolError(f"{label} не задан: передайте текст или путь к файлу")
    return prepare_text(text, label)
