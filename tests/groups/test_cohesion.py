from ruts import CohesionStats
from ruts.constants import COHESION_STATS_DESC

from ruts_mcp.analysis import Analysis, clean
from ruts_mcp.groups.cohesion import cohesion_group


def test_cohesion_group(chekhov):
    stats, warnings = cohesion_group(Analysis(chekhov))
    assert {name: item["value"] for name, item in stats.items()} == {
        name: clean(value) for name, value in CohesionStats(chekhov).get_stats().items()
    }
    for name, item in stats.items():
        assert item["description"].startswith(COHESION_STATS_DESC[name])
        assert item["description"].endswith(", от 0 до 1") == ("_overlap_" in name)
    assert warnings == []


def test_cohesion_one_sentence():
    """Повторы между предложениями не определены на тексте из одного предложения"""
    stats, warnings = cohesion_group(Analysis("Мама мыла раму."))
    assert stats["noun_overlap_adjacent"]["value"] is None
    assert stats["temporal_cohesion"]["value"] is None
    assert stats["p_pronouns"]["value"] == 0.0
    (warning,) = warnings
    assert warning.startswith("Не определены на этом тексте: noun_overlap_adjacent, ")
