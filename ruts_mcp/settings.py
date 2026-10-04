from collections.abc import Mapping
from dataclasses import dataclass
from os import environ as os_environ
from typing import Self

ENV_PREFIX = "RUTS_MCP_"


@dataclass(frozen=True)
class Settings:
    """
    Настройки сервера

    Описание:
        Настройка читается из переменной окружения с ее именем в верхнем
        регистре и префиксом RUTS_MCP_ (RUTS_MCP_MAX_TEXT_LENGTH); если
        переменная не задана, остается значение по умолчанию

    Атрибуты:
        max_text_length (int): Наибольшее число символов текста, который принимает инструмент
    """

    max_text_length: int = 500_000

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

        Пример использования:
            >>> Settings.from_env({"RUTS_MCP_MAX_TEXT_LENGTH": "1000"})
            Settings(max_text_length=1000)
        """
        environ = os_environ if environ is None else environ
        return cls(
            max_text_length=_positive_int(environ, "MAX_TEXT_LENGTH", cls.max_text_length),
        )


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
