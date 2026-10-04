from ruts import BasicStats
from ruts.constants import COMPLEX_SYL_FACTOR, LONG_WORD_LETTER_FACTOR

from ruts_mcp.analysis import Analysis, Options, clean
from ruts_mcp.groups.basic import BASIC_DISTRIBUTIONS, BASIC_STATS, basic_group

TEXT = "Не имей сто рублей, а имей сто друзей. Мама мыла раму — и т. д.!"


def test_basic_group():
    expected = BasicStats(TEXT, normalize=True).get_stats()
    stats, warnings = basic_group(Analysis(TEXT))
    assert warnings == []
    assert list(stats) == list(BASIC_STATS)
    for name, item in stats.items():
        assert item["value"] == expected[name]
        assert item["description"] == BASIC_STATS[name]
        assert item.get("share") == clean(expected.get("p" + name[1:]))
    assert stats["n_unique_words"] == {
        "value": 12,
        "share": 0.8571,
        "description": "Уникальные слова без учета регистра; доля от всех слов",
    }


def test_basic_thresholds():
    """Описания называют пороги ruTS"""
    assert f"от {LONG_WORD_LETTER_FACTOR} букв" in BASIC_STATS["n_long_words"]
    assert f"от {COMPLEX_SYL_FACTOR} слогов" in BASIC_STATS["n_complex_words"]
    assert f"от 1 до {COMPLEX_SYL_FACTOR - 1} слогов" in BASIC_STATS["n_simple_words"]


def test_basic_distributions():
    stats, _ = basic_group(Analysis(TEXT, Options(distributions=True)))
    assert stats["c_letters"]["value"] == {"1": 4, "2": 1, "3": 2, "4": 5, "6": 2}
    assert stats["c_syllables"]["value"] == {"0": 2, "1": 5, "2": 7}
    assert stats["c_punctuations"]["value"] == {
        "comma": 1,
        "period": 3,
        "exclamation": 1,
        "dash": 1,
    }
    assert not BASIC_DISTRIBUTIONS.keys() & basic_group(Analysis(TEXT))[0].keys()
