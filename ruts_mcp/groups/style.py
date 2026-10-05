from ..analysis import Analysis, GroupResult, stat, undefined_warnings

MIN_WORDS = 200

# Пояснения к описаниям ruTS: что считает метрика
STYLE_NOTES = {
    "classic_nausea": "квадратный корень из числа вхождений самого частого слова; растет "
    "с длиной текста",
    "academic_nausea": "доля вхождений {top_n} самых частых слов среди всех слов",
    "water": "доля незначимых слов - союзов, частиц, предлогов, местоимений, междометий, "
    "вводных слов",
    "spam": "доля повторов - вхождений слова, кроме первого",
    "zipf_naturalness": "согласие частот {top_n} самых частых слов с законом Ципфа",
    "verbal_nouns": "существительные на -ние, -тие, -ствие, -ция; маркер канцелярита",
    "compound_prepositions": "в целях, в связи с, в рамках и т. п.; маркер канцелярита",
    "parentheticals": "таким образом, как правило, конечно и т. п.; маркер канцелярита",
    "cliches": "из списка ruTS - на сегодняшний день, в настоящее время и т. п.; "
    "маркер канцелярита",
}
STYLE_REASONS = {
    "zipf_naturalness": "все слова текста встречаются по одному разу или в нем одно и то же слово",
    "verbal_nouns": "в тексте нет существительных",
}


def style_group(analysis: Analysis) -> GroupResult:
    """
    SEO-метрики стиля и маркеры канцелярита с прочтением по нормам сервисов

    Описание:
        Метрики StyleStats из ruTS по словоформам в нижнем регистре, без
        лемматизации; описание ruTS дополнено пояснением, что считает метрика.
        Прочтение дает ruTS (describe): тошнота - по нормам Advego, водность
        и заспамленность - по Text.ru, естественность по Ципфу - по pr-cy
        и megaindex; у маркеров канцелярита норм нет. Текст короче 200 слов
        получает предупреждение: нормы рассчитаны на тексты в несколько сотен слов

    Аргументы:
        analysis (Analysis): Текст и настройки

    Вывод:
        tuple[dict[str, Any], list[str]]: Имя метрики ruTS - ее значение, прочтение
            и описание; предупреждения

    Исключения:
        SourceError: Если в тексте нет слов

    Пример использования:
        >>> stats, warnings = style_group(Analysis("Мама мыла раму, а папа мыл окно."))
        >>> stats["water"]["value"], stats["water"]["interpretation"]
        (14.29, 'естественная водность по Text.ru')
    """
    from ruts import StyleStats
    from ruts.constants import STYLE_STATS_DESC

    ss = StyleStats(analysis.text)
    stats = {
        name: stat(
            value,
            f"{STYLE_STATS_DESC[name]}: {STYLE_NOTES[name].format(top_n=ss.top_n)}",
            interpretation=ss.describe(name),
        )
        for name, value in ss.get_stats().items()
    }
    warnings = []
    if len(ss.words) < MIN_WORDS:
        warnings.append(
            f"Слов в тексте: {len(ss.words)}, меньше {MIN_WORDS}. Нормы сервисов рассчитаны "
            "на тексты сайтов в несколько сотен слов: на коротком тексте тошнота, "
            "заспамленность и естественность по Ципфу неинформативны, их прочтение "
            "по нормам - грубая оценка"
        )
    for name, reason in STYLE_REASONS.items():
        warnings += undefined_warnings({name: stats[name]}, reason)
    return stats, warnings
