from collections import Counter
from collections.abc import Sequence

from ..analysis import Analysis, GroupResult, stat, undefined_warnings

MIN_WORDS = 200
MAX_WORDS = 1000
TOP_FOUND = 20

# Пояснения к описаниям ruTS: что считает метрика
STYLE_NOTES = {
    "classic_nausea": "квадратный корень из числа вхождений самого частого слова; растет "
    "с длиной текста",
    "academic_nausea": "доля вхождений {top_n} самых частых слов среди всех слов",
    "water": "доля незначимых слов - союзов, частиц, предлогов, местоимений, междометий, "
    "вводных слов",
    "spam": "доля повторов - вхождений слова, кроме первого; растет с длиной текста",
    "zipf_naturalness": "согласие частот {top_n} самых частых слов с законом Ципфа",
    "verbal_nouns": "существительные на -ние, -тие, -ствие, -ция; маркер канцелярита",
    "compound_prepositions": "в целях, в связи с, в рамках и т. п.; маркер канцелярита",
    "parentheticals": "таким образом, как правило, конечно и т. п.; маркер канцелярита",
    "cliches": "из списка ruTS - на сегодняшний день, в настоящее время и т. п.; "
    "маркер канцелярита",
}
FOUND_NOTE = (
    "count - число вхождений, found - найденные слова и фразы с частотами (до {top} самых частых)"
)
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
        и megaindex; у маркеров канцелярита норм нет, зато есть число вхождений
        и найденные слова и фразы (officialese_markers). Добавлены число слов
        и самые частые словоформы, по которым считаются тошнота и естественность
        по Ципфу. Текст короче 200 или длиннее 1000 слов получает предупреждение: нормы рассчитаны на тексты в несколько
        сотен слов, а тошнота и заспамленность растут с длиной текста

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
    n_words = len(ss.words)
    found = officialese_markers(ss.forms, ss.cliches_list)
    stats = {
        "n_words": stat(n_words, "Число слов, по которым считаются метрики"),
        "top_words": stat(
            dict(Counter(ss.words).most_common(ss.top_n)),
            f"{ss.top_n} самых частых словоформ с частотами: по ним считаются академическая "
            "тошнота и естественность по Ципфу, по первой - классическая тошнота",
        ),
    }
    for name, value in ss.get_stats().items():
        note = STYLE_NOTES.get(name, "").format(top_n=ss.top_n)
        details = None
        if name in found:
            note += "; " + FOUND_NOTE.format(top=TOP_FOUND)
            counts = Counter(found[name])
            details = {"count": len(found[name]), "found": dict(counts.most_common(TOP_FOUND))}
        description = ": ".join(filter(None, (STYLE_STATS_DESC[name], note)))
        stats[name] = stat(value, description, interpretation=ss.describe(name), details=details)
    warnings = []
    if n_words < MIN_WORDS:
        warnings.append(
            f"Слов в тексте: {n_words}, меньше {MIN_WORDS}. Нормы сервисов рассчитаны "
            "на тексты сайтов в несколько сотен слов: на коротком тексте тошнота, "
            "заспамленность и естественность по Ципфу неинформативны, их прочтение "
            "по нормам - грубая оценка"
        )
    elif n_words > MAX_WORDS:
        warnings.append(
            f"Слов в тексте: {n_words}, больше {MAX_WORDS}. Классическая тошнота "
            "и заспамленность растут с длиной текста, а нормы сервисов рассчитаны на тексты "
            "сайтов в несколько сотен слов: выход за норму на длинном тексте ожидаем, "
            "прочтение по нормам - грубая оценка"
        )
    for name, reason in STYLE_REASONS.items():
        warnings += undefined_warnings({name: stats[name]}, reason)
    return stats, warnings


def officialese_markers(forms: Sequence[str], cliches: Sequence[str]) -> dict[str, list[str]]:
    """
    Маркеры канцелярита, найденные в тексте, как их считает StyleStats

    Аргументы:
        forms (list[str]): Словоформы текста в нижнем регистре
        cliches (list[str]): Штампы

    Вывод:
        dict[str, list[str]]: Имя метрики - найденные слова и фразы по порядку

    Пример использования:
        >>> found = officialese_markers(["ввиду", "этого", "мы", "конечно", "решение"], [])
        >>> found["compound_prepositions"], found["parentheticals"], found["verbal_nouns"]
        (['ввиду'], ['конечно'], ['решение'])
    """
    from ruts.constants import COMPOUND_PREPOSITIONS, PARENTHETICALS
    from ruts.style_stats import expand_phrases, is_parenthetical
    from ruts.utils import find_phrases, is_verbal_noun, parse_word

    def phrases(items: Sequence[str], expand: bool = True) -> list[tuple[int, int]]:
        return find_phrases(forms, expand_phrases(forms, items) if expand else items)

    spans = phrases(PARENTHETICALS, expand=False)
    covered = {position for start, end in spans for position in range(start, end)}
    singles = [
        (position, position + 1)
        for position, word in enumerate(forms)
        if position not in covered and is_parenthetical(word)
    ]
    found = {
        "compound_prepositions": phrases(COMPOUND_PREPOSITIONS),
        "parentheticals": sorted(spans + singles),
        "cliches": phrases(cliches),
    }
    markers = {
        name: [" ".join(forms[start:end]) for start, end in items] for name, items in found.items()
    }
    markers["verbal_nouns"] = [
        word
        for word in forms
        if (parse := parse_word(word)).tag.POS == "NOUN" and is_verbal_noun(parse.normal_form)
    ]
    return markers
