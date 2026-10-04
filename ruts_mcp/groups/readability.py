from ..analysis import Analysis, GroupResult, stat

MIN_SENTS = 30

READABILITY_STATS = {
    "consensus_grade": "Сводный класс: медиана формул класса и индекса Флеша, переведенного "
    "в класс; число лет обучения, нужное для понимания текста",
    "flesch_kincaid_grade": "Тест Флеша-Кинкайда: число лет обучения по длине предложений "
    "в словах и слов в слогах",
    "flesch_reading_easy": "Индекс Флеша: номинально от 0 до 100, чем выше, тем легче текст",
    "coleman_liau_index": "Индекс Колман-Лиау: число лет обучения по буквам и предложениям "
    "на 100 слов",
    "smog_index": "Индекс SMOG: число лет обучения по словам от 5 слогов на предложение",
    "automated_readability_index": "Автоматический индекс удобочитаемости (ARI): число лет "
    "обучения по длине слов в буквах и предложений в словах",
    "lix": "Индекс LIX: средняя длина предложения плюс процент слов от 7 букв; "
    "прочтение по шкале Бьёрнссона",
    "rix": "Индекс RIX: слова от 7 букв на предложение; класс по таблице Андерсона",
    "sis_grade": "Формула Соловьёва, Иванова, Солнышкиной (2023): число лет обучения",
    "matskovsky_index": "Формула Мацковского (1976), первая для русского языка: чем выше, "
    "тем сложнее текст; шкалы у нее нет",
    "dale_chall_index": "Индекс Дейла-Чейла в адаптации plainrussian: число лет обучения "
    "по доле слов от 5 слогов и длине предложений",
    "gunning_fog_index": "Индекс Ганнинга в адаптации plainrussian: число лет обучения "
    "по длине предложений и доле слов от 5 слогов",
    "reading_time": "Время чтения в минутах при скорости 180 слов в минуту",
}
# Шкалы LIX (Björnsson, 1968) и RIX (Anderson, 1983) из документации ruTS, нижние границы включительно
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
        сводный класс идет первым. Формулы класса и индекс Флеша переводятся
        в ступень обучения и возраст по таблице ruTS, LIX и RIX - по шкалам
        Бьёрнссона и Андерсона, у формулы Мацковского шкалы нет. Текст короче
        30 предложений получает предупреждение: формулы на нем неустойчивы

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
    from ruts.readability_stats import flesch_reading_easy_to_grade, grade_to_age

    rs = ReadabilityStats(analysis.basic, preset=analysis.options.preset)
    values = rs.get_stats()
    grade_stats = {"consensus_grade", *rs.grade_stats}

    def age(grade: float) -> str:
        return grade_to_age(grade, rs.grade_age_levels, rs.postgraduate_level)

    interpretations = {name: rs.describe_grade(name) for name in grade_stats}
    interpretations["flesch_reading_easy"] = age(
        flesch_reading_easy_to_grade(values["flesch_reading_easy"])
    )
    interpretations["lix"] = _lix_level(values["lix"])
    interpretations["rix"] = age(_rix_grade(values["rix"]))
    stats = {
        name: stat(values[name], description, interpretation=interpretations.get(name))
        for name, description in READABILITY_STATS.items()
    }
    warnings = []
    if analysis.basic.n_sents < MIN_SENTS:
        warnings.append(
            f"Предложений в тексте: {analysis.basic.n_sents}. Формулы удобочитаемости "
            f"рассчитаны на тексты в десятки предложений (SMOG - на выборку из {MIN_SENTS}), "
            "на коротком тексте отдельные формулы неустойчивы: опирайтесь на сводный класс"
        )
    return stats, warnings


def _lix_level(lix: float) -> str:
    """Уровень текста по шкале LIX"""
    return next((level for bound, level in LIX_LEVELS if lix >= bound), LIX_BELOW)


def _rix_grade(rix: float) -> int:
    """Класс по таблице RIX; от последней границы - 13 лет обучения, университет"""
    return next((grade for bound, grade in RIX_GRADES if rix >= bound), 1)
