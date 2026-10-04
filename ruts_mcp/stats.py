import re
from collections.abc import Callable
from typing import Any, Literal

Group = Literal["basic"]

PRECISION = 3
MIN_RUSSIAN_SHARE = 0.5
MAX_FOREIGN_CYRILLIC_SHARE = 0.03
RUSSIAN = re.compile(r"[а-яё]", re.IGNORECASE)
FOREIGN_CYRILLIC = re.compile(r"(?![а-яё])[\u0400-\u052f]", re.IGNORECASE)

# Пороги ruts.constants записаны текстом, чтобы не импортировать ruTS до вызова
BASIC_STATS = {
    "n_sents": "Предложения, в которых есть слова",
    "n_words": "Слова, включая числа; у чисел и слов без гласных (в, км) 0 слогов, поэтому "
    "они не входят ни в простые и сложные, ни в одно- и многосложные слова",
    "n_unique_words": "Уникальные слова без учета регистра; доля от всех слов",
    "n_long_words": "Длинные слова, от 6 букв; доля от всех слов",
    "n_complex_words": "Сложные слова, от 4 слогов; доля от всех слов",
    "n_simple_words": "Простые слова, от 1 до 3 слогов; доля от всех слов",
    "n_monosyllable_words": "Односложные слова; доля от всех слов",
    "n_polysyllable_words": "Многосложные слова, от 2 слогов; доля от всех слов",
    "n_chars": "Символы без переводов строки",
    "n_letters": "Буквы; доля от всех символов",
    "n_spaces": "Пробелы и табуляции; доля от всех символов",
    "n_syllables": "Слоги",
    "n_punctuations": "Знаки препинания и прочие знаки и символы (%, $, №, эмодзи); "
    "доля от всех символов",
}
BASIC_DISTRIBUTIONS = {
    "c_letters": "Число слов по числу букв",
    "c_syllables": "Число слов по числу слогов",
    "c_punctuations": "Число знаков препинания по типам; other - прочие знаки и символы, "
    "в том числе эмодзи",
}


def basic_stats(text: str, distributions: bool = False) -> dict[str, Any]:
    """
    Основные статистики текста с их описаниями

    Описание:
        Счетчики BasicStats из ruTS; счетчик слов или символов идет с долей
        от всех слов или всех символов. Ключи распределений - строки, как
        в JSON; типы знаков препинания, которых нет в тексте, опускаются

    Аргументы:
        text (str): Текст на русском языке
        distributions (bool): Добавить распределения слов по числу букв
            и слогов и знаков препинания по типам

    Вывод:
        dict[str, Any]: Имя статистики ruTS - ее значение, доля и описание

    Исключения:
        SourceError: Если в тексте нет слов

    Пример использования:
        >>> stats = basic_stats("Мама мыла раму.")
        >>> stats["n_sents"]
        {'value': 1, 'description': 'Предложения, в которых есть слова'}
        >>> stats["n_long_words"]["share"]
        0.0
    """
    from ruts import BasicStats

    stats = BasicStats(text, normalize=True).get_stats()
    result: dict[str, Any] = {}
    for name, description in BASIC_STATS.items():
        item: dict[str, Any] = {"value": stats[name]}
        share = stats.get("p" + name[1:])
        if share is not None:
            item["share"] = round(share, PRECISION)
        result[name] = item | {"description": description}
    if distributions:
        for name, description in BASIC_DISTRIBUTIONS.items():
            counts = {str(key): count for key, count in stats[name].items() if count}
            result[name] = {"value": counts, "description": description}
    return result


GROUPS: dict[Group, Callable[[str, bool], dict[str, Any]]] = {"basic": basic_stats}


def language_warnings(text: str) -> list[str]:
    """
    Предупреждения о тексте не на русском языке

    Описание:
        ruTS считает слоги и слова по правилам русского языка, поэтому для
        текста на другом языке ее значения не имеют смысла. Текст без букв
        предупреждений не получает. Предупреждение дают меньше половины букв
        русского алфавита и от 3 % букв кириллицы не из него (і, ї, ў, ј, қ),
        как в украинском, белорусском, сербском или казахском тексте; доля
        в сообщении округляется вниз

    Аргументы:
        text (str): Текст, переданный инструменту

    Вывод:
        list[str]: Предупреждения для модели; для русского текста - пустой список

    Пример использования:
        >>> language_warnings("Мама мыла раму")
        []
        >>> language_warnings("Mama washed the frame")
        ['Букв русского алфавита - только 0%: ruTS считает статистики по правилам русского языка, для текста на другом языке значения не имеют смысла']
        >>> language_warnings("Він прийшов додому")
        ['Букв кириллицы не из русского алфавита - 6% (і): текст, похоже, не на русском языке, а ruTS считает слоги и слова по правилам русского, так что значения могут быть неверны']
    """
    letters = sum(char.isalpha() for char in text)
    if not letters:
        return []
    warnings = []
    russian = len(RUSSIAN.findall(text))
    if russian / letters < MIN_RUSSIAN_SHARE:
        warnings.append(
            f"Букв русского алфавита - только {_percent(russian, letters)}: ruTS считает статистики "
            "по правилам русского языка, для текста на другом языке значения не имеют смысла"
        )
    foreign = FOREIGN_CYRILLIC.findall(text)
    if len(foreign) / letters >= MAX_FOREIGN_CYRILLIC_SHARE:
        examples = ", ".join(sorted({char.lower() for char in foreign}))
        warnings.append(
            f"Букв кириллицы не из русского алфавита - {_percent(len(foreign), letters)} "
            f"({examples}): текст, похоже, не на русском языке, а ruTS считает слоги "
            "и слова по правилам русского, так что значения могут быть неверны"
        )
    return warnings


def _percent(count: int, total: int) -> str:
    """Доля в процентах с округлением вниз, чтобы 49,9 % не выглядели как пороговые 50 %; в целых числах, без погрешности float"""
    return f"{100 * count // total}%"
