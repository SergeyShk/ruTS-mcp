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
    "noun_overlap_2_sent": "доля существительных предложения, повторенных в одном из двух "
    "следующих предложений",
    "argument_overlap_2_sent": "доля существительных и местоимений предложения, повторенных "
    "в одном из двух следующих предложений",
    "content_overlap_2_sent": "доля знаменательных слов предложения, повторенных в одном из двух "
    "следующих предложений",
    "noun_overlap_para": "доля существительных абзаца (строки текста), повторенных в следующем "
    "абзаце",
    "argument_overlap_para": "доля существительных и местоимений абзаца (строки текста), "
    "повторенных в следующем абзаце",
    "content_overlap_para": "доля знаменательных слов абзаца (строки текста), повторенных "
    "в следующем абзаце",
    "tense_repetition": "доля пар соседних предложений с одинаковым преобладающим временем",
    "aspect_repetition": "доля пар соседних предложений с одинаковым преобладающим видом",
    "temporal_cohesion": "среднее повтора времени и вида",
}
CONNECTOR_NOTES = {
    "connectors_inter": "стоят в начале предложения - «Однако», «Поэтому», «Кроме того», "
    "«После этого», «Ибо»; кроме подчинительных союзов и предлогов, которые относятся "
    "к своему предложению («Когда он пришел», «Несмотря на дождь»)",
    "connectors_intra": "все, кроме межпредложенческих, - не в начале предложения "
    "(«Он, однако, ушел») и подчинительные союзы и предлоги в начале («Когда он пришел»)",
}
OVERLAP_REASON = "повторы считаются по парам предложений, а в тексте одно предложение"
FEW_SENTS_REASON = (
    "повтор в двух следующих предложениях считается для предложений, за которыми идут еще два, "
    "а в тексте меньше трех предложений"
)
ONE_PARAGRAPH_REASON = (
    "повтор в соседних абзацах считается по парам абзацев, а в тексте один абзац (абзац - "
    "строка текста; строка без знаменательных слов, например номер главы, присоединяется "
    "к соседнему абзацу)"
)
OVERLAP_ITEMS = {
    "noun": "существительных",
    "argument": "существительных и местоимений",
    "content": "знаменательных слов",
}
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
        по pymorphy3, коннекторы - по словарю ruTS с контекстными правилами,
        отдельно межпредложенческие и внутрипредложенческие; абзац - строка
        текста, как в TAACO. Повторы и доли пар лежат от 0 до 1. Метрики,
        не определенные на тексте, отдаются как None и перечисляются
        в предупреждениях по причинам: одно предложение, меньше трех
        предложений, один абзац, нет существительных или знаменательных слов,
        нет форм глагола со временем или видом в соседних предложениях

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

    cs = CohesionStats(analysis.text)
    stats = {}
    for name, value in cs.get_stats().items():
        description = COHESION_STATS_DESC[name]
        if name in COHESION_NOTES:
            description = f"{description}: {COHESION_NOTES[name]}, от 0 до 1"
        elif name in CONNECTOR_NOTES:
            description = f"{description}: {CONNECTOR_NOTES[name]}"
        stats[name] = stat(value, description)
    by_reason: dict[str, dict[str, Any]] = defaultdict(dict)
    for name, item in stats.items():
        kind = OVERLAP_ITEMS.get(name.split("_")[0])
        if name.endswith("_2_sent"):
            reason = (
                FEW_SENTS_REASON
                if cs.n_sents < 3
                else f"в предложениях текста, кроме двух последних, нет {kind}"
            )
        elif name.endswith("_para"):
            reason = (
                ONE_PARAGRAPH_REASON
                if cs.n_paragraphs < 2
                else f"в абзацах текста, кроме последнего, нет {kind}"
            )
        elif "_overlap_" in name:
            reason = OVERLAP_REASON
        else:
            reason = COHESION_REASONS.get(name, OTHER_REASON)
        by_reason[reason][name] = item
    warnings = [
        w for reason, items in by_reason.items() for w in undefined_warnings(items, reason)
    ]
    return stats, warnings
