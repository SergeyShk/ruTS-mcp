from typing import Annotated, Any

from pydantic import Field

from .errors import check_text, ruts_errors
from .stats import GROUPS, Group, language_warnings


def analyze_text(
    text: Annotated[str, Field(description="Текст на русском языке")],
    groups: Annotated[
        tuple[Group, ...],
        Field(description="Группы статистик; каждая - ключ результата", min_length=1),
    ] = ("basic",),
    distributions: Annotated[
        bool,
        Field(
            description="Добавить распределения слов по числу букв и слогов "
            "и знаков препинания по типам (группа basic)"
        ),
    ] = False,
) -> dict[str, Any]:
    """Измерить русский текст статистиками библиотеки ruTS.

    Используйте, чтобы получить точные числа о тексте, а не оценивать его на глаз.

    Группы статистик:
    - basic: предложения, слова, слоги, символы, буквы, пробелы и знаки препинания; уникальные, длинные (от 6 букв), сложные (от 4 слогов), простые, односложные и многосложные слова с долей от всех слов.

    В результате по ключу на каждую запрошенную группу: статистика с ее значением "value", долей "share", если она есть, и описанием "description" - что она считает. Ключ "warnings" - причины, по которым значения могут не иметь смысла для этого текста, например текст не на русском языке. Прочитайте предупреждения, прежде чем делать выводы.
    """
    check_text(text)
    with ruts_errors():
        result = {group: GROUPS[group](text, distributions) for group in dict.fromkeys(groups)}
    return result | {"warnings": language_warnings(text)}
