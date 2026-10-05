import pytest
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
        value, share = stats[name]["value"], stats[name]["share"]
        assert value == {labels[code]: count for code, count in counts.items()}
        assert list(value.values()) == sorted(value.values(), reverse=True)
        assert share == {label: clean(count / len(ms.words)) for label, count in value.items()}
        assert stats[name]["description"].startswith(MORPHOLOGY_STATS_DESC[name]["name"])
    for name, share in ms.get_markers().items():
        assert stats[name]["value"] == clean(share)
        assert stats[name]["description"].startswith(MORPHOLOGY_MARKERS_DESC[name])
    assert warnings == []


def test_morph_shares_compare_lengths(chekhov):
    """Доля сравнивает тексты разной длины, где число слов вводит в заблуждение"""
    whole = morph_group(Analysis(chekhov))[0]["pos"]
    start = morph_group(Analysis(" ".join(chekhov.split()[:61])))[0]["pos"]
    noun = "Имя существительное"
    assert whole["value"][noun] > start["value"][noun]
    assert whole["share"][noun] < start["share"][noun]


@pytest.mark.parametrize(
    ("text", "bases"),
    [
        ("Надо идти. Надо спать.", ["личных форм"]),
        ("Красивый дом у реки.", ["личных форм", "форм глагола", "форм глагола с видом"]),
    ],
    ids=["infinitives", "no-verbs"],
)
def test_morph_undefined_by_base(text, bases):
    """Предупреждение называет базу, которой нет, а доли с другой базой остаются"""
    stats, warnings = morph_group(Analysis(text))
    assert [w.split(" - ", 1)[1] for w in warnings] == [
        f"в тексте нет {base}, от которых считается доля" for base in bases
    ]
    assert (stats["p_infinitive"]["value"] is None) == ("форм глагола" in bases)


def test_morph_without_verbs():
    stats, _ = morph_group(Analysis("Красивый дом у реки."))
    assert stats["pos"]["value"] == {
        "Имя существительное": 2,
        "Имя прилагательное": 1,
        "Предлог": 1,
    }
    assert stats["tense"] == {
        "value": {},
        "share": {},
        "description": stats["tense"]["description"],
    }


def test_morph_labels_unique():
    """Значения признака подписываются названиями ruTS, и счетчики не сливаются"""
    for feature in MORPHOLOGY_STATS_DESC.values():
        labels = list(feature["values"].values())
        assert len(labels) == len(set(labels))
