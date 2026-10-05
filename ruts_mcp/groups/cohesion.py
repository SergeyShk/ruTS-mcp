from collections import defaultdict
from typing import Any

from ..analysis import Analysis, GroupResult, stat, undefined_warnings

# Определения из таблицы атрибутов документации ruTS там, где короткого описания мало
COHESION_NOTES = {
    "noun_overlap_adjacent": "доля пар соседних предложений с общим существительным",
    "noun_overlap_all": "доля всех пар предложений с общим существительным",
    "argument_overlap_adjacent": "доля пар соседних предложений с общим существительным "
    "или местоимением",
    "argument_overlap_all": "доля всех пар предложений с общим существительным или местоимением",
    "content_overlap_adjacent": "доля пар соседних предложений с общим знаменательным словом",
    "content_overlap_all": "доля всех пар предложений с общим знаменательным словом",
    "content_overlap_prop_adjacent": "средняя по парам соседних предложений доля общих "
    "знаменательных слов",
    "content_overlap_prop_all": "средняя по всем парам предложений доля общих знаменательных слов",
    "tense_repetition": "доля пар соседних предложений с одинаковым преобладающим временем",
    "aspect_repetition": "доля пар соседних предложений с одинаковым преобладающим видом",
    "temporal_cohesion": "среднее повтора времени и вида",
}
OVERLAP_REASON = "повторы считаются по парам предложений, а в тексте одно предложение"
TEMPORAL_REASON = (
    "в тексте одно предложение или в соседних предложениях нет форм глагола со временем "
    "или видом (у повелительного наклонения и инфинитива нет времени)"
)
COHESION_REASONS = {
    "pronoun_noun_ratio": "в тексте нет существительных",
    "p_given": "в тексте нет знаменательных слов",
    "tense_repetition": TEMPORAL_REASON,
    "aspect_repetition": TEMPORAL_REASON,
    "temporal_cohesion": TEMPORAL_REASON,
}
OTHER_REASON = "значение не определено на таком тексте"


def cohesion_group(analysis: Analysis) -> GroupResult:
    """
    Статистики связности текста по образцу Coh-Metrix и TAACO

    Описание:
        Метрики CohesionStats из ruTS по строке: части речи, время и вид -
        по pymorphy3, коннекторы - по словарю ruTS. Повторы и доли пар лежат
        от 0 до 1. Метрики, не определенные на тексте, отдаются как None
        и перечисляются в предупреждениях по причинам: одно предложение,
        нет существительных или знаменательных слов, нет форм глагола
        со временем или видом в соседних предложениях

    Аргументы:
        analysis (Analysis): Текст и настройки

    Вывод:
        tuple[dict[str, Any], list[str]]: Имя метрики ruTS - ее значение и описание;
            предупреждения

    Исключения:
        SourceError: Если в тексте нет слов

    Пример использования:
        >>> stats, warnings = cohesion_group(Analysis("Мама мыла раму. Мама устала."))
        >>> stats["noun_overlap_adjacent"]["value"]
        1.0
    """
    from ruts import CohesionStats
    from ruts.constants import COHESION_STATS_DESC

    stats = {}
    for name, value in CohesionStats(analysis.text).get_stats().items():
        description = COHESION_STATS_DESC[name]
        if name in COHESION_NOTES:
            description = f"{description}: {COHESION_NOTES[name]}, от 0 до 1"
        stats[name] = stat(value, description)
    by_reason: dict[str, dict[str, Any]] = defaultdict(dict)
    for name, item in stats.items():
        reason = (
            OVERLAP_REASON if "_overlap_" in name else COHESION_REASONS.get(name, OTHER_REASON)
        )
        by_reason[reason][name] = item
    warnings = [
        w for reason, items in by_reason.items() for w in undefined_warnings(items, reason)
    ]
    return stats, warnings
