from typing import Annotated, Any

from pydantic import Field

from .analysis import Analysis, Options, Preset
from .errors import check_text, ruts_errors
from .groups import DEFAULT_GROUPS, GROUPS, Group
from .language import language_warnings


def analyze_text(
    text: Annotated[str, Field(description="Текст на русском языке")],
    groups: Annotated[
        tuple[Group, ...],
        Field(description="Группы статистик; каждая - ключ результата", min_length=1),
    ] = DEFAULT_GROUPS,
    distributions: Annotated[
        bool,
        Field(
            description="Добавить распределения слов по числу букв и слогов "
            "и знаков препинания по типам (группа basic)"
        ),
    ] = False,
    readability_preset: Annotated[
        Preset,
        Field(
            description="Коэффициенты формул удобочитаемости: plainrussian - тексты общего "
            "назначения, fiction - художественные, academic - учебные (группа readability)"
        ),
    ] = "plainrussian",
) -> dict[str, Any]:
    """Измерить русский текст статистиками библиотеки ruTS.

    Используйте, чтобы получить точные числа о тексте, а не оценивать его на глаз. Считаются только запрошенные группы.

    Группы статистик:
    - basic: предложения, слова, слоги, символы, буквы, пробелы и знаки препинания; уникальные, длинные (от 6 букв), сложные (от 4 слогов), простые, односложные и многосложные слова с долей от всех слов.
    - readability: удобочитаемость - сводный класс и формулы Флеша-Кинкайда, Флеша, Колман-Лиау, SMOG, ARI, LIX, RIX, Соловьёва-Иванова-Солнышкиной, Мацковского, Дейла-Чейла и Ганнинга с переводом в класс школы и возраст читателя, время чтения.
    - diversity: лексическое разнообразие - TTR и поправки к нему, MATTR, MSTTR, MTLD, HD-D, индексы Симпсона, Юла и Оноре, энтропия, законы Ципфа и Хипса.

    В результате по ключу на каждую запрошенную группу: статистика с ее значением "value", долей "share" или прочтением по шкале "interpretation", если они есть, и описанием "description" - что она считает. Значение null - статистика на этом тексте не определена. Ключ "warnings" - причины, по которым значения могут быть неустойчивы или не иметь смысла для этого текста: короткий текст, текст не на русском языке. Прочитайте предупреждения, прежде чем делать выводы.
    """
    check_text(text)
    analysis = Analysis(text, Options(distributions=distributions, preset=readability_preset))
    result: dict[str, Any] = {}
    warnings = language_warnings(text)
    with ruts_errors():
        for group in dict.fromkeys(groups):
            result[group], group_warnings = GROUPS[group](analysis)
            warnings += group_warnings
    return result | {"warnings": warnings}
