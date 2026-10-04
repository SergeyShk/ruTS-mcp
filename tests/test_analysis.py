import pytest
from ruts import BasicStats

from ruts_mcp.analysis import Analysis, Options, clean, stat, undefined_warnings


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (0.0061549, 0.006155),
        (1771.13, 1771.0),
        (-9.00333, -9.003),
        (float("nan"), None),
        (float("inf"), None),
        (float("-inf"), None),
        (7, 7),
        ("ямб", "ямб"),
        (None, None),
    ],
)
def test_clean(value, expected):
    assert clean(value) == expected


def test_stat():
    assert stat(1, "Слова") == {"value": 1, "description": "Слова"}
    item = stat(0.12345, "Доля", share=0.56789, interpretation="мало")
    assert item == {
        "value": 0.1235,
        "share": 0.5679,
        "interpretation": "мало",
        "description": "Доля",
    }
    assert list(item) == ["value", "share", "interpretation", "description"]
    assert stat(float("inf"), "Мера") == {"value": None, "description": "Мера"}


def test_undefined_warnings():
    stats = {"a": stat(float("nan"), "A"), "b": stat(1.0, "B"), "c": stat(float("inf"), "C")}
    assert undefined_warnings(stats, "причина") == ["Не определены на этом тексте: a, c - причина"]
    assert undefined_warnings({"b": stat(1.0, "B")}, "причина") == []


def test_analysis():
    analysis = Analysis("Мама мыла раму.")
    assert analysis.options == Options(distributions=False, preset="plainrussian")
    assert isinstance(analysis.basic, BasicStats)
    assert analysis.basic is analysis.basic
