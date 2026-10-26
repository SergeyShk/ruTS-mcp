import pytest
from ruts import CohesionStats
from ruts.constants import COHESION_STATS_DESC

from ruts_mcp.analysis import Analysis, clean
from ruts_mcp.groups.cohesion import (
    COHESION_NOTES,
    CONNECTOR_NOTES,
    FEW_SENTS_REASON,
    ONE_PARAGRAPH_REASON,
    OVERLAP_REASON,
    TEMPORAL_REASON,
    cohesion_group,
)

NO_NOUNS = "в тексте нет существительных"
NO_SENT_NOUNS = "в предложениях текста, кроме двух последних, нет существительных"


def test_cohesion_group(chekhov):
    stats, warnings = cohesion_group(Analysis(chekhov))
    assert set(COHESION_NOTES) | set(CONNECTOR_NOTES) <= set(stats)
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
    assert stats["noun_overlap_para"]["description"] == (
        "Повтор существительных в соседних абзацах: доля существительных абзаца (строки "
        "текста), повторенных в следующем абзаце, от 0 до 1"
    )
    assert stats["connectors_intra"]["description"] == (
        "Внутрипредложенческих коннекторов на 1000 слов: все, кроме межпредложенческих, - "
        "не в начале предложения («Он, однако, ушел») и подчинительные союзы и предлоги "
        "в начале («Когда он пришел»)"
    )
    assert warnings == []


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (
            "Мама мыла раму.",
            {OVERLAP_REASON: 8, FEW_SENTS_REASON: 3, ONE_PARAGRAPH_REASON: 3, TEMPORAL_REASON: 3},
        ),
        (
            "Он ушёл. Она пришла. Мы спим.",
            {NO_SENT_NOUNS: 1, ONE_PARAGRAPH_REASON: 3, NO_NOUNS: 1},
        ),
        (
            "Иди домой. Открой окно. Ложись спать.",
            {
                NO_SENT_NOUNS: 1,
                "в предложениях текста, кроме двух последних, нет существительных и местоимений": 1,
                ONE_PARAGRAPH_REASON: 3,
                TEMPORAL_REASON: 2,
            },
        ),
        (
            "Он ушёл.\nОна пришла.\nМы спим.",
            {
                NO_SENT_NOUNS: 1,
                "в абзацах текста, кроме последнего, нет существительных": 1,
                NO_NOUNS: 1,
            },
        ),
        (
            "123 456 789",
            {
                OVERLAP_REASON: 8,
                FEW_SENTS_REASON: 3,
                ONE_PARAGRAPH_REASON: 3,
                NO_NOUNS: 1,
                "в тексте нет знаменательных слов": 1,
                TEMPORAL_REASON: 3,
            },
        ),
        # Номер главы без знаменательных слов присоединяется к следующей строке: абзац один
        ("I\nКот спит. Пес лает.", {FEW_SENTS_REASON: 3, ONE_PARAGRAPH_REASON: 3}),
    ],
    ids=["one-sentence", "no-nouns", "imperatives", "lines", "numbers", "heading-line"],
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
