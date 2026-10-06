from typing import Annotated, Any, Literal

from fastmcp.exceptions import ToolError
from pydantic import Field

from .analysis import clean
from .corpus import text_words
from .data import FREQ_DICT_TITLE, freq_dict, missing_warning
from .errors import check_text, ruts_errors
from .language import language_warnings

KeynessMeasure = Literal["log_likelihood", "log_ratio", "chi2", "diff", "bic", "ell", "odds_ratio"]
KEYNESS_MEASURES = {
    "log_likelihood": "логарифм правдоподобия G² (Rayson и Garside 2000): значимость различия, "
    "со знаком минус - слово чаще в эталоне; критические значения: {critical}",
    "log_ratio": "Log Ratio (Hardie 2014): двоичный логарифм отношения частот на миллион слов, "
    "размер эффекта; 1 - слово вдвое чаще в тексте",
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


def keyness(
    text: Annotated[str, Field(description="Текст, ключевые слова которого нужны")],
    reference: Annotated[
        str | None,
        Field(
            description="Текст-эталон; не задано - частотный словарь Ляшевской и Шарова "
            "(современный русский язык, 92 млн словоупотреблений)"
        ),
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

    Используйте, чтобы понять, чем лексика текста отличается от обычного языка (эталон по умолчанию - частотный словарь, его нужно скачать командой ruts-mcp download) или от другого текста (параметр reference). Слова сравниваются в нижнем регистре, ё сводится к е. Со словарем числа и слова с латиницей отбрасываются, а слово вне словаря получает его наименьшую частоту (freq_reference около 37): имена, термины и опечатки попадают в ключевые слова.

    В результате "n_words" - число слов текста, которые сравниваются с эталоном, "reference" - эталон, "measure" - мера сортировки и как ее читать, "keywords" - слова по убыванию меры: частота в тексте "freq_target" и в эталоне "freq_reference", они же на миллион слов "ipm_target" и "ipm_reference", логарифм правдоподобия "g2" (значимость, со знаком минус - слово чаще в эталоне) с p-значением "p_value", Log Ratio "log_ratio" (размер эффекта) и значение меры "score". p_value не поправлено на число проверенных слов: надежнее p < 0,0001 (g2 от 15,13). Ключ "warnings" - предупреждения: текст не на русском языке, ключевых слов нет.
    """
    from anyts.constants import G2_CRITICAL_VALUES
    from ruts.corpus import keyness as ruts_keyness
    from ruts.datasets.freq2011 import CORPUS_SIZE
    from ruts.exceptions import DatasetNotFoundError
    from ruts.lexical_stats import DICTIONARY_WORD

    check_text(text)
    warnings = language_warnings(text)
    if reference is not None:
        check_text(reference)
        warnings += [f"Эталон: {warning}" for warning in language_warnings(reference)]
    with ruts_errors():
        if reference is None:
            target = text_words(text, lemmatize=False)
            try:
                found = ruts_keyness(target, freq_dict(), measure, min_freq, positive, top_n)
            except DatasetNotFoundError:
                raise ToolError(
                    missing_warning(FREQ_DICT_TITLE, "ключевые слова не посчитаны")
                    + "; эталоном может быть и другой текст (reference)"
                ) from None
            target = tuple(word for word in target if DICTIONARY_WORD.fullmatch(word))
            size = CORPUS_SIZE // 1_000_000
            source = f"частотный словарь Ляшевской и Шарова (НКРЯ, {size} млн слов)"
        else:
            target = text_words(text, lemmatize)
            reference_words = text_words(reference, lemmatize)
            found = ruts_keyness(target, reference_words, measure, min_freq, positive, top_n)
            source = f"текст-эталон, {len(reference_words)} слов"
    if not found:
        direction = "чаще" if positive else "реже"
        warnings.append(
            f"Ключевых слов с частотой от {min_freq} нет: уменьшите min_freq"
            if min_freq > 1
            else f"Слов, которые в тексте {direction}, чем в эталоне, нет"
        )
    critical = ", ".join(f"{value} - p < {level}" for level, value in G2_CRITICAL_VALUES.items())
    return {
        "n_words": len(target),
        "reference": source,
        "measure": f"{measure}: {KEYNESS_MEASURES[measure].format(critical=critical)}",
        "keywords": [
            {"word": keyword.word}
            | {field: clean(getattr(keyword, field)) for field in KEYWORD_FIELDS}
            for keyword in found
        ],
        "warnings": warnings,
    }


def compare_texts(
    a: Annotated[list[str], Field(description="Тексты первого корпуса (A)", min_length=1)],
    b: Annotated[list[str], Field(description="Тексты второго корпуса (B)", min_length=1)],
    window: Annotated[
        int | None,
        Field(
            description="Размер окна в словах: тексты режутся на окна равной длины, чтобы "
            "признаки не зависели от длины текста; null - тексты целиком",
            ge=100,
            le=10_000,
        ),
    ] = 1000,
    top_n: Annotated[
        int, Field(description="Число признаков с наибольшим различием", ge=1, le=200)
    ] = 15,
) -> dict[str, Any]:
    """Сравнить два корпуса текстов по признакам стиля и найти, чем они различаются сильнее всего.

    Используйте для атрибуции авторства, сравнения жанров, переводов, текстов человека и модели. Тексты режутся на окна по window слов, у каждого окна считаются около 110 признаков ruTS, и распределения признака в корпусах A и B сравниваются. Окно короче половины window отбрасывается.

    Признаки по префиксам: basic_ - доли длинных, сложных, одно- и многосложных слов, букв, пробелов и знаков, буквы и слоги на слово; readability_ - формулы удобочитаемости; diversity_ - меры лексического разнообразия; morph_ - доли частей речи от слов (morph_pos_NOUN) и значений признаков внутри признака (morph_case_Gen, morph_tense_Past); sents_ - средняя длина предложения в словах, ее стандартное отклонение, коэффициент вариации и автокорреляция соседних длин; punct_ - знаки по типам на 1000 слов и доля буквы ё.

    В результате "n_windows" и "n_texts" - число окон и текстов в A и B, "features" - признаки по убыванию модуля дельты Клиффа: средние по окнам "mean_a" и "mean_b", разность медиан A - B "median_diff" с 95% бутстрэп-интервалом "ci_low" - "ci_high", дельта Клиффа "cliff_delta" (от -1 до 1: доля пар окон, где в A больше, минус доля, где меньше; по модулю от 0,147 - малый, от 0,33 - средний, от 0,474 - большой эффект, Romano и др. 2006) и p-значение U-критерия Манна-Уитни с поправкой Холма на число признаков "p_holm". Окна одного текста не независимы: p_holm считает их независимыми и занижено, если текстов в корпусе мало, а бутстрэп-интервал берет целые тексты и при одном тексте в корпусе не определен. Ключ "warnings" - предупреждения: корпус не на русском языке, в корпусе один текст, ни одно различие не значимо.
    """
    from ruts.corpus import compare_corpora
    from ruts.exceptions import SourceError

    warnings = []
    for label, corpus in (("A", a), ("B", b)):
        joined = "\n\n".join(corpus)
        check_text(joined)
        if not any(text_words(text, lemmatize=False) for text in corpus):
            raise ToolError(f"Корпус {label}: в текстах нет слов")
        warnings += [f"Корпус {label}: {warning}" for warning in language_warnings(joined)]
    with ruts_errors():
        try:
            table = compare_corpora(a, b, window=window, labels=("A", "B"))
        except SourceError as error:
            raise ToolError(
                f"{error}. В инструменте окно короче половины window отбрасывается: "
                "уменьшите window или сравните тексты целиком (window=null)"
            ) from error
    n_windows = {"a": int(table["n_A"].max()), "b": int(table["n_B"].max())}
    n_texts = {"a": int(table["n_texts_A"].max()), "b": int(table["n_texts_B"].max())}
    if min(n_windows.values()) < 2:
        raise ToolError(
            f"Окон в A - {n_windows['a']}, в B - {n_windows['b']}: для сравнения распределений "
            "нужно хотя бы два окна в каждом корпусе; уменьшите window или добавьте текстов"
        )
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
    return {
        "n_windows": n_windows,
        "n_texts": n_texts,
        "features": [
            {"feature": feature}
            | {field: clean(float(row[column])) for field, column in COMPARISON_FIELDS.items()}
            for feature, row in table.head(top_n).iterrows()
        ],
        "warnings": warnings,
    }
