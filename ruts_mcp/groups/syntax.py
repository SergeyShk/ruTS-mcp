import re
from collections import defaultdict
from collections.abc import Iterator
from itertools import pairwise
from typing import TYPE_CHECKING, Any

from ..analysis import Analysis, GroupResult, stat, undefined_warnings
from ..data import SPACY_MODEL_TITLE, missing_warning, spacy_model

if TYPE_CHECKING:
    from spacy.language import Language
    from spacy.tokens import Doc

CHUNK_SIZE = 20_000
WORD_CHAR = re.compile(r"\w")

L2SCA_CLAUSES = "клаузы - без однородных сказуемых с общим подлежащим и инфинитивных клауз"
# Пояснения к описаниям ruTS там, где по названию статистику не прочитать
SYNTAX_NOTES = {
    "mean_dependency_distance": "расстояние в словах между словом и его вершиной; чем больше, "
    "тем больше нагрузка на память при чтении",
    "max_dependency_distance": "наибольшая длина зависимости в предложении, средняя "
    "по предложениям",
    "p_adjacent_dependencies": "доля зависимостей между соседними словами, от 0 до 1",
    "tree_depth": "наибольшее число связей от вершины предложения до слова",
    "leaves_per_sent": "листья - слова без зависимых",
    "nodes_per_leaf": "слов на лист; чем больше, тем длиннее ветви дерева, чем меньше - "
    "тем оно ветвистее",
    "words_before_root": "вершина - главное сказуемое, у предложения со связкой - именная часть "
    "(«была врачом»); говорит о порядке слов не меньше, чем о сложности",
    "verb_valency": "среднее число зависимых у финитного глагола",
    "mean_clause_len": "клауза - часть предложения со своим сказуемым: главная, придаточная, "
    "сочиненная, однородное сказуемое, инфинитивная клауза («хочу спать», «пришел, чтобы "
    "помочь»); модальное или фазовое сочетание («может уйти», «нужно уйти», «начал читать») - "
    "одна клауза; причастные и деепричастные обороты считаются отдельно",
    "p_complex_sents": "от 0 до 1",
    "infinitive_clauses_per_sent": "инфинитив со своей клаузой - при глаголе («хочу спать», "
    "«попросил его уйти»), с союзом «чтобы» («пришел, чтобы помочь»), при оценочном слове "
    "(«трудно сказать»); входит в клаузы, но не в придаточные",
    "t_units_per_sent": "T/S по L2SCA; T-единица - главная клауза с зависящими от нее "
    "клаузами, в «я пришел, а он ушел» их две, в «я пришел и ушел» - одна",
    "mean_t_unit_len": "MLT по L2SCA",
    "clauses_per_t_unit": f"C/T по L2SCA; {L2SCA_CLAUSES} («пришел и ушел» - одна клауза)",
    "p_complex_t_units": "CT/T по L2SCA, от 0 до 1",
    "verb_phrases_per_t_unit": "VP/T по L2SCA; глагольная группа - сказуемое, а причастие-"
    "определение («дом, построенный рабочими») ею не считается",
    "coordinate_phrases_per_clause": "CP/C по L2SCA; сочиненная группа - однородные члены "
    f"(«мужчина и женщина») или сказуемые с общим подлежащим («пришел и ушел»); {L2SCA_CLAUSES}",
    "complex_nominals_per_clause": "CN/C по L2SCA; сложная именная группа - существительное "
    "с определением, дополнением, приложением, придаточной или причастным оборотом или "
    f"именная клауза; {L2SCA_CLAUSES}",
    "modifiers_per_noun": "определения, числительные, местоимения, зависимые существительные "
    "и обороты при существительном",
    "prep_chains_per_sent": "цепочка - два и более вложенных дополнения с предлогом, каждое "
    "при предыдущем",
    "max_prep_chain_len": "в дополнениях: «на коврике в доме у мэра» - 3",
    "genitive_chains_per_sent": "цепочка - два и более вложенных беспредложных определения "
    "в родительном падеже",
    "max_genitive_chain_len": "в словах: «повышение эффективности использования ресурсов» - 3",
    "p_passive": "среди глагольных форм, от 0 до 1",
    "p_agentless_passive": "среди пассивных форм, без указания на действующее лицо, от 0 до 1",
    "split_predicates_per_sent": "легкий глагол с именной частью вместо простого глагола: "
    "«осуществлять проверку», «оказать помощь», «принять участие»",
    "p_preverbal_subjects": "вершина - сказуемое, подлежащее - существительное, а не "
    "местоимение; от 0 до 1",
    "p_preverbal_objects": "вершина - сказуемое, прямое дополнение - существительное, а не "
    "местоимение; от 0 до 1",
    "pos_edit_distance": "наименьшее число вставок, удалений и замен, которое превращает части "
    "речи одного предложения в части речи следующего, деленное на длину более длинного, "
    "от 0 до 1; чем меньше, тем больше схожи предложения",
    "syntax_similarity": "доля общих троек зависимостей (части речи слова и его вершины "
    "и связь) у соседних предложений, от 0 до 1; растет с длиной предложений",
    "noun_verb_ratio": "чем больше, тем номинативнее стиль",
}
NO_LINKS_REASON = "в предложениях текста нет связей между словами"
NO_VERBS_REASON = "в тексте нет глагольных форм"
NO_CLAUSES_REASON = "в тексте нет клауз"
NO_T_UNITS_REASON = "в тексте нет T-единиц"
ONE_SENT_REASON = "схожесть считается по парам соседних предложений, а в тексте одно предложение"
SYNTAX_REASONS = {
    "mean_dependency_distance": NO_LINKS_REASON,
    "std_dependency_distance": NO_LINKS_REASON,
    "max_dependency_distance": NO_LINKS_REASON,
    "p_adjacent_dependencies": NO_LINKS_REASON,
    "words_before_root": "вершины предложений текста - не слова",
    "verb_valency": "в тексте нет финитных глаголов",
    "mean_coordination_chain_len": "в тексте нет сочинительных цепочек",
    "mean_clause_len": NO_CLAUSES_REASON,
    "mean_t_unit_len": NO_T_UNITS_REASON,
    "clauses_per_t_unit": NO_T_UNITS_REASON,
    "p_complex_t_units": NO_T_UNITS_REASON,
    "verb_phrases_per_t_unit": NO_T_UNITS_REASON,
    "coordinate_phrases_per_clause": NO_CLAUSES_REASON,
    "complex_nominals_per_clause": NO_CLAUSES_REASON,
    "modifiers_per_noun": "в тексте нет существительных",
    "mean_participle_clause_len": "в тексте нет причастных оборотов",
    "mean_converb_clause_len": "в тексте нет деепричастных оборотов",
    "p_passive": NO_VERBS_REASON,
    "p_agentless_passive": "в тексте нет пассивных форм",
    "p_preverbal_subjects": "в тексте нет подлежащих-существительных",
    "p_preverbal_objects": "в тексте нет прямых дополнений-существительных",
    "pos_edit_distance": ONE_SENT_REASON,
    "syntax_similarity": ONE_SENT_REASON,
    "noun_verb_ratio": NO_VERBS_REASON,
}
OTHER_REASON = "значение не определено на таком тексте"


def text_chunks(text: str, size: int = CHUNK_SIZE) -> Iterator[tuple[str, list[int]]]:
    """
    Куски текста не длиннее size символов с началами их предложений для разбора spaCy

    Описание:
        Кусок собирается из целых предложений razdel (iter_text_sents) с пробелами
        после них - тех же предложений, что у групп ruTS по строке; предложение
        длиннее size режется по концу строки, пробелу или длине, и его продолжение
        начинает кусок без начала предложения. Куски вместе дают исходный текст,
        пустой текст - один пустой кусок

    Аргументы:
        text (str): Текст
        size (int): Наибольшая длина куска в символах

    Вывод:
        Iterator[tuple[str, list[int]]]: Куски по порядку и позиции начал предложений в них

    Пример использования:
        >>> list(text_chunks("Кот спит. Пес лает. Дождь.", size=12))
        [('Кот спит. ', [0]), ('Пес лает. ', [0]), ('Дождь.', [0])]
        >>> list(text_chunks("Кот спит. Пес лает.", size=100))
        [('Кот спит. Пес лает.', [0, 10])]
    """
    from ruts.utils import iter_text_sents

    starts = [start for start, _, sent in iter_text_sents(text) if sent.strip()]
    bounds = [0, *starts[1:], len(text)]
    firsts: list[int | None] = [*starts] or [None]
    pieces: list[tuple[int, int, int | None]] = []
    for (begin, end), start in zip(pairwise(bounds), firsts, strict=True):
        while end - begin > size:
            window = text[begin : begin + size]
            cut = window.rfind("\n") + 1 or window.rfind(" ") + 1 or size
            pieces.append((begin, begin + cut, start))
            begin += cut
            start = None
        pieces.append((begin, end, start))
    chunk_begin, chunk_end = 0, 0
    offsets: list[int] = []
    for begin, end, start in pieces:
        if chunk_end > chunk_begin and end - chunk_begin > size:
            yield text[chunk_begin:chunk_end], offsets
            chunk_begin, offsets = begin, []
        chunk_end = end
        if start is not None:
            offsets.append(start - chunk_begin)
    yield text[chunk_begin:chunk_end], offsets


def parse(nlp: "Language", text: str) -> "Doc":
    """
    Разбор текста моделью spaCy по кускам

    Описание:
        Куски text_chunks разбираются по одному, чтобы память не росла с длиной
        текста. Предложения разбора - предложения razdel (set_sent_starts), как
        у групп ruTS по строке; пустая строка завершает предложение. Пробелы
        и переводы строк по краям куска отбрасываются: за ними spaCy иначе
        разбирает последнее предложение. Тензоры кусков статистикам не нужны
        и тоже отбрасываются

    Аргументы:
        nlp (Language): Модель spaCy
        text (str): Текст

    Вывод:
        Doc: Разобранный текст
    """
    import numpy
    from ruts.utils import set_sent_starts
    from spacy.tokens import Doc

    def unparsed() -> Iterator["Doc"]:
        for chunk, starts in text_chunks(text):
            shift = len(chunk) - len(chunk.lstrip())
            doc = nlp.make_doc(chunk.strip())
            yield set_sent_starts(doc, [start - shift for start in starts])

    docs = []
    for doc in nlp.pipe(unparsed(), batch_size=1):
        doc.tensor = numpy.zeros((0,), dtype="float32")
        docs.append(doc)
    return Doc.from_docs(docs)


def syntax_group(analysis: Analysis) -> GroupResult:
    """
    Синтаксические статистики текста по дереву зависимостей spaCy

    Описание:
        Статистики SyntaxStats из ruTS по разбору моделью spaCy ru_core_news_sm:
        длины зависимостей, форма дерева, клаузы и единицы L2SCA, сочинительные
        и предложные цепочки, обороты, пассив, цепочки родительных падежей,
        расщепленные сказуемые, порядок слов, схожесть соседних предложений.
        Модель разбирает текст без знаков ударения и мягких переносов
        (strip_marks): слова со знаками она размечает неверно; предложения
        разбора - предложения razdel, как в группах ruTS по строке. Без модели
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
    from ruts.exceptions import SourceError
    from ruts.utils import strip_marks

    # Разбор длинного текста занимает секунды, а без букв и цифр слов в нем нет
    if not WORD_CHAR.search(analysis.text):
        raise SourceError("В источнике данных отсутствуют слова")
    nlp = spacy_model()
    if nlp is None:
        return {}, [missing_warning(SPACY_MODEL_TITLE, "группа syntax не посчитана", "не скачана")]
    syntax = SyntaxStats(parse(nlp, strip_marks(analysis.text)))
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
