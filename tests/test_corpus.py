from typing import get_args

import pytest
from anyts.constants import (
    COLLOCATION_MEASURES as CORE_COLLOCATION_MEASURES,
    DISPERSION_STATS_DESC,
)
from fastmcp.exceptions import ToolError
from ruts.corpus import collocations as ruts_collocations, dispersion as ruts_dispersion

from ruts_mcp.analysis import clean
from ruts_mcp.corpus import (
    COLLOCATION_MEASURES,
    DISPERSION_FIELDS,
    CollocationMeasure,
    collocations,
    dispersion,
    kwic,
    one_word,
    text_words,
)

TEXT = "Кот спит. Коты играют в саду, а кот смотрит на котов. Кошка спит."


def test_kwic():
    result = kwic(TEXT, "кот", window=2)
    assert result == {
        "n_matches": 2,
        "matches": [
            {"left": "", "keyword": "Кот", "right": "спит. Коты"},
            {"left": "саду, а", "keyword": "кот", "right": "смотрит на"},
        ],
        "warnings": [],
    }
    assert kwic(TEXT, "кот", by_lemma=True)["n_matches"] == 4


def test_kwic_limit():
    result = kwic(TEXT, "кот", by_lemma=True, limit=3)
    assert len(result["matches"]) == 3
    assert result["warnings"] == [
        "Вхождений: 4, показаны первые 3; больше строк дает параметр limit"
    ]


def test_kwic_not_found():
    """Без вхождений по словоформе предупреждение подсказывает поиск по лемме"""
    assert kwic(TEXT, "котам")["warnings"] == [
        "Вхождений нет. Поиск шел по словоформе: другие формы слова находит by_lemma"
    ]
    assert kwic(TEXT, "собака", by_lemma=True)["warnings"] == []


def test_kwic_errors():
    with pytest.raises(ToolError):
        kwic(TEXT, "...")


def test_collocations(chekhov):
    result = collocations(chekhov, top_n=5)
    expected = ruts_collocations(text_words(chekhov, lemmatize=True), top_n=5)
    assert result["n_words"] == 241
    assert [
        (pair["left"], pair["right"], pair["freq_pair"], pair["score"])
        for pair in result["collocations"]
    ] == [(pair.left, pair.right, pair.freq_pair, clean(pair.score)) for pair in expected]
    assert result["measure"].startswith("logdice: logDice (Rychlý 2008)")
    assert "всегда стоит рядом, получает 11.7," in result["measure"]
    assert result["warnings"] == []


def test_collocations_node(chekhov):
    """Узел приводится к лемме, как слова текста"""
    result = collocations(chekhov, node="Тонкого", top_n=3)
    assert all("тонкий" in (pair["left"], pair["right"]) for pair in result["collocations"])
    assert collocations(chekhov, node="Тонкий", lemmatize=False)["collocations"]
    with pytest.raises(ToolError, match=r"^Нужно одно слово, получено 'толстый и тонкий'$"):
        collocations(chekhov, node="толстый и тонкий")


def test_collocations_measures():
    assert list(get_args(CollocationMeasure)) == list(COLLOCATION_MEASURES)
    assert set(COLLOCATION_MEASURES) == set(CORE_COLLOCATION_MEASURES)
    result = collocations(TEXT, window=1, measure="mi", min_freq=1)
    assert result["measure"].startswith("mi: взаимная информация MI")


def test_collocations_window_scales():
    """Шкалы Дайс-мер зависят от окна: частота пары в мере делится на window"""
    assert "всегда стоит рядом, получает 0.2," in collocations(TEXT, measure="dice")["measure"]
    assert "получает 1," in collocations(TEXT, window=1, measure="min_sensitivity")["measure"]


def test_collocations_yo():
    """Буква ё сводится к е, как в kwic: «ещё» и «еще» - одно слово"""
    result = collocations("Ещё раз, и еще раз.", window=1, lemmatize=False)
    assert result["collocations"][0]["left"] == "еще"
    assert result["collocations"][0]["freq_pair"] == 2


def test_collocations_absent_node():
    assert collocations(TEXT, node="собака", min_freq=1)["warnings"] == [
        "Слова нет в тексте: собака"
    ]


def test_collocations_not_found():
    result = collocations(TEXT, min_freq=5)
    assert result["collocations"] == []
    assert result["warnings"] == [
        "Пар, которые встречаются вместе от 5 раз на расстоянии до 5 слов, нет: "
        "уменьшите min_freq или увеличьте window"
    ]


def test_dispersion(chekhov):
    result = dispersion(chekhov, words=["Тонкого", "тонкий", "жена", "слон"], parts=5)
    sequence = text_words(chekhov, lemmatize=True)
    assert result["n_words"] == len(sequence)
    assert [item["word"] for item in result["words"]] == ["тонкий", "жена", "слон"]
    expected = ruts_dispersion(sequence, 5, word="тонкий")[0]
    assert result["words"][0] == {"word": "тонкий", "freq": expected.freq} | {
        field: clean(getattr(expected, field)) for field in DISPERSION_FIELDS
    }
    assert result["words"][2]["freq"] == 0
    assert result["words"][2]["dp"] is None
    assert result["warnings"] == [
        "Слов нет в тексте: слон",
        "Частота слов меньше числа частей (5): жена. Такое слово не может попасть во все части, "
        "и меры дисперсии показывают сосредоточенность даже при самом ровном распределении; "
        "для них уменьшите parts",
    ]


def test_dispersion_top(chekhov):
    result = dispersion(chekhov, top_n=3)
    assert [item["word"] for item in result["words"]] == ["и", "он", "ты"]
    assert set(DISPERSION_FIELDS) == set(DISPERSION_STATS_DESC)


def test_dispersion_errors():
    with pytest.raises(ToolError):
        dispersion("Кот спит", parts=5)


def test_one_word():
    assert one_word("Котами", lemmatize=True) == "кот"
    assert one_word("Котами", lemmatize=False) == "котами"
    with pytest.raises(ToolError):
        one_word("...", lemmatize=True)


def test_language_warnings():
    for tool in (kwic, collocations, dispersion):
        arguments = {"keyword": "cat"} if tool is kwic else {}
        result = tool("The cat sleeps and the cat eats and the cat runs", **arguments)
        assert result["warnings"][0].startswith("Букв русского алфавита - только 0%")
