import pytest
from ruts import StyleStats
from ruts.constants import STYLE_NORMS, STYLE_STATS_DESC

from ruts_mcp.analysis import Analysis, clean
from ruts_mcp.groups.style import MIN_WORDS, STYLE_NOTES, STYLE_REASONS, style_group


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


@pytest.mark.parametrize(("n_words", "short"), [(MIN_WORDS - 1, True), (MIN_WORDS, False)])
def test_style_short_text(n_words, short):
    """Оговорка о нормах сервисов - у текста короче 200 слов"""
    _, warnings = style_group(Analysis("кот пес " * (n_words // 2) + "кот" * (n_words % 2)))
    assert any(w.startswith("Слов в тексте: ") for w in warnings) is short
