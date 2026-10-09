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
from ruts_mcp.inputs import prepare_text
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


def test_verse_stress_marks(dicts):
    """Знак ударения в тексте важнее словаря: «прави́л» - мужское окончание строки"""
    marked = PUSHKIN.replace("правил", "прави\u0301л")
    stats, _ = verse_group(Analysis(prepare_text(marked)))
    vs = VerseStats(marked, stress_dict=StressDict(dicts))
    assert stats["p_masculine"]["value"] == clean(vs.p_masculine) == 0.75
    assert stats["rhyme_schemes"]["value"] == {"-A-A": 1}


def test_verse_without_dict(data_dir):
    """Без словаря ударений группа пуста, предупреждение называет команду"""
    stats, warnings = verse_group(Analysis(PUSHKIN))
    assert stats == {}
    (warning,) = warnings
    assert warning.startswith(
        "Словарь ударений Козиева не скачан: группа verse не посчитана. "
        "Словари и модель скачивает команда ruts-mcp "
        "download"
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


def test_verse_long_scheme(dicts, monkeypatch):
    """Длинная схема обрезается, а строфы с одинаковым началом схемы считаются вместе"""
    monkeypatch.setattr("ruts_mcp.groups.verse.MAX_SCHEME", 4)
    text = "\n\n".join("\n".join(["Абырвалг кукарямба"] * size) for size in (4, 5, 6))
    stats, _ = verse_group(Analysis(text))
    assert stats["rhyme_schemes"]["value"] == {"---…": 2, "----": 1}
    assert "длиннее 32 строк обрезана" in stats["rhyme_schemes"]["description"]


def test_verse_ladder(dicts, monkeypatch):
    """Много пропущенных ударений - метр мог быть подобран случайно, как у стиха лесенкой"""
    assert not [item for item in verse_group(Analysis(PUSHKIN))[1] if "лесенкой" in item]
    monkeypatch.setattr("ruts_mcp.groups.verse.LADDER_PYRRHICS", 0.1)
    assert verse_group(Analysis(PUSHKIN))[1] == [
        "Метр ямб (4-стопный, доля пропущенных ударений 0.1875) может быть случайным: так "
        "бывает со стихом, записанным лесенкой, и с текстом, где строка - не стих. Стих "
        "лесенкой соберите в строки по смыслу и посчитайте заново"
    ]


def test_verse_one_foot(dicts, monkeypatch):
    init = VerseStats.__init__

    def one_foot(self, *args, **kwargs):
        init(self, *args, **kwargs)
        self.n_feet = 1

    monkeypatch.setattr(VerseStats, "__init__", one_foot)
    (warning,) = verse_group(Analysis(PUSHKIN))[1]
    assert warning.startswith("Метр ямб (1-стопный, доля пропущенных ударений 0.1875)")
