from ruts import PhonStats
from ruts.constants import PHON_STATS_DESC

from ruts_mcp.analysis import Analysis, clean
from ruts_mcp.groups.phon import PHON_NOTES, phon_group


def test_phon_group(chekhov):
    stats, warnings = phon_group(Analysis(chekhov))
    ps = PhonStats(chekhov)
    assert set(PHON_NOTES) <= set(PHON_STATS_DESC)
    assert {name: item["value"] for name, item in stats.items()} == {
        name: clean(value) for name, value in ps.get_stats().items()
    }
    for name, item in stats.items():
        assert item["description"].startswith(PHON_STATS_DESC[name])
    assert stats["p_open_syllables"]["description"] == PHON_STATS_DESC["p_open_syllables"]
    assert f"окна из {ps.window_len} слов" in stats["alliteration"]["description"]
    assert warnings == []


def test_phon_undefined():
    """Текст короче окна аллитерации не дает индексов повторов"""
    stats, warnings = phon_group(Analysis("Мама"))
    assert stats["alliteration"]["value"] is None
    assert stats["assonance"]["value"] is None
    (warning,) = warnings
    assert warning.startswith("Не определены на этом тексте: ")
    assert "alliteration, assonance" in warning
