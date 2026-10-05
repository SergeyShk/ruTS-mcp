import pytest
from ruts import StyleStats
from ruts.constants import STYLE_NORMS, STYLE_STATS_DESC

from ruts_mcp.analysis import Analysis, clean
from ruts_mcp.groups.style import (
    MAX_WORDS,
    MIN_WORDS,
    STYLE_NOTES,
    STYLE_REASONS,
    style_group,
)


def test_style_group(chekhov):
    stats, warnings = style_group(Analysis(chekhov))
    ss = StyleStats(chekhov)
    assert list(STYLE_NOTES) == list(STYLE_STATS_DESC)
    assert {name: item["value"] for name, item in stats.items()} == {
        name: clean(value) for name, value in ss.get_stats().items()
    }
    assert {name: item.get("interpretation") for name, item in stats.items()} == {
        name: ss.describe(name) for name in STYLE_STATS_DESC
    }
    assert {name for name, item in stats.items() if "interpretation" in item} == set(STYLE_NORMS)
    for name, item in stats.items():
        assert item["description"].startswith(f"{STYLE_STATS_DESC[name]}: ")
    assert f"{ss.top_n} самых частых слов" in stats["academic_nausea"]["description"]
    assert all("{" not in item["description"] for item in stats.values())
    assert warnings == []


@pytest.mark.parametrize(
    ("text", "undefined"),
    [
        ("Мама мыла раму.", ["zipf_naturalness"]),
        ("Ушел, ушел, ушел.", ["zipf_naturalness", "verbal_nouns"]),
    ],
)
def test_style_undefined(text, undefined):
    """Неопределенная метрика отдается без прочтения, с причиной в предупреждении"""
    stats, warnings = style_group(Analysis(text))
    for name in undefined:
        assert "interpretation" not in stats[name]
        assert stats[name]["value"] is None
    assert warnings[1:] == [
        f"Не определены на этом тексте: {name} - {STYLE_REASONS[name]}" for name in undefined
    ]


@pytest.mark.parametrize(
    ("n_words", "expected"),
    [
        (MIN_WORDS - 1, [f"Слов в тексте: {MIN_WORDS - 1}, меньше {MIN_WORDS}."]),
        (MIN_WORDS, []),
        (MAX_WORDS, []),
        (MAX_WORDS + 1, [f"Слов в тексте: {MAX_WORDS + 1}, больше {MAX_WORDS}."]),
    ],
)
def test_style_length(n_words, expected):
    """Оговорка о нормах сервисов - у текста короче 200 и длиннее 1000 слов"""
    _, warnings = style_group(Analysis("кот пес " * (n_words // 2) + "кот" * (n_words % 2)))
    assert [w[: len(start)] for w, start in zip(warnings, expected, strict=True)] == expected


def test_style_new_metric(monkeypatch):
    """Метрика новой версии ruTS без пояснения сервера отдается с описанием ruTS"""
    monkeypatch.setitem(STYLE_STATS_DESC, "keyword_stuffing", "Перебор ключевых слов (%)")
    monkeypatch.setattr(StyleStats, "keyword_stuffing", 1.0, raising=False)
    stats, _ = style_group(Analysis("Мама мыла раму."))
    assert stats["keyword_stuffing"] == {"value": 1.0, "description": "Перебор ключевых слов (%)"}
