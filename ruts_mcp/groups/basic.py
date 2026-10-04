from ..analysis import Analysis, GroupResult, stat

BASIC_STATS = {
    "n_sents": "Предложения, в которых есть слова",
    "n_words": "Слова, включая числа; у чисел и слов без гласных (в, км) 0 слогов, поэтому "
    "они не входят ни в простые и сложные, ни в одно- и многосложные слова",
    "n_unique_words": "Уникальные слова без учета регистра; доля от всех слов",
    "n_long_words": "Длинные слова, от {long_letters} букв; доля от всех слов",
    "n_complex_words": "Сложные слова, от {complex_syllables} слогов; доля от всех слов",
    "n_simple_words": "Простые слова, от 1 до {simple_syllables} слогов; доля от всех слов",
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


def basic_group(analysis: Analysis) -> GroupResult:
    """
    Основные статистики текста с их описаниями

    Описание:
        Счетчики BasicStats из ruTS; счетчик слов или символов идет с долей
        от всех слов или всех символов. Пороги длинных и сложных слов в описаниях -
        пороги ruTS, с которыми посчитаны значения. Распределения добавляются настройкой
        distributions, их ключи - строки, как в JSON; типы знаков препинания,
        которых нет в тексте, опускаются

    Аргументы:
        analysis (Analysis): Текст и настройки

    Вывод:
        tuple[dict[str, Any], list[str]]: Имя статистики ruTS - ее значение, доля
            и описание; предупреждений у группы нет

    Исключения:
        SourceError: Если в тексте нет слов

    Пример использования:
        >>> stats, warnings = basic_group(Analysis("Мама мыла раму."))
        >>> stats["n_sents"]
        {'value': 1, 'description': 'Предложения, в которых есть слова'}
        >>> stats["n_long_words"]["share"]
        0.0
    """
    from ruts.constants import COMPLEX_SYL_FACTOR, LONG_WORD_LETTER_FACTOR

    stats = analysis.basic.get_stats()
    params = {
        "long_letters": LONG_WORD_LETTER_FACTOR,
        "complex_syllables": COMPLEX_SYL_FACTOR,
        "simple_syllables": COMPLEX_SYL_FACTOR - 1,
    }
    result = {
        name: stat(stats[name], description.format(**params), share=stats.get("p" + name[1:]))
        for name, description in BASIC_STATS.items()
    }
    if analysis.options.distributions:
        for name, description in BASIC_DISTRIBUTIONS.items():
            counts = {str(key): count for key, count in stats[name].items() if count}
            result[name] = {"value": counts, "description": description}
    return result, []
