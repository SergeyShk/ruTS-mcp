from ..analysis import Analysis, GroupResult, stat

MIN_SENTS = 30

READABILITY_STATS = {
    "consensus_grade": "Сводный класс: медиана формул класса и индекса Флеша, переведенного "
    "в класс; число лет обучения, нужное для понимания текста",
    "flesch_kincaid_grade": "Тест Флеша-Кинкайда: число лет обучения по длине предложений "
    "в словах и слов в слогах",
    "flesch_reading_easy": "Индекс Флеша: номинально от 0 до 100, чем выше, тем легче текст; "
    "прочтение по шкале Флеша",
    "coleman_liau_index": "Индекс Колман-Лиау: число лет обучения по буквам и предложениям "
    "на 100 слов",
    "smog_index": "Индекс SMOG: число лет обучения по словам от {smog_syllables} слогов "
    "на предложение",
    "automated_readability_index": "Автоматический индекс удобочитаемости (ARI): число лет "
    "обучения по длине слов в буквах и предложений в словах",
    "lix": "Индекс LIX: средняя длина предложения плюс процент слов от {lix_letters} букв; "
    "прочтение по шкале Бьёрнссона",
    "rix": "Индекс RIX: слова от {lix_letters} букв на предложение; класс по таблице Андерсона",
    "sis_grade": "Формула Соловьёва, Иванова, Солнышкиной (2023): класс школы по средней "
    "длине слова в буквах и предложения в словах",
    "matskovsky_index": "Формула Мацковского (1976), первая для русского языка: чем выше, "
    "тем сложнее текст; шкалы у нее нет",
    "dale_chall_index": "Индекс Дейла-Чейла в адаптации plainrussian: число лет обучения "
    "по доле слов от {smog_syllables} слогов и длине предложений",
    "gunning_fog_index": "Индекс Ганнинга в адаптации plainrussian: число лет обучения "
    "по длине предложений и доле слов от {smog_syllables} слогов",
    "reading_time": "Время чтения в минутах при скорости {speed} слов в минуту",
}


def readability_group(analysis: Analysis) -> GroupResult:
    """
    Метрики удобочитаемости текста с переводом в класс школы и возраст читателя

    Описание:
        Метрики ReadabilityStats из ruTS с пресетом коэффициентов из настроек;
        сводный класс идет первым. Прочтение метрики дает ruTS (describe):
        формулы класса и RIX - ступень обучения и возраст, индекс Флеша и LIX -
        полоса своей шкалы; у формулы Мацковского и времени чтения шкалы нет.
        Текст короче 30 предложений получает предупреждение: формулы на нем
        неустойчивы

    Аргументы:
        analysis (Analysis): Текст и настройки

    Вывод:
        tuple[dict[str, Any], list[str]]: Имя метрики ruTS - ее значение, прочтение
            и описание; предупреждения

    Исключения:
        SourceError: Если в тексте нет слов

    Пример использования:
        >>> stats, warnings = readability_group(Analysis("Мама мыла раму."))
        >>> stats["consensus_grade"]["interpretation"]
        '1-3-й класс (6-8 лет)'
    """
    from ruts import ReadabilityStats

    rs = ReadabilityStats(analysis.basic, preset=analysis.options.preset)
    values = rs.get_stats()
    params = {
        "smog_syllables": rs.smog_complex_syl_factor,
        "lix_letters": rs.lix_long_word_letter_factor,
        "speed": rs.reading_speed,
    }
    stats = {
        name: stat(values[name], description.format(**params), interpretation=rs.describe(name))
        for name, description in READABILITY_STATS.items()
    }
    warnings = []
    if analysis.basic.n_sents < MIN_SENTS:
        warnings.append(
            f"Предложений в тексте: {analysis.basic.n_sents}, меньше {MIN_SENTS}. Формулы "
            "удобочитаемости опираются на среднюю длину предложения, исходный SMOG - "
            "на выборку из 30 предложений: на коротком тексте значения неустойчивы, "
            "включая сводный класс, это грубая оценка"
        )
    return stats, warnings
