from collections import Counter, defaultdict
from typing import Any

from ..analysis import NO_WORDS_WARNING, Analysis, GroupResult, stat, undefined_warnings
from ..data import STRESS_DICT_TITLE, missing_warning, stress_dict

TOP_SCHEMES = 10
MAX_SCHEME = 32
LADDER_PYRRHICS = 0.5

# Пояснения к описаниям ruTS: что считает статистика
VERSE_NOTES = {
    "n_lines": "строки с русскими словами",
    "n_stanzas": "строфы разделяются пустыми строками",
    "meter": "силлабо-тонический метр по ударениям: ямб, хорей, дактиль, амфибрахий или анапест",
    "n_feet": "преобладающее число стоп в строке",
    "p_deviations": "доля ударений многосложных слов на слабых позициях метра, от 0 до 1",
    "p_pyrrhics": "доля сильных позиций метра без ударения, от 0 до 1",
    "p_rhymed": "доля строк, рифмующихся с другой строкой той же строфы не дальше "
    "{window} строк, от 0 до 1",
    "p_masculine": "ударение на последнем слоге строки, от 0 до 1",
    "p_feminine": "один заударный слог в конце строки, от 0 до 1",
    "p_dactylic": "два заударных слога в конце строки, от 0 до 1",
}
RHYME_SCHEMES = (
    "Самые частые схемы рифмовки строф, до {top}, и число строф с каждой: рифмующиеся строки "
    "обозначены одной буквой по порядку появления, нерифмованные - дефисом (ABAB, -A-A); "
    f"схема длиннее {MAX_SCHEME} строк обрезана с многоточием"
)
LADDER_WARNING = (
    "Метр {meter} ({feet}-стопный, доля пропущенных ударений {pyrrhics}) может быть случайным: "
    "так бывает со стихом, записанным лесенкой, и с текстом, где строка - не стих. Стих "
    "лесенкой соберите в строки по смыслу и посчитайте заново"
)
METER_REASON = (
    "метр не определен: текст не силлабо-тонический (дольник, акцентный стих, верлибр, проза) "
    "или в нем меньше {min_stresses} словарных ударений многосложных слов"
)
CLAUSULA_REASON = "ни в одной строке не найдено ударение последнего слова"
VERSE_REASONS = {
    "meter": METER_REASON,
    "n_feet": METER_REASON,
    "p_deviations": METER_REASON,
    "p_pyrrhics": METER_REASON,
    "p_masculine": CLAUSULA_REASON,
    "p_feminine": CLAUSULA_REASON,
    "p_dactylic": CLAUSULA_REASON,
}
NO_LINES_REASON = "в тексте нет строк с русскими словами"
OTHER_REASON = "значение не определено на таком тексте"


def verse_group(analysis: Analysis) -> GroupResult:
    """
    Стиховедческие статистики текста: метр, рифма и окончания строк

    Описание:
        Статистики VerseStats из ruTS: ударения из знаков ударения в тексте,
        по словарю ударений Козиева и правилам, метр по алгоритму Барахнина,
        Кожемякиной и Кузнецовой, рифма по фонетическому ключу окончания
        внутри строфы; к ним добавлены самые частые схемы рифмовки строф.
        Без скачанного словаря и у текста
        без слов, кроме чисел, группа пуста, а предупреждение называет причину.
        Статистики, не определенные на тексте (метр не подобран, ударения
        последних слов строк не найдены, нет строк с русскими словами),
        отдаются как None с причиной

    Аргументы:
        analysis (Analysis): Текст и настройки

    Вывод:
        tuple[dict[str, Any], list[str]]: Имя статистики ruTS - ее значение и описание;
            предупреждения
    """
    from ruts import VerseStats
    from ruts.constants import RHYME_WINDOW, VERSE_MIN_STRESSES, VERSE_STATS_DESC
    from ruts.exceptions import DatasetNotFoundError, SourceError

    try:
        vs = VerseStats(analysis.text, stress_dict=stress_dict())
    except DatasetNotFoundError:
        return {}, [missing_warning(STRESS_DICT_TITLE, "группа verse не посчитана")]
    except SourceError:
        return {}, [NO_WORDS_WARNING.format(group="verse")]
    stats: dict[str, Any] = {}
    for name, value in vs.get_stats().items():
        note = VERSE_NOTES.get(name, "").format(window=RHYME_WINDOW)
        stats[name] = stat(value, ": ".join(filter(None, (VERSE_STATS_DESC[name], note))))
    schemes = Counter(
        scheme if len(scheme) <= MAX_SCHEME else scheme[: MAX_SCHEME - 1] + "…"
        for scheme in vs.rhyme_schemes
    )
    stats["rhyme_schemes"] = stat(
        dict(schemes.most_common(TOP_SCHEMES)), RHYME_SCHEMES.format(top=TOP_SCHEMES)
    )
    if not vs.n_lines:
        return stats, undefined_warnings(stats, NO_LINES_REASON)
    by_reason: dict[str, dict[str, Any]] = defaultdict(dict)
    for name, item in stats.items():
        by_reason[VERSE_REASONS.get(name, OTHER_REASON)][name] = item
    warnings = []
    for reason, items in by_reason.items():
        warnings += undefined_warnings(items, reason.format(min_stresses=VERSE_MIN_STRESSES))
    if vs.meter is not None and (vs.n_feet == 1 or vs.p_pyrrhics > LADDER_PYRRHICS):
        warnings.append(
            LADDER_WARNING.format(
                meter=vs.meter, feet=vs.n_feet, pyrrhics=stats["p_pyrrhics"]["value"]
            )
        )
    return stats, warnings
