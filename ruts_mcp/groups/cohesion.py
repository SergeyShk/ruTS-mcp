from ..analysis import Analysis, GroupResult, stat, undefined_warnings


def cohesion_group(analysis: Analysis) -> GroupResult:
    """
    Статистики связности текста по образцу Coh-Metrix и TAACO

    Описание:
        Метрики CohesionStats из ruTS по строке: части речи, время и вид -
        по pymorphy3, коннекторы - по словарю ruTS. Повторы между предложениями
        лежат от 0 до 1 и не определены на тексте из одного предложения, как
        темпоральная связность без глаголов в соседних предложениях; такие
        метрики отдаются как None и перечисляются в предупреждении

    Аргументы:
        analysis (Analysis): Текст и настройки

    Вывод:
        tuple[dict[str, Any], list[str]]: Имя метрики ruTS - ее значение и описание;
            предупреждения

    Исключения:
        SourceError: Если в тексте нет слов

    Пример использования:
        >>> stats, warnings = cohesion_group(Analysis("Мама мыла раму. Мама устала."))
        >>> stats["noun_overlap_adjacent"]
        {'value': 1.0, 'description': 'Повтор существительных в соседних предложениях, от 0 до 1'}
    """
    from ruts import CohesionStats
    from ruts.constants import COHESION_STATS_DESC

    stats = {
        name: stat(
            value,
            COHESION_STATS_DESC[name] + (", от 0 до 1" if "_overlap_" in name else ""),
        )
        for name, value in CohesionStats(analysis.text).get_stats().items()
    }
    warnings = undefined_warnings(
        stats,
        "повторы считаются по парам предложений, а в тексте одно предложение, "
        "или в соседних предложениях нет глаголов для темпоральной связности",
    )
    return stats, warnings
