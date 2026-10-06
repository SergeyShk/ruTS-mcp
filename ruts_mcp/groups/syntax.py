import re
from collections import defaultdict
from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

from ..analysis import Analysis, GroupResult, stat, undefined_warnings
from ..data import SPACY_MODEL_TITLE, missing_warning, spacy_model

if TYPE_CHECKING:
    from spacy.language import Language
    from spacy.tokens import Doc

CHUNK_SIZE = 20_000
SENTENCE_END = re.compile(r"[.!?…]+\s+")

# Пояснения к описаниям ruTS там, где по названию статистику не прочитать
SYNTAX_NOTES = {
    "mean_dependency_distance": "расстояние в словах между словом и его вершиной; чем больше, "
    "тем больше нагрузка на память при чтении",
    "max_dependency_distance": "наибольшая длина зависимости в предложении, средняя "
    "по предложениям",
    "p_adjacent_dependencies": "доля зависимостей между соседними словами, от 0 до 1",
    "tree_depth": "наибольшее число связей от вершины предложения до слова",
    "leaves_per_sent": "листья - слова без зависимых",
    "nodes_per_leaf": "слов на лист; чем больше, тем ветвистее дерево",
    "verb_valency": "среднее число зависимых у финитного глагола",
    "mean_clause_len": "клауза - вершина предложения или придаточного со своими зависимыми; "
    "причастные и деепричастные обороты считаются отдельно",
    "p_complex_sents": "от 0 до 1",
    "modifiers_per_noun": "определения, числительные, местоимения, зависимые существительные "
    "и обороты при существительном",
    "genitive_chains_per_sent": "цепочка - два и более вложенных беспредложных определения "
    "в родительном падеже",
    "max_genitive_chain_len": "в словах: «повышение эффективности использования ресурсов» - 3",
    "p_passive": "среди глагольных форм, от 0 до 1",
    "p_agentless_passive": "пассив без указания на действующее лицо, от 0 до 1",
    "split_predicates_per_sent": "легкий глагол с именной частью вместо простого глагола: "
    "«осуществлять проверку», «оказать помощь», «принять участие»",
    "noun_verb_ratio": "чем больше, тем номинативнее стиль",
}
NO_LINKS_REASON = "в предложениях текста нет связей между словами"
NO_VERBS_REASON = "в тексте нет глагольных форм"
SYNTAX_REASONS = {
    "mean_dependency_distance": NO_LINKS_REASON,
    "std_dependency_distance": NO_LINKS_REASON,
    "max_dependency_distance": NO_LINKS_REASON,
    "p_adjacent_dependencies": NO_LINKS_REASON,
    "verb_valency": "в тексте нет финитных глаголов",
    "mean_coordination_chain_len": "в тексте нет сочинительных цепочек",
    "mean_clause_len": "в тексте нет клауз",
    "modifiers_per_noun": "в тексте нет существительных",
    "mean_participle_clause_len": "в тексте нет причастных оборотов",
    "mean_converb_clause_len": "в тексте нет деепричастных оборотов",
    "p_passive": NO_VERBS_REASON,
    "p_agentless_passive": "в тексте нет пассивных форм",
    "noun_verb_ratio": NO_VERBS_REASON,
}
OTHER_REASON = "значение не определено на таком тексте"


def text_chunks(text: str, size: int = CHUNK_SIZE) -> Iterator[str]:
    """
    Куски текста не длиннее size символов для разбора spaCy

    Описание:
        Текст режется по концам строк, а строка длиннее size - по концу
        предложения или пробелу; куски вместе дают исходный текст, пустой
        текст - один пустой кусок

    Аргументы:
        text (str): Текст
        size (int): Наибольшая длина куска в символах

    Вывод:
        Iterator[str]: Куски по порядку

    Пример использования:
        >>> list(text_chunks("Кот спит. Пес лает. Дождь.", size=12))
        ['Кот спит. ', 'Пес лает. ', 'Дождь.']
    """
    parts = []
    for line in text.splitlines(keepends=True):
        while len(line) > size:
            ends = [match.end() for match in SENTENCE_END.finditer(line, 0, size)]
            cut = ends[-1] if ends else line.rfind(" ", 0, size) + 1 or size
            parts.append(line[:cut])
            line = line[cut:]
        parts.append(line)
    chunk = ""
    for part in parts:
        if chunk and len(chunk) + len(part) > size:
            yield chunk
            chunk = ""
        chunk += part
    yield chunk


def parse(nlp: "Language", text: str) -> "Doc":
    """
    Разбор текста моделью spaCy по кускам

    Описание:
        Целиком длинный текст spaCy разбирает с пиком памяти в гигабайты (2,4 ГБ
        на 500 тысяч символов), по кускам text_chunks по одному - в сотни
        мегабайт; разбор меняется только у предложений на стыке кусков

    Аргументы:
        nlp (Language): Модель spaCy
        text (str): Текст

    Вывод:
        Doc: Разобранный текст
    """
    from spacy.tokens import Doc

    return Doc.from_docs(list(nlp.pipe(text_chunks(text), batch_size=1)))


def syntax_group(analysis: Analysis) -> GroupResult:
    """
    Синтаксические статистики текста по дереву зависимостей spaCy

    Описание:
        Статистики SyntaxStats из ruTS по разбору моделью spaCy ru_core_news_sm:
        длины зависимостей, форма дерева, клаузы, сочинительные цепочки, обороты,
        пассив, цепочки родительных падежей, расщепленные сказуемые. Без модели
        группа пуста, а предупреждение говорит, как ее скачать. Статистики,
        не определенные на тексте (средняя длина оборота без оборотов, доля
        пассива без глаголов), отдаются как None с причиной

    Аргументы:
        analysis (Analysis): Текст и настройки

    Вывод:
        tuple[dict[str, Any], list[str]]: Имя статистики ruTS - ее значение и описание;
            предупреждения

    Исключения:
        SourceError: Если в тексте нет слов
    """
    from ruts import SyntaxStats
    from ruts.constants import SYNTAX_STATS_DESC

    nlp = spacy_model()
    if nlp is None:
        return {}, [missing_warning(SPACY_MODEL_TITLE, "группа syntax не посчитана", "не скачана")]
    syntax = SyntaxStats(parse(nlp, analysis.text))
    stats: dict[str, Any] = {}
    for name, value in syntax.get_stats().items():
        description = ": ".join(filter(None, (SYNTAX_STATS_DESC[name], SYNTAX_NOTES.get(name))))
        stats[name] = stat(value, description)
    by_reason: dict[str, dict[str, Any]] = defaultdict(dict)
    for name, item in stats.items():
        by_reason[SYNTAX_REASONS.get(name, OTHER_REASON)][name] = item
    warnings = []
    for reason, items in by_reason.items():
        warnings += undefined_warnings(items, reason)
    return stats, warnings
