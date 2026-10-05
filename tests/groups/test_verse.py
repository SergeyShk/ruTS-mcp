import pytest
from ruts import VerseStats
from ruts.constants import RHYME_WINDOW, VERSE_STATS_DESC
from ruts.datasets import StressDict

from ruts_mcp.analysis import Analysis, clean
from ruts_mcp.groups.verse import (
    CLAUSULA_REASON,
    NO_LINES_REASON,
    RHYME_SCHEMES,
    TOP_SCHEMES,
    VERSE_NOTES,
    verse_group,
)
from tests.conftest import PUSHKIN

METER_STATS = "meter, n_feet, p_deviations, p_pyrrhics"


def test_verse_group(dicts):
    stats, warnings = verse_group(Analysis(PUSHKIN))
    vs = VerseStats(PUSHKIN, stress_dict=StressDict(dicts))
    assert set(VERSE_NOTES) == set(VERSE_STATS_DESC)
    assert {name: item["value"] for name, item in stats.items()} == {
        name: clean(value) for name, value in vs.get_stats().items()
    } | {"rhyme_schemes": {"ABAB": 1}}
    assert (stats["meter"]["value"], stats["n_feet"]["value"]) == ("ямб", 4)
    for name, item in stats.items():
        assert item["description"].startswith(
            VERSE_STATS_DESC.get(name, RHYME_SCHEMES.format(top=TOP_SCHEMES))
        )
    assert f"не дальше {RHYME_WINDOW} строк" in stats["p_rhymed"]["description"]
    assert warnings == []


def test_verse_without_dict(data_dir):
    """Без словаря ударений группа пуста, предупреждение называет команду"""
    stats, warnings = verse_group(Analysis(PUSHKIN))
    assert stats == {}
    (warning,) = warnings
    assert warning.startswith(
        "Словарь ударений Козиева не скачан: группа verse не посчитана. "
        "Словари скачивает команда ruts-mcp download"
    )


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (
            "Hello world",
            [f"{METER_STATS}, p_rhymed, p_masculine, p_feminine, p_dactylic - {NO_LINES_REASON}"],
        ),
        (
            "Абырвалг кукарямба",
            [
                f"{METER_STATS} - метр не определен",
                f"p_masculine, p_feminine, p_dactylic - {CLAUSULA_REASON}",
            ],
        ),
    ],
)
def test_verse_undefined(dicts, text, expected):
    """Причины неопределенных статистик: нет русских строк, метр, ударение последних слов"""
    _, warnings = verse_group(Analysis(text))
    for warning, start in zip(warnings, expected, strict=True):
        assert warning.startswith(f"Не определены на этом тексте: {start}")


def test_verse_prose(dicts, chekhov):
    """У прозы метр не определен, окончания строк посчитаны"""
    stats, warnings = verse_group(Analysis(chekhov))
    assert stats["meter"]["value"] is None
    assert stats["p_rhymed"]["value"] == 0.0
    (warning,) = warnings
    assert "меньше 6 словарных ударений многосложных слов" in warning


def test_verse_rhyme_schemes(dicts):
    """Схемы рифмовки - самые частые, не больше TOP_SCHEMES, с числом строф"""
    text = "\n\n".join("\n".join(["Абырвалг кукарямба"] * size) for size in range(1, 13))
    stats, _ = verse_group(Analysis(text))
    assert stats["n_stanzas"]["value"] == 12
    assert stats["rhyme_schemes"]["value"] == {"-" * size: 1 for size in range(1, 11)}


def test_verse_new_metric(dicts, monkeypatch):
    """Статистика новой версии ruTS без пояснения сервера отдается с описанием ruTS"""
    monkeypatch.setitem(VERSE_STATS_DESC, "p_enjambments", "Доля переносов")
    monkeypatch.setattr(VerseStats, "p_enjambments", 0.25, raising=False)
    stats, _ = verse_group(Analysis(PUSHKIN))
    assert stats["p_enjambments"] == {"value": 0.25, "description": "Доля переносов"}
