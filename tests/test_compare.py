from typing import get_args

import pytest
from anyts.constants import G2_CRITICAL_VALUES, KEYNESS_MEASURES as CORE_KEYNESS_MEASURES
from fastmcp.exceptions import ToolError
from ruts.corpus import compare_corpora, keyness as ruts_keyness
from ruts.datasets import FreqDict

from ruts_mcp.analysis import clean
from ruts_mcp.compare import (
    COMPARISON_FIELDS,
    KEYNESS_MEASURES,
    KEYWORD_FIELDS,
    KeynessMeasure,
    compare_texts,
    keyness,
)
from ruts_mcp.corpus import text_words
from tests.conftest import CAT, PUSHKIN

REFERENCE = "Кот спал. Собака лаяла на кота, а кот спал на окне. Собака ушла."


def rows(keywords):
    return [
        {"word": item.word} | {f: clean(getattr(item, f)) for f in KEYWORD_FIELDS}
        for item in keywords
    ]


def test_keyness_dictionary(dicts):
    """Эталон по умолчанию - частотный словарь: словоформы приводятся к его леммам"""
    result = keyness(CAT, min_freq=1)
    expected = ruts_keyness(text_words(CAT, lemmatize=False), FreqDict(dicts), top_n=20)
    assert result["n_words"] == 8
    assert result["reference"] == "частотный словарь Ляшевской и Шарова (НКРЯ, 92 млн слов)"
    assert result["keywords"] == rows(expected)
    assert result["keywords"][0]["word"] == "кот"
    assert result["warnings"] == []


def test_keyness_without_dictionary(data_dir):
    with pytest.raises(ToolError) as info:
        keyness(CAT)
    message = str(info.value)
    assert message.startswith("Частотный словарь Ляшевской и Шарова не скачан: ключевые слова")
    assert "ruts-mcp download" in message
    assert message.endswith("эталоном может быть и другой текст (reference)")


def test_keyness_reference():
    result = keyness(REFERENCE, reference=CAT, min_freq=1)
    expected = ruts_keyness(
        text_words(REFERENCE, lemmatize=True), text_words(CAT, lemmatize=True), top_n=20
    )
    assert result["reference"] == "текст-эталон, 8 слов"
    assert result["keywords"] == rows(expected)
    assert result["keywords"][0]["word"] == "собака"
    negative = keyness(REFERENCE, reference=CAT, positive=False, min_freq=1)
    assert all(item["g2"] < 0 for item in negative["keywords"])


def test_keyness_measures():
    assert list(get_args(KeynessMeasure)) == list(KEYNESS_MEASURES)
    assert set(KEYNESS_MEASURES) == set(CORE_KEYNESS_MEASURES)
    measure = keyness(REFERENCE, reference=CAT)["measure"]
    for level, value in G2_CRITICAL_VALUES.items():
        assert f"{value} - p < {level}" in measure
    result = keyness(REFERENCE, reference=CAT, measure="log_ratio", min_freq=1)
    assert result["measure"].startswith("log_ratio: Log Ratio (Hardie 2014)")
    assert [item["score"] for item in result["keywords"]] == [
        item["log_ratio"] for item in result["keywords"]
    ]


def test_keyness_warnings():
    result = keyness(REFERENCE, reference="The cat sleeps", min_freq=10)
    assert result["warnings"] == [
        "Эталон: Букв русского алфавита - только 0%: ruTS считает статистики по правилам "
        "русского языка, для текста на другом языке значения не имеют смысла",
        "Ключевых слов с частотой от 10 нет: уменьшите min_freq",
    ]


def test_compare_texts(chekhov):
    a, b = [chekhov] * 5, [PUSHKIN * 12] * 5
    result = compare_texts(a, b, window=100, top_n=5)
    table = compare_corpora(a, b, window=100, labels=("A", "B")).head(5)
    assert result["n_windows"] == {"a": 10, "b": 10}
    assert result["n_texts"] == {"a": 5, "b": 5}
    assert result["features"] == [
        {"feature": feature}
        | {field: clean(float(row[column])) for field, column in COMPARISON_FIELDS.items()}
        for feature, row in table.iterrows()
    ]
    assert result["features"][0]["p_holm"] < 0.05
    assert result["warnings"] == []


def test_compare_texts_not_significant(chekhov):
    """На двух текстах целиком статистики нет, предупреждение называет число окон"""
    result = compare_texts([chekhov], [PUSHKIN * 6], window=None)
    assert result["n_windows"] == {"a": 1, "b": 1}
    assert result["features"][0]["p_holm"] is None
    (warning,) = result["warnings"]
    assert warning.startswith("Ни одно различие не значимо после поправки Холма")
    assert "окон в A - 1, в B - 1" in warning


def test_compare_texts_short():
    with pytest.raises(ToolError, match=r"сравните тексты целиком \(window=null\)$"):
        compare_texts(["Короткий текст"], ["Другой текст"])


def test_compare_texts_limit(monkeypatch, chekhov):
    """Лимит длины действует на корпус целиком"""
    monkeypatch.setenv("RUTS_MCP_MAX_TEXT_LENGTH", str(len(chekhov) + 10))
    with pytest.raises(ToolError, match="лимит"):
        compare_texts([chekhov, chekhov], [PUSHKIN])
