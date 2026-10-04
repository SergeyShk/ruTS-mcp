from ruts import DiversityStats
from ruts.constants import DIVERSITY_STATS_DESC

from ruts_mcp.analysis import Analysis, clean
from ruts_mcp.groups.diversity import DIVERSITY_STATS, diversity_group


def test_diversity_group(chekhov):
    stats, warnings = diversity_group(Analysis(chekhov))
    expected = DiversityStats(chekhov).get_stats()
    assert list(stats) == list(DIVERSITY_STATS)
    assert set(DIVERSITY_STATS) == set(DIVERSITY_STATS_DESC)
    assert stats == {
        name: {"value": clean(expected[name]), "description": description}
        for name, description in DIVERSITY_STATS.items()
    }
    assert warnings == []


def test_diversity_short_text():
    stats, warnings = diversity_group(Analysis("Мама мыла раму, а папа мыл пол."))
    assert stats["hdd"]["value"] is None
    assert warnings[0].startswith("Слов в тексте: 7, меньше 50: меры лексического разнообразия")
    assert warnings[1].startswith("Не определены на этом тексте: sttr, dttr, mtld, mamtld, ")
    assert warnings[1].endswith("нет слов, встреченных один или два раза")


def test_diversity_medium_text(chekhov):
    text = " ".join(chekhov.split()[:120])
    stats, warnings = diversity_group(Analysis(text))
    assert warnings[0].startswith("Слов в тексте: 114, меньше 200. По Zenker и Kyle (2021)")
    assert warnings[0].endswith("сравнивайте тексты по MATTR, MTLD и HD-D")
    assert all(stats[name]["value"] is not None for name in ("mattr", "mtld", "hdd"))


def test_diversity_repeats():
    """На тексте из одних повторов не определены меры, которым нужны гапаксы или разные слова"""
    stats, warnings = diversity_group(Analysis(" ".join(["слово"] * 300) + "."))
    undefined = [name for name, item in stats.items() if item["value"] is None]
    assert undefined == ["sttr", "michea_m", "alpha2", "evenness", "zipf_alpha"]
    (warning,) = warnings
    assert warning.startswith(f"Не определены на этом тексте: {', '.join(undefined)} - ")
