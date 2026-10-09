from math import log2
from typing import Annotated, Any, Literal

from fastmcp.exceptions import ToolError
from pydantic import Field

from .analysis import clean
from .errors import ruts_errors
from .inputs import PATH, TEXT, load_ruts, read_source
from .language import language_warnings

CollocationMeasure = Literal[
    "logdice", "mi", "mi3", "t_score", "dice", "log_likelihood", "npmi", "min_sensitivity"
]
COLLOCATION_MEASURES = {
    "logdice": "logDice (Rychlý 2008): чем выше, тем устойчивее пара, не зависит от размера "
    "текста; пара, которая всегда стоит рядом, получает {logdice_max}, наибольшее значение 14 - "
    "у пары, которая встречается на каждом расстоянии в окне, ниже нуля - слабая связь",
    "mi": "взаимная информация MI (Church и Hanks 1990): завышает редкие пары",
    "mi3": "MI³ (Oakes 1998): отдает предпочтение частым парам",
    "t_score": "t-критерий (Church и др. 1991): отдает предпочтение частым парам",
    "dice": "коэффициент Дайса: от 0 до 1, не зависит от размера текста; пара, которая всегда "
    "стоит рядом, получает {adjacent}, 1 - пара, которая встречается на каждом расстоянии в окне",
    "log_likelihood": "логарифм правдоподобия G² (Dunning 1993)",
    "npmi": "нормированная взаимная информация NPMI (Bouma 2009): от -1 до 1; 1 - слова "
    "встречаются только вместе и на каждом расстоянии в окне, при window больше 1 пара, "
    "которая всегда стоит рядом, получает меньше 1",
    "min_sensitivity": "минимальная чувствительность (Pedersen 1998): от 0 до 1; пара, которая "
    "всегда стоит рядом, получает {adjacent}, 1 - пара, которая встречается на каждом "
    "расстоянии в окне",
}
KWIC_LIMIT = 500
KWIC_BUDGET = 40_000
DISPERSION_FIELDS = (
    "dp",
    "dp_norm",
    "juilland_d",
    "carroll_d2",
    "rosengren_s",
    "kl_divergence",
)


def text_words(text: str, lemmatize: bool) -> tuple[str, ...]:
    """
    Слова текста в нижнем регистре, без знаков препинания и с е вместо ё

    Аргументы:
        text (str): Текст
        lemmatize (bool): Заменить слова леммами pymorphy3

    Вывод:
        tuple[str]: Слова по порядку

    Пример использования:
        >>> text_words("Коты ещё спят на окне", lemmatize=True)
        ('кот', 'еще', 'спать', 'на', 'окно')
    """
    from ruts import WordsExtractor
    from ruts.utils import normalize_yo

    words = WordsExtractor(use_lexemes=lemmatize, lowercase=True).extract(text)
    return tuple(normalize_yo(word) for word in words)


def one_word(word: str, lemmatize: bool) -> str:
    """
    Слово запроса в том виде, в каком сравниваются слова текста (text_words)

    Аргументы:
        word (str): Слово, переданное инструменту
        lemmatize (bool): Заменить слово леммой pymorphy3

    Вывод:
        str: Слово в нижнем регистре или его лемма

    Исключения:
        ToolError: Если в строке не одно слово
    """
    words = text_words(word, lemmatize)
    if len(words) != 1:
        raise ToolError(f"Нужно одно слово, получено {word!r}")
    return words[0]


def kwic(
    keyword: Annotated[str, Field(description="Слово или словосочетание", min_length=1)],
    text: Annotated[str, Field(description=TEXT)] = "",
    path: Annotated[str | None, Field(description=PATH)] = None,
    window: Annotated[
        int, Field(description="Число слов контекста слева и справа", ge=0, le=50)
    ] = 5,
    by_lemma: Annotated[
        bool, Field(description="Искать все формы слова по лемме: «кот» находит «кота», «коты»")
    ] = False,
    limit: Annotated[
        int, Field(description="Наибольшее число строк ответа", ge=1, le=KWIC_LIMIT)
    ] = 50,
) -> dict[str, Any]:
    """Найти все вхождения слова или словосочетания в тексте с контекстом (конкорданс KWIC).

    Используйте, чтобы увидеть, как слово употребляется в тексте, и цитировать точно. Слова сравниваются без учета регистра и буквы ё, с by_lemma - по леммам pymorphy3; словосочетание не переходит через конец предложения.

    В результате "n_matches" - число вхождений, "matches" - строки по порядку в тексте: контекст слева "left", вхождение "keyword", как оно записано в тексте, и контекст справа "right". Строки ограничены параметром limit и общим объемом ответа около 40 тысяч символов. Ключ "warnings" - предупреждения: текст не на русском языке, показаны не все вхождения.
    """
    load_ruts()
    from ruts.corpus import kwic as ruts_kwic

    text = read_source(text, path)
    warnings = language_warnings(text)
    with ruts_errors():
        lines = ruts_kwic(text, keyword, window, by_lemma)
    matches: list[dict[str, str]] = []
    size = 0
    for line in lines[:limit]:
        size += len(line.left) + len(line.keyword) + len(line.right)
        if matches and size > KWIC_BUDGET:
            break
        matches.append({"left": line.left, "keyword": line.keyword, "right": line.right})
    if len(matches) < min(limit, len(lines)):
        warnings.append(
            f"Вхождений: {len(lines)}, показаны первые {len(matches)}: ответ ограничен "
            f"{KWIC_BUDGET} символами контекста; уменьшите window, чтобы увидеть больше строк"
        )
    elif len(lines) > limit:
        more = (
            "больше строк дает параметр limit"
            if limit < KWIC_LIMIT
            else f"больше {KWIC_LIMIT} строк за вызов не показывается"
        )
        warnings.append(f"Вхождений: {len(lines)}, показаны первые {limit}; {more}")
    if not lines and not by_lemma:
        warnings.append(
            "Вхождений нет. Поиск шел по словоформе: другие формы слова находит by_lemma"
        )
    return {"n_matches": len(lines), "matches": matches, "warnings": warnings}


def collocations(
    text: Annotated[str, Field(description=TEXT)] = "",
    path: Annotated[str | None, Field(description=PATH)] = None,
    window: Annotated[
        int,
        Field(description="Наибольшее расстояние между словами пары; 1 - биграммы", ge=1, le=10),
    ] = 5,
    measure: Annotated[
        CollocationMeasure,
        Field(
            description="Мера ассоциации: logdice - устойчивость пары, не зависит от размера "
            "текста; mi завышает редкие пары; mi3 и t_score отдают предпочтение частым"
        ),
    ] = "logdice",
    min_freq: Annotated[
        int, Field(description="Наименьшее значение freq_pair - числа пар позиций в окне", ge=1)
    ] = 2,
    node: Annotated[
        str | None,
        Field(description="Слово, сочетаемость которого нужна; не задано - все пары"),
    ] = None,
    lemmatize: Annotated[
        bool,
        Field(description="Сравнивать леммы: «точка зрения» и «точки зрения» - одна пара"),
    ] = True,
    top_n: Annotated[int, Field(description="Число коллокаций в ответе", ge=1, le=200)] = 20,
) -> dict[str, Any]:
    """Найти коллокации текста - пары слов, которые встречаются вместе чаще, чем случайно.

    Используйте для устойчивых сочетаний, терминологии и сочетаемости слова (параметр node). Пара упорядочена: правое слово стоит не дальше window слов после левого. Леммы pymorphy3 берутся без снятия омонимии.

    В результате "n_words" - число слов текста, "measure" - мера и как ее читать, "collocations" - пары по убыванию меры: левое слово "left", правое "right", их частоты "freq_left" и "freq_right", частота пары "freq_pair" и значение меры "score". freq_pair - число пар позиций, где правое слово стоит в окне после левого: слово, повторенное в окне, дает несколько пар, поэтому freq_pair бывает больше частоты слова, и такая пара - повтор, а не устойчивое сочетание. Ключ "warnings" - предупреждения: текст не на русском языке, слова node нет в тексте, пар с такой частотой нет.
    """
    load_ruts()
    from ruts.corpus import collocations as ruts_collocations

    text = read_source(text, path)
    warnings = language_warnings(text)
    with ruts_errors():
        words = text_words(text, lemmatize)
        node_word = None if node is None else one_word(node, lemmatize)
        found = ruts_collocations(words, window, measure, min_freq, node_word, top_n)
    if node is not None and node_word not in words:
        shown = node_word if node_word == node.strip().lower() else f"{node} ({node_word})"
        warnings.append(f"Слова нет в тексте: {shown}")
    elif not found:
        warnings.append(
            f"Пар, которые встречаются вместе от {min_freq} раз на расстоянии до {window} слов, "
            "нет: уменьшите min_freq или увеличьте window"
        )
    description = COLLOCATION_MEASURES[measure].format(
        logdice_max=f"{14 - log2(window):.1f}", adjacent=f"{1 / window:.2g}"
    )
    return {
        "n_words": len(words),
        "measure": f"{measure}: {description}",
        "collocations": [
            {
                "left": pair.left,
                "right": pair.right,
                "freq_left": pair.freq_left,
                "freq_right": pair.freq_right,
                "freq_pair": pair.freq_pair,
                "score": clean(pair.score),
            }
            for pair in found
        ],
        "warnings": warnings,
    }


def dispersion(
    text: Annotated[str, Field(description=TEXT)] = "",
    path: Annotated[str | None, Field(description=PATH)] = None,
    words: Annotated[
        list[str] | None,
        Field(
            description="Слова, дисперсия которых нужна; не задано - самые частые слова",
            max_length=200,
        ),
    ] = None,
    parts: Annotated[
        int, Field(description="Число частей текста примерно равного размера", ge=2, le=100)
    ] = 10,
    lemmatize: Annotated[
        bool, Field(description="Сравнивать леммы: формы слова считаются одним словом")
    ] = True,
    top_n: Annotated[
        int, Field(description="Число самых частых слов, если words не задано", ge=1, le=200)
    ] = 20,
) -> dict[str, Any]:
    """Измерить, насколько равномерно слова распределены по тексту (дисперсия Гриса).

    Используйте, чтобы отличить слово, которое проходит через весь текст, от слова, сосредоточенного в одном месте: частота их не различает. Текст делится на parts частей примерно равного размера.

    В результате "n_words" - число слов текста, "words" - слова в порядке запроса или по убыванию частоты, с частотой "freq" и мерами дисперсии:
    - dp: отклонение пропорций DP Гриса, основная мера; 0 - слово распределено пропорционально размерам частей, наибольшее значение около 1 - 1/parts - все вхождения в одной части.
    - dp_norm: DP, деленное на наибольшее возможное значение; 1 - все вхождения в самой малой части.
    - juilland_d: D Жюйана; 1 - равномерно, 0 - в одной части.
    - carroll_d2: D2 Кэрролла по энтропии распределения; 1 - равномерно, 0 - в одной части.
    - rosengren_s: S Розенгрена; 1 - пропорционально, около 1/parts - в одной части.
    - kl_divergence: дивергенция Кульбака-Лейблера в битах; 0 - пропорционально, растет при сосредоточении.
    У слова, которого нет в тексте, частота 0 и меры null. Слово с частотой меньше parts не может попасть во все части, и его меры показывают сосредоточенность даже при самом ровном распределении. Ключ "warnings" - предупреждения: текст не на русском языке, слов нет в тексте, частота слов меньше числа частей.
    """
    load_ruts()
    from ruts.corpus import dispersion as ruts_dispersion

    text = read_source(text, path)
    warnings = language_warnings(text)
    with ruts_errors():
        sequence = text_words(text, lemmatize)
        table = ruts_dispersion(sequence, parts)
        if words:
            by_word = {item.word: item for item in table}
            targets = dict.fromkeys(one_word(word, lemmatize) for word in words)
            found = [
                by_word.get(target) or ruts_dispersion(sequence, parts, word=target)[0]
                for target in targets
            ]
        else:
            found = table[:top_n]
    absent = [item.word for item in found if not item.freq]
    if absent:
        warnings.append(f"Слов нет в тексте: {', '.join(absent)}")
    rare = [item.word for item in found if 0 < item.freq < parts]
    if rare:
        warnings.append(
            f"Частота слов меньше числа частей ({parts}): {', '.join(rare)}. Такое слово не может "
            "попасть во все части, и меры дисперсии показывают сосредоточенность даже при самом "
            "ровном распределении; для них уменьшите parts"
        )
    return {
        "n_words": len(sequence),
        "words": [
            {"word": item.word, "freq": item.freq}
            | {field: clean(getattr(item, field)) for field in DISPERSION_FIELDS}
            for item in found
        ],
        "warnings": warnings,
    }
