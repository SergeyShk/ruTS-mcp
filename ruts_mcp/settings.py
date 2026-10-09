from collections.abc import Mapping
from dataclasses import dataclass
from os import environ as os_environ
from pathlib import Path
from typing import Self

from platformdirs import user_data_dir

ENV_PREFIX = "RUTS_MCP_"
DEFAULT_DATA_DIR = Path(user_data_dir("ruts-mcp", appauthor=False))


@dataclass(frozen=True)
class Settings:
    """
    Настройки сервера

    Описание:
        Настройка читается из переменной окружения с ее именем в верхнем
        регистре и префиксом RUTS_MCP_ (RUTS_MCP_MAX_TEXT_LENGTH); если
        переменная не задана, остается значение по умолчанию. Каталог данных
        задает переменная ruTS RUTS_DATA_DIR, без нее это каталог данных
        пользователя: ~/Library/Application Support/ruts-mcp на macOS,
        ~/.local/share/ruts-mcp на Linux, %LOCALAPPDATA%\\ruts-mcp на Windows

    Атрибуты:
        max_text_length (int): Наибольшее число символов текста, который принимает инструмент
        data_dir (Path): Каталог данных; словари лежат в его подкаталоге dicts, как в ruTS
    """

    max_text_length: int = 500_000
    data_dir: Path = DEFAULT_DATA_DIR

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> Self:
        """
        Чтение настроек из окружения

        Аргументы:
            environ (Mapping[str, str]): Переменные окружения; None - os.environ

        Вывод:
            Settings: Настройки сервера

        Исключения:
            ValueError: Если значение переменной не целое положительное число
                или RUTS_DATA_DIR - относительный путь

        Пример использования:
            >>> settings = Settings.from_env({"RUTS_MCP_MAX_TEXT_LENGTH": "1000"})
            >>> settings.max_text_length, settings.data_dir.name
            (1000, 'ruts-mcp')
        """
        environ = os_environ if environ is None else environ
        return cls(
            max_text_length=_positive_int(environ, "MAX_TEXT_LENGTH", cls.max_text_length),
            data_dir=_data_dir(environ),
        )


def _data_dir(environ: Mapping[str, str]) -> Path:
    """Каталог данных из RUTS_DATA_DIR или каталог данных пользователя"""
    raw = environ.get("RUTS_DATA_DIR")
    if not raw:
        return DEFAULT_DATA_DIR
    data_dir = Path(raw).expanduser()
    # Клиент запускает сервер из своего текущего каталога, и относительный путь указывал бы туда
    if not data_dir.is_absolute():
        raise ValueError(f"RUTS_DATA_DIR должна быть абсолютным путем, получено {raw!r}")
    return data_dir.resolve()


def _positive_int(environ: Mapping[str, str], name: str, default: int) -> int:
    """Целое положительное значение переменной или значение по умолчанию, если она не задана"""
    variable = ENV_PREFIX + name
    if variable not in environ:
        return default
    raw = environ[variable]
    try:
        value = int(raw)
    except ValueError:
        value = 0
    if value < 1:
        raise ValueError(f"{variable} должна быть целым положительным числом, получено {raw!r}")
    return value
