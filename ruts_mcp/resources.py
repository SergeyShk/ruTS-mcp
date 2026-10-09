from collections.abc import Iterable
from math import inf, nextafter

from .data import (
    FREQ_DICT_TITLE,
    SPACY_MODEL,
    SPACY_MODEL_TITLE,
    STRESS_DICT_TITLE,
    SpacyModel,
    freq_dict,
    freq_dict_damaged,
    models_dir,
    stress_dict,
)
from .inputs import load_ruts
from .settings import Settings


def bound(value: float) -> tuple[float, bool]:
    """
    Граница полосы шкалы ruTS: число и входит ли оно в полосу

    Описание:
        Полоса «больше X» в ruTS начинается со следующего за X числа
        (nextafter(X, inf)): если короткая запись есть только у числа перед
        границей, граница читается как это число без включения

    Аргументы:
        value (float): Нижняя граница полосы

    Вывод:
        tuple[float, bool]: Граница для чтения и входит ли она в полосу

    Пример использования:
        >>> bound(90), bound(nextafter(7, inf))
        ((90, True), (7.0, False))
    """
    below = nextafter(value, -inf)
    if float(f"{value:.10g}") != value and float(f"{below:.10g}") == below:
        return below, False
    return value, True


def number(value: float) -> str:
    """Число для таблицы: без лишних нулей, с запятой"""
    return f"{value:g}".replace(".", ",")


def scale_table(header: str, bands: Iterable[tuple[float, str]]) -> str:
    """
    Таблица Markdown полос шкалы ruTS с интервалами значений

    Аргументы:
        header (str): Заголовок столбца полос
        bands (list[tuple[float, str]]): Нижние границы и полосы по убыванию, последняя
            полоса открыта вниз

    Вывод:
        str: Таблица: интервал значений полосы и сама полоса

    Пример использования:
        >>> print(scale_table("Норма", [(nextafter(7, inf), "выше"), (5, "норма"), (0, "ниже")]))
        | Интервал | Норма |
        |---|---|
        | (7; ∞) | выше |
        | [5; 7] | норма |
        | (-∞; 5) | ниже |
    """
    bands = list(bands)
    rows = [f"| Интервал | {header} |", "|---|---|"]
    for index, (value, label) in enumerate(bands):
        lower = "(-∞" if index == len(bands) - 1 else "[{}" if bound(value)[1] else "({}"
        lower = lower.format(number(bound(value)[0]))
        if index:
            upper_value, upper_in_previous = bound(bands[index - 1][0])
            upper = f"{number(upper_value)}{')' if upper_in_previous else ']'}"
        else:
            upper = "∞)"
        rows.append(f"| {lower}; {upper} | {label} |")
    return "\n".join(rows)


def readability_scales() -> str:
    """
    Шкалы прочтения метрик удобочитаемости ruTS

    Описание:
        Таблица классов и возраста читателя для формул класса и сводного
        класса, полосы индекса Флеша и LIX, классы RIX - по данным ruTS
        (GRADE_AGE_LEVELS, READING_EASE_LEVELS, LIX_LEVELS, RIX_GRADES)

    Вывод:
        str: Текст Markdown
    """
    load_ruts()
    from ruts import ReadabilityStats
    from ruts.constants import (
        GRADE_AGE_LEVELS,
        POSTGRADUATE_LEVEL,
        READABILITY_GRADE_STATS,
        READABILITY_STATS_DESC,
    )

    formulas = ", ".join(READABILITY_STATS_DESC[name] for name in READABILITY_GRADE_STATS)
    grades = ["| Лет обучения | Ступень | Возраст |", "|---|---|---|"]
    grades += [
        f"| {f'до {last}' if index == 0 else f'{first}-{last}'} | {stage} | {age} |"
        for index, (first, last, stage, age) in enumerate(GRADE_AGE_LEVELS)
    ]
    grades.append(f"| больше {GRADE_AGE_LEVELS[-1][1]} | {' | '.join(POSTGRADUATE_LEVEL)} |")
    rix = [(value, f"{grade}") for value, grade in ReadabilityStats.grade_scales["rix"]]
    sections = [
        "# Шкалы удобочитаемости ruTS",
        "## Класс и возраст читателя",
        f"Формулы класса ({formulas}) и сводный класс дают число лет обучения, нужное для "
        "понимания текста; у простых текстов оно бывает ниже нуля. Число округляется "
        "арифметически (6,5 - до 7) и читается по таблице:",
        "\n".join(grades),
        f"## {READABILITY_STATS_DESC['flesch_reading_easy']}",
        "Номинально от 0 до 100, чем выше, тем легче текст:",
        scale_table("Уровень", ReadabilityStats.level_scales["flesch_reading_easy"]),
        f"## {READABILITY_STATS_DESC['lix']}",
        scale_table("Тексты", ReadabilityStats.level_scales["lix"]),
        f"## {READABILITY_STATS_DESC['rix']}",
        "RIX переводится в число лет обучения по таблице Андерсона и читается по таблице классов:",
        scale_table("Лет обучения", rix),
    ]
    return "\n\n".join(sections) + "\n"


def style_norms() -> str:
    """
    Нормы SEO-сервисов для метрик стиля ruTS

    Описание:
        Полосы STYLE_NORMS, по которым читает метрики StyleStats.describe

    Вывод:
        str: Текст Markdown
    """
    load_ruts()
    from ruts.constants import STYLE_NORMS, STYLE_STATS_DESC

    sections = [
        "# Нормы стиля ruTS",
        "Нормы - ориентиры SEO-сервисов для текстов сайтов в несколько сотен слов: на коротких "
        "текстах тошнота и заспамленность неинформативны, к художественной прозе нормы "
        "неприменимы. У маркеров канцелярита норм нет.",
    ]
    for name, bands in STYLE_NORMS.items():
        sections += [f"## {name}: {STYLE_STATS_DESC[name]}", scale_table("Прочтение", bands)]
    return "\n\n".join(sections) + "\n"


def data_status() -> str:
    """
    Что из данных сервера скачано: словари и модель spaCy

    Вывод:
        str: Текст Markdown с каталогом данных, состоянием словарей и модели
            и командой, которая их скачивает
    """
    load_ruts()
    dictionary = freq_dict()
    if dictionary.filepath:
        dictionary_state = (
            "поврежден, скачайте заново с --force" if freq_dict_damaged(dictionary) else "скачан"
        )
    else:
        dictionary_state = "не скачан"
    model = SpacyModel(models_dir())
    if model.installed:
        model_state = f"установлена пакетом {SPACY_MODEL}"
    else:
        model_state = "скачана" if model.filepath else "не скачана"
    rows = [
        "| Данные | Группы и инструменты | Состояние |",
        "|---|---|---|",
        f"| {FREQ_DICT_TITLE} | lexical, keyness | {dictionary_state} |",
        f"| {STRESS_DICT_TITLE} | verse | {'скачан' if stress_dict().filepath else 'не скачан'} |",
        f"| {SPACY_MODEL_TITLE} | syntax | {model_state} |",
    ]
    return (
        "# Данные ruTS-mcp\n\n"
        f"Каталог данных: {Settings.from_env().data_dir}\n\n"
        + "\n".join(rows)
        + "\n\nНе скачанные словари и модель скачивает команда `ruts-mcp download` "
        "(при запуске через uvx - `uvx ruts-mcp download`).\n"
    )
