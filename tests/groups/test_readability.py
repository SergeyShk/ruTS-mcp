from ruts import BasicStats, ReadabilityStats
from ruts.constants import READABILITY_STATS_DESC

from ruts_mcp.analysis import Analysis, Options, clean
from ruts_mcp.groups.basic import basic_group
from ruts_mcp.groups.readability import READABILITY_STATS, readability_group

RIDDLE = "Ног нет, а хожу, рта нет, а скажу: когда спать, когда вставать, когда работу начинать"


def test_readability_group():
    stats, _ = readability_group(Analysis(RIDDLE))
    rs = ReadabilityStats(RIDDLE)
    assert list(stats) == list(READABILITY_STATS)
    assert set(READABILITY_STATS) == set(READABILITY_STATS_DESC)
    assert {name: item["value"] for name, item in stats.items()} == {
        name: clean(value) for name, value in rs.get_stats().items()
    }
    assert stats["smog_index"]["description"] == (
        f"Индекс SMOG: число лет обучения по словам от {rs.smog_complex_syl_factor} слогов "
        "на предложение"
    )
    assert f"от {rs.lix_long_word_letter_factor} букв" in stats["rix"]["description"]
    assert f"скорости {rs.reading_speed} слов" in stats["reading_time"]["description"]
    assert all("{" not in item["description"] for item in stats.values())
    for name, item in stats.items():
        assert item.get("interpretation") == rs.describe(name)
    assert stats["consensus_grade"]["interpretation"] == "1-3-й класс (6-8 лет)"
    # Индекс Флеша 87.17 - 6-й класс, RIX 2.0 - 6-й класс, LIX 28.33 - ниже 30
    assert stats["flesch_reading_easy"]["interpretation"] == "6-й класс"
    assert stats["rix"]["interpretation"] == "4-6-й класс (9-11 лет)"
    assert stats["lix"]["interpretation"] == "очень простые тексты, детские книги"
    assert "interpretation" not in stats["matskovsky_index"]
    assert "interpretation" not in stats["reading_time"]


def test_readability_preset():
    stats, _ = readability_group(Analysis(RIDDLE, Options(preset="fiction")))
    fiction = ReadabilityStats(RIDDLE, preset="fiction").flesch_kincaid_grade
    assert stats["flesch_kincaid_grade"]["value"] == clean(fiction)
    assert fiction != ReadabilityStats(RIDDLE).flesch_kincaid_grade


def test_readability_shares_basic(monkeypatch):
    """Группы basic и readability считают базовые статистики один раз"""
    calls = []
    init = BasicStats.__init__

    def counting_init(self, *args, **kwargs):
        calls.append(args)
        init(self, *args, **kwargs)

    monkeypatch.setattr(BasicStats, "__init__", counting_init)
    analysis = Analysis(RIDDLE)
    basic_group(analysis)
    readability_group(analysis)
    assert calls == [(RIDDLE,)]


def test_readability_warnings(chekhov):
    _, warnings = readability_group(Analysis(RIDDLE))
    assert len(warnings) == 1
    assert warnings[0].startswith("Предложений в тексте: 1, меньше 30. Формулы удобочитаемости")
    assert "включая сводный класс" in warnings[0]
    assert readability_group(Analysis(chekhov))[1] == []
