from math import ceil
from typing import Annotated, Any, Literal

from fastmcp.exceptions import ToolError
from pydantic import Field

from .analysis import clean
from .corpus import text_words
from .data import (
    FREQ_DICT_TITLE,
    damaged_warning,
    freq_dict,
    freq_dict_damaged,
    missing_warning,
)
from .errors import ruts_errors
from .inputs import PATH, TEXT, check_length, load_ruts, prepare_text, read_file, read_source
from .language import language_warnings

KeynessMeasure = Literal["log_likelihood", "log_ratio", "chi2", "diff", "bic", "ell", "odds_ratio"]
LOG_RATIO_ZERO = (
    "при нулевой частоте в эталоне она заменяется на 0,5, и log_ratio тогда - оценка, которая "
    "бывает и меньше 0, хотя слово чаще в тексте"
)
KEYNESS_MEASURES = {
    "log_likelihood": "логарифм правдоподобия G² (Rayson и Garside 2000): значимость различия, "
    "со знаком минус - слово чаще в эталоне; критические значения: {critical}",
    "log_ratio": "Log Ratio (Hardie 2014): двоичный логарифм отношения частот на миллион слов, "
    f"размер эффекта; 1 - слово вдвое чаще в тексте; {LOG_RATIO_ZERO}",
    "chi2": "хи-квадрат с поправкой Йейтса: значимость различия",
    "diff": "%DIFF (Gabrielatos и Marchi 2011): разность частот на миллион слов в процентах "
    "от частоты в эталоне",
    "bic": "BIC (Wilson 2013): при том же знаке, что у g2, от 2 - положительное свидетельство "
    "различия, от 6 - сильное, от 10 - очень сильное; знак, обратный g2, - свидетельства нет",
    "ell": "ELL (Johnston, Berry и Mielke 2006): размер эффекта G² со знаком G², обычно от 0 до 1; "
    "null, когда наименьшая ожидаемая частота не больше 1 - со словарем и на коротком тексте "
    "у большинства слов, и тогда наверх выходят частые служебные слова; размер эффекта надежнее "
    "дает log_ratio",
    "odds_ratio": "отношение шансов: 1 - шансы равны",
}
KEYWORD_FIELDS = (
    "freq_target",
    "freq_reference",
    "ipm_target",
    "ipm_reference",
    "g2",
    "p_value",
    "log_ratio",
    "score",
)
COMPARISON_FIELDS = {
    "mean_a": "mean_A",
    "mean_b": "mean_B",
    "median_diff": "median_diff",
    "ci_low": "ci_low",
    "ci_high": "ci_high",
    "cliff_delta": "cliff_delta",
    "p_holm": "p_holm",
}
SIGNIFICANCE = 0.05
MAX_TEXTS = 1000
AUTO_WINDOW = 1000
MIN_WINDOW = 100
# Тексты корпусов, средняя длина которых различается больше, сравниваются нечестно
WINDOW_RATIO = 1.25
LOST_SHARE = 0.1


def keyness(
    text: Annotated[str, Field(description=TEXT)] = "",
    path: Annotated[str | None, Field(description=PATH)] = None,
    reference: Annotated[
        str | None,
        Field(
            description="Текст-эталон; не задано (и не задан reference_path) - частотный "
            "словарь Ляшевской и Шарова (современный русский язык, 92 млн словоупотреблений)"
        ),
    ] = None,
    reference_path: Annotated[
        str | None,
        Field(description="Абсолютный путь к файлу с текстом-эталоном вместо reference"),
    ] = None,
    measure: Annotated[
        KeynessMeasure,
        Field(
            description="Мера для сортировки: log_likelihood - значимость различия, "
            "log_ratio - во сколько раз слово чаще"
        ),
    ] = "log_likelihood",
    positive: Annotated[
        bool,
        Field(description="Слова, которые чаще в тексте; false - которые чаще в эталоне"),
    ] = True,
    min_freq: Annotated[
        int, Field(description="Наименьшая частота слова там, где оно чаще", ge=1)
    ] = 2,
    lemmatize: Annotated[
        bool,
        Field(description="Сравнивать леммы; с частотным словарем леммы сравниваются всегда"),
    ] = True,
    top_n: Annotated[int, Field(description="Число ключевых слов в ответе", ge=1, le=200)] = 20,
) -> dict[str, Any]:
    """Найти ключевые слова текста - слова, которые в нем значимо чаще (или реже), чем в эталоне.

    Используйте, чтобы понять, чем лексика текста отличается от обычного языка (эталон по умолчанию - частотный словарь, его нужно скачать командой ruts-mcp download) или от другого текста (reference или reference_path). Слова сравниваются в нижнем регистре и с е вместо ё. Со словарем числа и слова с латиницей отбрасываются, а слово вне словаря получает его наименьшую частоту (freq_reference около 37): имена, термины и опечатки попадают в ключевые слова. Статьи словаря, которые лемматизатор не дает (его, ее, их, во, со), в слова, которые чаще в эталоне, не попадают: в тексте эти формы относятся к другим леммам (он, она, они, в, с).

    В результате "n_words" - число слов текста, которые сравниваются с эталоном, "reference" - эталон, "measure" - мера сортировки и как ее читать, "keywords" - слова по убыванию меры: частота в тексте "freq_target" и в эталоне "freq_reference", они же на миллион слов "ipm_target" и "ipm_reference", логарифм правдоподобия "g2" (значимость, со знаком минус - слово чаще в эталоне) с p-значением "p_value", Log Ratio "log_ratio" (размер эффекта; при нулевой частоте в эталоне - оценка с поправкой 0,5, бывает меньше 0) и значение меры "score". p_value не поправлено на число проверенных слов: надежнее p < 0,0001 (g2 от 15,13). Ключ "warnings" - предупреждения: текст не на русском языке, ключевых слов нет.
    """
    load_ruts()
    from anyts.constants import G2_CRITICAL_VALUES
    from ruts import WordsExtractor
    from ruts.corpus import keyness as ruts_keyness
    from ruts.datasets.freq2011 import CORPUS_SIZE
    from ruts.exceptions import DatasetNotFoundError
    from ruts.lexical_stats import DICTIONARY_WORD

    text = read_source(text, path)
    warnings = language_warnings(text)
    source: Any
    if reference is None and reference_path is None:
        target: tuple[str, ...] = WordsExtractor(lowercase=True).extract(text)
        n_words = sum(1 for word in target if DICTIONARY_WORD.fullmatch(word))
        if not n_words:
            raise ToolError(
                "Со словарем сравниваются только слова из кириллических букв, а в тексте их "
                "нет: числа и латиница отбрасываются; эталоном может быть другой текст "
                "(reference)"
            )
        source = freq_dict()
        if freq_dict_damaged(source):
            raise ToolError(damaged_warning(FREQ_DICT_TITLE, "ключевые слова не посчитаны"))
        title = f"частотный словарь Ляшевской и Шарова (НКРЯ, {CORPUS_SIZE // 1_000_000} млн слов)"
    else:
        reference = read_source(reference or "", reference_path, "Эталон")
        warnings += [f"Эталон: {warning}" for warning in language_warnings(reference)]
        target = text_words(text, lemmatize)
        source = text_words(reference, lemmatize)
        if not target or not source:
            raise ToolError(f"В {'тексте' if not target else 'эталоне'} нет слов")
        n_words = len(target)
        title = f"текст-эталон, {len(source)} слов"
    with ruts_errors():
        try:
            found = ruts_keyness(target, source, measure, min_freq, positive, top_n)
        except DatasetNotFoundError:
            raise ToolError(
                missing_warning(FREQ_DICT_TITLE, "ключевые слова не посчитаны")
                + "; эталоном может быть и другой текст (reference)"
            ) from None
        rare = not found and min_freq > 1 and ruts_keyness(target, source, measure, 1, positive, 1)
    if rare:
        warnings.append(f"Ключевых слов с частотой от {min_freq} нет: уменьшите min_freq")
    elif not found:
        direction = "чаще" if positive else "реже"
        warnings.append(f"Слов, которые в тексте {direction}, чем в эталоне, нет")
    critical = ", ".join(f"{value} - p < {level}" for level, value in G2_CRITICAL_VALUES.items())
    return {
        "n_words": n_words,
        "reference": title,
        "measure": f"{measure}: {KEYNESS_MEASURES[measure].format(critical=critical)}",
        "keywords": [
            {"word": keyword.word}
            | {field: clean(getattr(keyword, field)) for field in KEYWORD_FIELDS}
            for keyword in found
        ],
        "warnings": warnings,
    }


def auto_window(shortest: int) -> int:
    """
    Размер окна по самому короткому тексту

    Аргументы:
        shortest (int): Число слов в самом коротком тексте со словами

    Вывод:
        int: Не больше 1000 слов и такой, чтобы текст делился хотя бы на два окна,
            но не меньше 100

    Пример использования:
        >>> [auto_window(words) for words in (150, 228, 1500, 2400, 100_000)]
        [100, 114, 750, 800, 1000]
    """
    return max(MIN_WINDOW, shortest // max(2, ceil(shortest / AUTO_WINDOW)))


def coverage_warnings(
    windows: dict[str, list[list[str]]], sizes: dict[str, list[int]], size: int | None
) -> list[str]:
    """
    Предупреждения о том, какая часть корпусов не сравнивается

    Описание:
        Тексты без окон (короче окна или без слов), остатки текстов короче окна,
        если на них теряется больше 10 % слов корпуса, и при сравнении текстов
        целиком - средняя длина текстов корпусов, различающаяся больше чем
        в 1,25 раза

    Аргументы:
        windows (dict[str, list[list[str]]]): Корпус - окна каждого текста
        sizes (dict[str, list[int]]): Корпус - число слов каждого текста
        size (int): Размер окна в словах; None - тексты целиком

    Вывод:
        list[str]: Предупреждения
    """
    warnings = []
    for label, items in windows.items():
        dropped = sum(1 for item in items if not item)
        if dropped:
            reason = "без слов" if size is None else f"короче окна в {size} слов"
            warnings.append(
                f"{dropped} из {len(items)} текстов корпуса {label} {reason} и не вошли "
                "в сравнение"
            )
        if size is not None:
            total = sum(count for count, item in zip(sizes[label], items, strict=True) if item)
            lost = total - sum(map(len, items)) * size
            if lost > LOST_SHARE * total:
                warnings.append(
                    f"Остатки текстов корпуса {label} короче окна в {size} слов не вошли "
                    f"в сравнение: {lost} из {total} слов; окно поменьше теряет меньше текста"
                )
    if size is None:
        means = {
            label: sum(counts) / sum(1 for count in counts if count)
            for label, counts in sizes.items()
        }
        if max(means.values()) > WINDOW_RATIO * min(means.values()):
            warnings.append(
                f"Средняя длина текста в A - {means['A']:.0f} слов, в B - {means['B']:.0f}: "
                "признаки, которые зависят от длины текста (лексическое разнообразие, доли "
                "и частоты слов), различаются и из-за нее; чтобы сравнивать отрывки одной "
                "длины, сравнивайте окнами (whole_texts=false)"
            )
    return warnings


def compare_texts(
    a: Annotated[
        tuple[str, ...],
        Field(description="Тексты первого корпуса (A)", max_length=MAX_TEXTS),
    ] = (),
    b: Annotated[
        tuple[str, ...],
        Field(description="Тексты второго корпуса (B)", max_length=MAX_TEXTS),
    ] = (),
    a_paths: Annotated[
        tuple[str, ...],
        Field(
            description="Абсолютные пути к файлам с текстами корпуса A, вместе с a или вместо",
            max_length=MAX_TEXTS,
        ),
    ] = (),
    b_paths: Annotated[
        tuple[str, ...],
        Field(
            description="Абсолютные пути к файлам с текстами корпуса B, вместе с b или вместо",
            max_length=MAX_TEXTS,
        ),
    ] = (),
    window: Annotated[
        int | None,
        Field(
            description="Размер окна в словах; не задано - не больше 1000 и такой, чтобы "
            "самый короткий текст делился хотя бы на два окна, но не меньше 100",
            ge=MIN_WINDOW,
            le=10_000,
        ),
    ] = None,
    whole_texts: Annotated[
        bool,
        Field(description="Сравнивать тексты целиком, без окон; нужно хотя бы по два текста"),
    ] = False,
    top_n: Annotated[
        int, Field(description="Число признаков с наибольшим различием", ge=1, le=200)
    ] = 15,
) -> dict[str, Any]:
    """Сравнить два корпуса текстов по признакам стиля и найти, чем они различаются сильнее всего.

    Используйте для атрибуции авторства, сравнения жанров, переводов, текстов человека и модели. Тексты режутся подряд на окна ровно по window слов (whole_texts - тексты целиком), у каждого окна считаются около 110 признаков ruTS, и распределения признака в корпусах A и B сравниваются. Остаток текста короче окна и текст короче окна отбрасываются: ответ предупреждает о таких текстах и о потере больше 10 % слов корпуса на остатках. Для сравнения нужно хотя бы по два окна в каждом корпусе. Тексты из файлов передавайте через a_paths и b_paths.

    Признаки по префиксам: basic_ - доли длинных, сложных, одно- и многосложных слов, букв, пробелов и знаков, буквы и слоги на слово; readability_ - формулы удобочитаемости; diversity_ - меры лексического разнообразия; morph_ - доли частей речи от слов (morph_pos_NOUN) и значений признаков внутри признака (morph_case_Gen, morph_tense_Past); sents_ - средняя длина предложения в словах, ее стандартное отклонение, коэффициент вариации и автокорреляция соседних длин; punct_ - знаки по типам на 1000 слов и доля буквы ё.

    В результате "window" - размер окна (null - тексты целиком), "n_windows" и "n_texts" - число окон и текстов в A и B, "features" - признаки по убыванию модуля дельты Клиффа, при равной дельте - по относительной разности медиан: средние по окнам "mean_a" и "mean_b", разность медиан A - B "median_diff" с 95% бутстрэп-интервалом "ci_low" - "ci_high", дельта Клиффа "cliff_delta" (от -1 до 1: доля пар окон, где в A больше, минус доля, где меньше; по модулю от 0,147 - малый, от 0,33 - средний, от 0,474 - большой эффект, Romano и др. 2006) и p-значение U-критерия Манна-Уитни с поправкой Холма на число признаков "p_holm". Окна одного текста не независимы: p_holm считает их независимыми и занижено, если текстов в корпусе мало, а бутстрэп-интервал берет целые тексты и при одном тексте в корпусе не определен. Ключ "warnings" - предупреждения: корпус не на русском языке, тексты корпусов разной длины при whole_texts, тексты или их остатки не вошли в сравнение, в корпусе один текст, ни одно различие не значимо.
    """
    load_ruts()
    from ruts.corpus import compare_corpora, split_windows
    from ruts.utils import iter_text_words

    warnings = []
    corpora = {}
    for label, texts, paths in (("A", a, a_paths), ("B", b, b_paths)):
        name = f"Корпус {label}"
        corpus = [prepare_text(text, name, check=False) for text in texts]
        corpus += [prepare_text(read_file(path, name), name, check=False) for path in paths]
        if not corpus:
            raise ToolError(
                f"{name} пуст: передайте тексты в {label.lower()} или пути к файлам "
                f"в {label.lower()}_paths"
            )
        check_length(sum(map(len, corpus)), name)
        warnings += [f"{name}: {warning}" for warning in language_warnings("\n\n".join(corpus))]
        corpora[label] = corpus
    sizes = {
        label: [sum(1 for _ in iter_text_words(text)) for text in corpus]
        for label, corpus in corpora.items()
    }
    for label, counts in sizes.items():
        if not sum(counts):
            raise ToolError(f"Корпус {label}: в текстах нет слов")
    if whole_texts:
        size = None
    elif window is not None:
        size = window
    else:
        size = auto_window(min(count for counts in sizes.values() for count in counts if count))
    with ruts_errors():
        windows = {
            label: [split_windows(text, size) for text in corpus]
            for label, corpus in corpora.items()
        }
    n_windows = {label.lower(): sum(map(len, items)) for label, items in windows.items()}
    if min(n_windows.values()) < 2:
        if size is None:
            advice = (
                "передайте хотя бы по два текста со словами в каждый корпус или сравнивайте "
                "окнами (whole_texts=false)"
            )
        elif size > MIN_WINDOW:
            advice = (
                f"тексты коротки для окна в {size} слов: задайте window поменьше (не меньше "
                f"{MIN_WINDOW}), добавьте текстов или сравните тексты целиком (whole_texts=true)"
            )
        else:
            advice = (
                f"тексты коротки даже для наименьшего окна в {MIN_WINDOW} слов: сравните тексты "
                "целиком (whole_texts=true, нужно хотя бы по два текста в корпусе) или, если "
                "текстов меньше, сравните результаты analyze_text"
            )
        raise ToolError(
            f"Окон в A - {n_windows['a']}, в B - {n_windows['b']}: для сравнения распределений "
            f"нужно хотя бы два окна в каждом корпусе; {advice}"
        )
    warnings += coverage_warnings(windows, sizes, size)
    with ruts_errors():
        table = compare_corpora(corpora["A"], corpora["B"], window=size, labels=("A", "B"))
    n_texts = {"a": int(table["n_texts_A"].max()), "b": int(table["n_texts_B"].max())}
    for label, count in n_texts.items():
        if count < 2:
            warnings.append(
                f"В корпусе {label.upper()} один текст: интервал разности медиан не определен, "
                "а p_holm считает окна одного текста независимыми и занижено; различия могут "
                "быть особенностями текста, а не корпуса"
            )
    if not (table["p_holm"] < SIGNIFICANCE).any():
        warnings.append(
            f"Ни одно различие не значимо после поправки Холма (p_holm < {SIGNIFICANCE}): окон "
            f"в A - {n_windows['a']}, в B - {n_windows['b']}. Нужно больше текста или окно "
            "поменьше; дельта Клиффа на таком числе окон - грубая оценка"
        )
    scale = table[["mean_A", "mean_B"]].abs().max(axis=1)
    ordered = table.assign(
        delta=table["cliff_delta"].abs(), relative=(table["median_diff"].abs() / scale).fillna(0)
    ).sort_values(["delta", "relative"], ascending=False, na_position="last", kind="stable")
    shown = ordered.head(top_n)
    last = shown["delta"].iloc[-1]
    hidden = int((ordered["delta"].iloc[top_n:] == last).sum())
    if hidden:
        warnings.append(
            f"Еще {hidden} признаков с тем же модулем дельты Клиффа {clean(float(last))} "
            "не показаны: "
            "при равной дельте признаки упорядочены по относительной разности медиан; больше "
            "признаков дает top_n"
        )
    return {
        "window": size,
        "n_windows": n_windows,
        "n_texts": n_texts,
        "features": [
            {"feature": feature}
            | {field: clean(float(row[column])) for field, column in COMPARISON_FIELDS.items()}
            for feature, row in shown.iterrows()
        ],
        "warnings": warnings,
    }
