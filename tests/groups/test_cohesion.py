import pytest
from ruts import CohesionStats
from ruts.constants import COHESION_STATS_DESC

from ruts_mcp.analysis import Analysis, clean
from ruts_mcp.groups.cohesion import (
    COHESION_NOTES,
    OVERLAP_REASON,
    TEMPORAL_REASON,
    cohesion_group,
)


def test_cohesion_group(chekhov):
    stats, warnings = cohesion_group(Analysis(chekhov))
    assert set(COHESION_NOTES) <= set(stats)
    assert {name: item["value"] for name, item in stats.items()} == {
        name: clean(value) for name, value in CohesionStats(chekhov).get_stats().items()
    }
    for name, item in stats.items():
        assert item["description"].startswith(COHESION_STATS_DESC[name])
        assert item["description"].endswith(", от 0 до 1") == (name in COHESION_NOTES)
    assert stats["noun_overlap_adjacent"]["description"] == (
        "Повтор существительных в соседних предложениях: доля пар соседних предложений "
        "с общим существительным, от 0 до 1"
    )
    assert warnings == []


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Мама мыла раму.", {OVERLAP_REASON: 8, TEMPORAL_REASON: 3}),
        ("Он ушёл. Она пришла. Мы спим.", {"в тексте нет существительных": 1}),
        ("Иди домой. Открой окно. Ложись спать.", {TEMPORAL_REASON: 2}),
        (
            "123 456 789",
            {
                OVERLAP_REASON: 8,
                "в тексте нет существительных": 1,
                "в тексте нет знаменательных слов": 1,
                TEMPORAL_REASON: 3,
            },
        ),
    ],
    ids=["one-sentence", "no-nouns", "imperatives", "numbers"],
)
def test_cohesion_reasons(text, expected):
    """Каждое предупреждение называет причину своих метрик"""
    stats, warnings = cohesion_group(Analysis(text))
    reasons = {}
    for warning in warnings:
        names, reason = warning.removeprefix("Не определены на этом тексте: ").split(" - ", 1)
        reasons[reason] = len(names.split(", "))
        assert all(stats[name]["value"] is None for name in names.split(", "))
    assert reasons == expected
