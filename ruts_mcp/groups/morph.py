from collections import defaultdict
from typing import Any

from ..analysis import Analysis, GroupResult, clean, stat, undefined_warnings


def morph_group(analysis: Analysis) -> GroupResult:
    """
    Морфологический профиль текста: части речи, грамматические признаки и доли форм глагола

    Описание:
        Признаки MorphStats из ruTS по разбору pymorphy3 без контекста, так что
        омонимия не снимается. Значение признака - число слов с каждым его
        значением по убыванию, с подписями значений из ruTS, доля - от всех
        слов; слова, у которых признак не определен, не считаются. Доли форм
        глагола - get_markers; доля без форм, от которых она считается (база
        из описания ruTS: личные формы, формы глагола, формы с видом),
        отдается как None и перечисляется в предупреждении

    Аргументы:
        analysis (Analysis): Текст и настройки

    Вывод:
        tuple[dict[str, Any], list[str]]: Имя признака или доли ruTS - значение,
            доля и описание; предупреждения

    Исключения:
        SourceError: Если в тексте нет слов

    Пример использования:
        >>> stats, warnings = morph_group(Analysis("Красивый дом у реки."))
        >>> stats["pos"]["value"], stats["pos"]["share"]["Предлог"]
        ({'Имя существительное': 2, 'Имя прилагательное': 1, 'Предлог': 1}, 0.25)
        >>> stats["p_perfective"]["value"], len(warnings)
        (None, 3)
    """
    from ruts import MorphStats
    from ruts.constants import MORPHOLOGY_MARKERS_DESC, MORPHOLOGY_STATS_DESC

    ms = MorphStats(analysis.text)
    n_words = len(ms.words)
    result: dict[str, Any] = {}
    for name, counts in ms.get_stats(filter_none=True).items():
        feature = MORPHOLOGY_STATS_DESC[name]
        ranked = [
            (feature["values"].get(code, code), count)
            for code, count in sorted(counts.items(), key=lambda item: -item[1])
        ]
        result[name] = {
            "value": dict(ranked),
            "share": {label: clean(count / n_words) for label, count in ranked},
            "description": f"{feature['name']}: число слов с каждым значением и их доля "
            "от всех слов",
        }
    by_base: dict[str, dict[str, Any]] = defaultdict(dict)
    for name, share in ms.get_markers().items():
        description = MORPHOLOGY_MARKERS_DESC[name]
        result[name] = stat(share, f"{description}, доля от 0 до 1")
        by_base[description.split(" среди ")[-1]][name] = result[name]
    warnings = [
        warning
        for base, markers in by_base.items()
        for warning in undefined_warnings(
            markers, f"в тексте нет {base}, от которых считается доля"
        )
    ]
    return result, warnings
