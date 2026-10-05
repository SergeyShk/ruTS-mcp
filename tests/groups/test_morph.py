from ruts import MorphStats
from ruts.constants import MORPHOLOGY_MARKERS_DESC, MORPHOLOGY_STATS_DESC

from ruts_mcp.analysis import Analysis, clean
from ruts_mcp.groups.morph import morph_group


def test_morph_group(chekhov):
    stats, warnings = morph_group(Analysis(chekhov))
    ms = MorphStats(chekhov)
    features = ms.get_stats(filter_none=True)
    assert list(stats) == [*features, *ms.get_markers()]
    for name, counts in features.items():
        labels = MORPHOLOGY_STATS_DESC[name]["values"]
        value = stats[name]["value"]
        assert value == {labels[code]: count for code, count in counts.items()}
        assert list(value.values()) == sorted(value.values(), reverse=True)
        assert stats[name]["description"].startswith(MORPHOLOGY_STATS_DESC[name]["name"])
    for name, share in ms.get_markers().items():
        assert stats[name]["value"] == clean(share)
        assert stats[name]["description"].startswith(MORPHOLOGY_MARKERS_DESC[name])
    assert warnings == []


def test_morph_without_verbs():
    """Без форм глагола доли не определены, а признаки без значения не попадают в ответ"""
    stats, warnings = morph_group(Analysis("Красивый дом у реки."))
    assert stats["pos"]["value"] == {
        "Имя существительное": 2,
        "Имя прилагательное": 1,
        "Предлог": 1,
    }
    assert stats["tense"]["value"] == {}
    assert all(stats[name]["value"] is None for name in MORPHOLOGY_MARKERS_DESC)
    (warning,) = warnings
    assert warning.startswith("Не определены на этом тексте: p_indicative, ")
    assert warning.endswith("в тексте нет форм глагола, от которых считается доля")


def test_morph_labels_unique():
    """Значения признака подписываются названиями ruTS, и счетчики не сливаются"""
    for feature in MORPHOLOGY_STATS_DESC.values():
        labels = list(feature["values"].values())
        assert len(labels) == len(set(labels))
