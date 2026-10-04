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
    "smog_index": "Индекс SMOG: число лет обучения по словам от 5 слогов на предложение",
    "automated_readability_index": "Автоматический индекс удобочитаемости (ARI): число лет "
    "обучения по длине слов в буквах и предложений в словах",
    "lix": "Индекс LIX: средняя длина предложения плюс процент слов от 7 букв; "
    "прочтение по шкале Бьёрнссона",
    "rix": "Индекс RIX: слова от 7 букв на предложение; класс по таблице Андерсона",
    "sis_grade": "Формула Соловьёва, Иванова, Солнышкиной (2023): класс школы по средней "
    "длине слова в буквах и предложения в словах",
    "matskovsky_index": "Формула Мацковского (1976), первая для русского языка: чем выше, "
    "тем сложнее текст; шкалы у нее нет",
    "dale_chall_index": "Индекс Дейла-Чейла в адаптации plainrussian: число лет обучения "
    "по доле слов от 5 слогов и длине предложений",
    "gunning_fog_index": "Индекс Ганнинга в адаптации plainrussian: число лет обучения "
    "по длине предложений и доле слов от 5 слогов",
    "reading_time": "Время чтения в минутах при скорости 180 слов в минуту",
}
# Шкалы индекса Флеша (Flesch, 1948), LIX (Björnsson, 1968) и RIX (Anderson, 1983)
# из документации ruTS, нижние границы включительно
FLESCH_LEVELS = (
    (90, "5-й класс"),
    (80, "6-й класс"),
    (70, "7-й класс"),
    (60, "8-9-й класс"),
    (50, "10-11-й класс"),
    (30, "университет"),
)
FLESCH_BELOW = "выпускник университета"
LIX_LEVELS = (
    (60, "очень сложный текст: законы и канцелярский язык"),
    (50, "сложный текст: научно-популярная литература, официальные тексты"),
    (40, "текст средней сложности: журнальные статьи"),
    (30, "простой текст: художественная литература, газетные статьи"),
)
LIX_BELOW = "очень простой текст: детские книги"
RIX_GRADES = (
    (7.2, 13),
    (6.2, 12),
    (5.3, 11),
    (4.5, 10),
    (3.7, 9),
    (3.0, 8),
    (2.4, 7),
    (1.8, 6),
    (1.3, 5),
    (0.8, 4),
    (0.5, 3),
    (0.2, 2),
)


def readability_group(analysis: Analysis) -> GroupResult:
    """
    Метрики удобочитаемости текста с переводом в класс школы и возраст читателя

    Описание:
        Метрики ReadabilityStats из ruTS с пресетом коэффициентов из настроек;
        сводный класс идет первым. Формулы класса переводятся в ступень обучения
        и возраст по таблице ruTS, индекс Флеша, LIX и RIX - по шкалам Флеша,
        Бьёрнссона и Андерсона из документации ruTS, у формулы Мацковского шкалы
        нет. Текст короче 30 предложений получает предупреждение: формулы на нем
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
    from ruts.readability_stats import grade_to_age

    rs = ReadabilityStats(analysis.basic, preset=analysis.options.preset)
    values = rs.get_stats()
    grade_stats = {"consensus_grade", *rs.grade_stats}

    interpretations = {name: rs.describe_grade(name) for name in grade_stats}
    interpretations["flesch_reading_easy"] = _level(
        values["flesch_reading_easy"], FLESCH_LEVELS, FLESCH_BELOW
    )
    interpretations["lix"] = _level(values["lix"], LIX_LEVELS, LIX_BELOW)
    interpretations["rix"] = grade_to_age(
        _rix_grade(values["rix"]), rs.grade_age_levels, rs.postgraduate_level
    )
    stats = {
        name: stat(values[name], description, interpretation=interpretations.get(name))
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


def _level(value: float, levels: tuple[tuple[float, str], ...], below: str) -> str:
    """Уровень по шкале из нижних границ в порядке убывания"""
    return next((level for bound, level in levels if value >= bound), below)


def _rix_grade(rix: float) -> int:
    """Класс по таблице RIX; от последней границы - 13 лет обучения, университет"""
    return next((grade for bound, grade in RIX_GRADES if rix >= bound), 1)
