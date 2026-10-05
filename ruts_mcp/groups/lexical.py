from collections import defaultdict
from typing import Any

from ..analysis import Analysis, GroupResult, stat, undefined_warnings
from ..data import FREQ_DICT_TITLE, freq_dict, missing_warning

CONTENT_WORDS = (
    "существительных, прилагательных, глаголов (с причастиями и деепричастиями) и наречий"
)
BAND_NOTE = "самых частых лемм по списку Шарова, от 0 до 1"
# Пояснения к описаниям ruTS: по чему считается метрика и как ее читать
LEXICAL_NOTES = {
    "coverage": "по словарю Ляшевской и Шарова (НКРЯ, 52 138 лемм), от 0 до 1; средние "
    "по словарю считаются только по найденным словам",
    "mean_ipm": "употреблений леммы на миллион слов корпуса, среднее по найденным словам; "
    "чем ниже, тем реже слова",
    "mean_ipm_content": f"то же среди {CONTENT_WORDS}; признак FREQ2 формулы Соловьева, "
    "Иванова, Солнышкиной (2023), в статье от 200 до 1000",
    "mean_log_ipm": "средний десятичный логарифм ipm найденных слов, меньше зависит "
    "от самых частых слов",
    "mean_log_ipm_content": f"то же среди {CONTENT_WORDS}",
    "mean_range": "в скольких из 100 частей корпуса встречается лемма, среднее по найденным "
    "словам; чем ниже, тем специальнее лексика",
    "mean_dispersion": "равномерность употребления леммы по корпусу (коэффициент Жуйана, "
    "от 0 до 100), среднее по найденным словам",
    "surprisal": "средняя неожиданность слова по частотам словаря (униграммная модель); "
    "чем выше, тем реже слова",
    "perplexity": "2 в степени сюрпризала",
    "p_top1000": BAND_NOTE,
    "p_top2000": BAND_NOTE,
    "p_top5000": BAND_NOTE,
    "p_top10000": BAND_NOTE,
    "p_beyond_top10000": BAND_NOTE,
    "lexical_density": f"доля {CONTENT_WORDS} среди слов, от 0 до 1",
}
NOT_FOUND_REASON = "ни одно слово текста не найдено в частотном словаре"
CONTENT_NOT_FOUND_REASON = "ни одно знаменательное слово текста не найдено в частотном словаре"
LEXICAL_REASONS = {
    "mean_ipm": NOT_FOUND_REASON,
    "mean_log_ipm": NOT_FOUND_REASON,
    "mean_range": NOT_FOUND_REASON,
    "mean_dispersion": NOT_FOUND_REASON,
    "mean_ipm_content": CONTENT_NOT_FOUND_REASON,
    "mean_log_ipm_content": CONTENT_NOT_FOUND_REASON,
}
OTHER_REASON = "значение не определено на таком тексте"


def lexical_group(analysis: Analysis) -> GroupResult:
    """
    Лексическая сложность текста по частотам русского языка

    Описание:
        Метрики LexicalStats из ruTS по образцу TAALES: насколько слова текста
        редки относительно языка. Частотность, диапазон, дисперсия, сюрпризал
        и доля найденных слов считаются по частотному словарю Ляшевской
        и Шарова, доли частотных полос и лексическая плотность - по вшитому
        списку и разбору pymorphy3. Без скачанного словаря метрики по словарю
        отдаются как None, а предупреждение говорит, как его скачать. Числа
        словами не считаются

    Аргументы:
        analysis (Analysis): Текст и настройки

    Вывод:
        tuple[dict[str, Any], list[str]]: Имя метрики ruTS - ее значение и описание;
            предупреждения

    Исключения:
        SourceError: Если в тексте нет слов

    Пример использования:
        >>> stats, warnings = lexical_group(Analysis("Кот сидел на окне и смотрел на птиц"))
        >>> stats["p_top1000"]["value"], stats["lexical_density"]["value"]
        (0.75, 0.625)
    """
    from ruts import LexicalStats
    from ruts.constants import LEXICAL_STATS_DESC
    from ruts.exceptions import DatasetNotFoundError

    ls = LexicalStats(analysis.text, freq_dict=freq_dict())
    stats: dict[str, Any] = {}
    missing = []
    for name, title in LEXICAL_STATS_DESC.items():
        try:
            value = getattr(ls, name)
        except DatasetNotFoundError:
            value = None
            missing.append(name)
        description = ": ".join(filter(None, (title, LEXICAL_NOTES.get(name, ""))))
        stats[name] = stat(value, description)
    warnings = []
    if missing:
        warnings.append(
            missing_warning(FREQ_DICT_TITLE, f"метрики {', '.join(missing)} не посчитаны")
        )
    by_reason: dict[str, dict[str, Any]] = defaultdict(dict)
    for name, item in stats.items():
        if name not in missing:
            by_reason[LEXICAL_REASONS.get(name, OTHER_REASON)][name] = item
    for reason, items in by_reason.items():
        warnings += undefined_warnings(items, reason)
    return stats, warnings
