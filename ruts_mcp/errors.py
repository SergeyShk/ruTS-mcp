from collections.abc import Iterator
from contextlib import contextmanager

from fastmcp.exceptions import ToolError

from .settings import Settings


def check_text(text: str) -> None:
    """
    Проверка, что текст не длиннее лимита сервера

    Аргументы:
        text (str): Текст, переданный инструменту

    Исключения:
        ToolError: Если текст длиннее Settings.max_text_length
    """
    limit = Settings.from_env().max_text_length
    if len(text) > limit:
        raise ToolError(
            f"Текст длиннее лимита сервера (символов: {len(text)}, лимит: {limit}): "
            "передайте текст короче или его часть; лимит задает переменная RUTS_MCP_MAX_TEXT_LENGTH"
        )


@contextmanager
def ruts_errors() -> Iterator[None]:
    """
    Перевод исключений ruTS в ошибки инструмента

    Описание:
        Сообщение RutsError и ее подклассов говорит, что не так с входными
        данными, поэтому модель получает его как ошибку инструмента, а не
        как сбой сервера. ruTS импортируется при входе

    Исключения:
        ToolError: Если ruTS поднимает RutsError
    """
    from ruts import RutsError

    try:
        yield
    except RutsError as error:
        raise ToolError(str(error)) from error
