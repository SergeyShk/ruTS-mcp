from typing import Any

from ..analysis import Analysis, GroupResult, stat, undefined_warnings


def morph_group(analysis: Analysis) -> GroupResult:
    """
    Морфологический профиль текста: части речи, грамматические признаки и доли форм глагола

    Описание:
        Признаки MorphStats из ruTS по разбору pymorphy3 без контекста, так что
        омонимия не снимается. Значение признака - число слов с каждым его
        значением по убыванию, с подписями значений из ruTS; слова, у которых
        признак не определен, не считаются. Доли форм глагола - get_markers;
        доля без форм, от которых она считается, отдается как None и
        перечисляется в предупреждении

    Аргументы:
        analysis (Analysis): Текст и настройки

    Вывод:
        tuple[dict[str, Any], list[str]]: Имя признака или доли ruTS - значение
            и описание; предупреждения

    Исключения:
        SourceError: Если в тексте нет слов

    Пример использования:
        >>> stats, warnings = morph_group(Analysis("Красивый дом у реки."))
        >>> stats["pos"]["value"]
        {'Имя существительное': 2, 'Имя прилагательное': 1, 'Предлог': 1}
        >>> stats["p_perfective"]["value"], len(warnings)
        (None, 1)
    """
    from ruts import MorphStats
    from ruts.constants import MORPHOLOGY_MARKERS_DESC, MORPHOLOGY_STATS_DESC

    ms = MorphStats(analysis.text)
    result: dict[str, Any] = {}
    for name, counts in ms.get_stats(filter_none=True).items():
        feature = MORPHOLOGY_STATS_DESC[name]
        ranked = sorted(counts.items(), key=lambda item: -item[1])
        result[name] = {
            "value": {feature["values"].get(code, code): count for code, count in ranked},
            "description": f"{feature['name']}: число слов с каждым значением",
        }
    markers = {
        name: stat(share, f"{MORPHOLOGY_MARKERS_DESC[name]}, доля от 0 до 1")
        for name, share in ms.get_markers().items()
    }
    warnings = undefined_warnings(markers, "в тексте нет форм глагола, от которых считается доля")
    return result | markers, warnings
