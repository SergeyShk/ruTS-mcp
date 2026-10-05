from pathlib import Path
from typing import TYPE_CHECKING

from .settings import Settings

if TYPE_CHECKING:
    from ruts.datasets import FreqDict, StressDict

FREQ_DICT_TITLE = "Частотный словарь Ляшевской и Шарова"
STRESS_DICT_TITLE = "Словарь ударений Козиева"


def dicts_dir() -> Path:
    """Каталог словарей: подкаталог dicts каталога данных, как в ruTS"""
    return Settings.from_env().data_dir / "dicts"


def freq_dict() -> "FreqDict":
    """Частотный словарь ruTS из каталога словарей сервера"""
    from ruts.datasets import FreqDict

    return FreqDict(dicts_dir())


def stress_dict() -> "StressDict":
    """Словарь ударений ruTS из каталога словарей сервера"""
    from ruts.datasets import StressDict

    return StressDict(dicts_dir())


def missing_warning(title: str, consequence: str) -> str:
    """
    Предупреждение о не скачанном словаре

    Аргументы:
        title (str): Название словаря
        consequence (str): Что не посчитано без словаря

    Вывод:
        str: Предупреждение с командой, которая скачивает словари

    Пример использования:
        >>> missing_warning("Словарь ударений Козиева", "группа verse не посчитана")[:63]
        'Словарь ударений Козиева не скачан: группа verse не посчитана. '
    """
    return (
        f"{title} не скачан: {consequence}. Словари скачивает команда ruts-mcp download "
        f"(при запуске через uvx - uvx ruts-mcp download) в каталог {dicts_dir()}"
    )
