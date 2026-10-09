from collections.abc import Iterator
from contextlib import contextmanager

from fastmcp.exceptions import ToolError

from .inputs import load_ruts


@contextmanager
def ruts_errors() -> Iterator[None]:
    """
    Перевод исключений ruTS в ошибки инструмента

    Описание:
        Сообщение RutsError и ее подклассов говорит, что не так с входными
        данными, поэтому модель получает его как ошибку инструмента, а не
        как сбой сервера. ruTS загружается при входе (load_ruts)

    Исключения:
        ToolError: Если ruTS поднимает RutsError
    """
    load_ruts()
    from ruts import RutsError

    try:
        yield
    except RutsError as error:
        raise ToolError(str(error)) from error
