import pytest
from ruts import LexicalStats
from ruts.constants import LEXICAL_STATS_DESC
from ruts.datasets import FreqDict

from ruts_mcp.analysis import NO_WORDS_WARNING, Analysis, clean
from ruts_mcp.groups.lexical import (
    CONTENT_NOT_FOUND_REASON,
    LEXICAL_NOTES,
    NOT_FOUND_REASON,
    lexical_group,
)
from ruts_mcp.groups.verse import verse_group
from tests.conftest import CAT

DICT_STATS = [
    "coverage",
    "mean_ipm",
    "mean_ipm_content",
    "mean_log_ipm",
    "mean_log_ipm_content",
    "mean_range",
    "mean_dispersion",
    "surprisal",
    "perplexity",
]


def test_lexical_group(dicts):
    stats, warnings = lexical_group(Analysis(CAT))
    expected = LexicalStats(CAT, freq_dict=FreqDict(dicts)).get_stats()
    assert set(LEXICAL_NOTES) == set(LEXICAL_STATS_DESC)
    assert {name: item["value"] for name, item in stats.items()} == {
        name: clean(value) for name, value in expected.items()
    }
    for name, item in stats.items():
        assert item["description"].startswith(f"{LEXICAL_STATS_DESC[name]}: ")
    assert stats["coverage"]["value"] == 1.0
    assert warnings == []


def test_lexical_without_dict(data_dir):
    """Без словаря метрики по словарю - None, полосы и плотность посчитаны"""
    stats, warnings = lexical_group(Analysis(CAT))
    assert [name for name, item in stats.items() if item["value"] is None] == DICT_STATS
    assert stats["p_top1000"]["value"] == 0.75
    assert stats["lexical_density"]["value"] == 0.625
    (warning,) = warnings
    assert warning.startswith(
        f"Частотный словарь Ляшевской и Шарова не скачан: метрики {', '.join(DICT_STATS)} "
        "не посчитаны. Словари скачивает команда ruts-mcp download"
    )
    assert warning.endswith(f"в каталог {data_dir / 'dicts'}")


NOT_FOUND = (
    "Не определены на этом тексте: mean_ipm, mean_log_ipm, mean_range, mean_dispersion - "
    f"{NOT_FOUND_REASON}"
)
CONTENT_NOT_FOUND = (
    "Не определены на этом тексте: mean_ipm_content, mean_log_ipm_content - "
    f"{CONTENT_NOT_FOUND_REASON}"
)


@pytest.mark.parametrize(
    ("text", "expected"),
    [("Абырвалг кукарямба", [NOT_FOUND, CONTENT_NOT_FOUND]), ("И на", [CONTENT_NOT_FOUND])],
)
def test_lexical_undefined(dicts, text, expected):
    """Средние без найденных в словаре слов не определены, причина - в предупреждении"""
    stats, warnings = lexical_group(Analysis(text))
    assert warnings == expected
    assert stats["coverage"]["value"] == (0.0 if len(expected) == 2 else 1.0)


@pytest.mark.parametrize("group", [lexical_group, verse_group])
def test_numbers_only(dicts, group):
    """Числа - не слова для lexical и verse: группа пуста, вызов не падает"""
    name = group.__name__.removesuffix("_group")
    assert group(Analysis("2020 5.5")) == ({}, [NO_WORDS_WARNING.format(group=name)])


def test_lexical_new_metric(dicts, monkeypatch):
    """Метрика новой версии ruTS без пояснения сервера отдается с описанием ruTS"""
    monkeypatch.setitem(LEXICAL_STATS_DESC, "rare_share", "Доля редких слов")
    monkeypatch.setattr(LexicalStats, "rare_share", 0.5, raising=False)
    stats, _ = lexical_group(Analysis(CAT))
    assert stats["rare_share"] == {"value": 0.5, "description": "Доля редких слов"}
