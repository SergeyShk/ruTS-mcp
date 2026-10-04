from typing import get_args

import pytest
from ruts import BasicStats
from ruts.constants import COMPLEX_SYL_FACTOR, LONG_WORD_LETTER_FACTOR

from ruts_mcp.stats import (
    BASIC_DISTRIBUTIONS,
    BASIC_STATS,
    GROUPS,
    Group,
    basic_stats,
    language_warnings,
)

TEXT = "Не имей сто рублей, а имей сто друзей. Мама мыла раму — и т. д.!"


def test_groups():
    assert set(GROUPS) == set(get_args(Group))


def test_basic_stats():
    expected = BasicStats(TEXT, normalize=True).get_stats()
    stats = basic_stats(TEXT)
    assert list(stats) == list(BASIC_STATS)
    for name, item in stats.items():
        assert item["value"] == expected[name]
        assert item["description"] == BASIC_STATS[name]
        share = expected.get("p" + name[1:])
        assert item.get("share") == (None if share is None else round(share, 3))
    assert stats["n_unique_words"] == {
        "value": 12,
        "share": 0.857,
        "description": "Уникальные слова без учета регистра; доля от всех слов",
    }


def test_basic_thresholds():
    """Описания называют пороги ruTS"""
    assert f"от {LONG_WORD_LETTER_FACTOR} букв" in BASIC_STATS["n_long_words"]
    assert f"от {COMPLEX_SYL_FACTOR} слогов" in BASIC_STATS["n_complex_words"]
    assert f"от 1 до {COMPLEX_SYL_FACTOR - 1} слогов" in BASIC_STATS["n_simple_words"]


def test_basic_distributions():
    stats = basic_stats(TEXT, distributions=True)
    assert stats["c_letters"]["value"] == {"1": 4, "2": 1, "3": 2, "4": 5, "6": 2}
    assert stats["c_syllables"]["value"] == {"0": 2, "1": 5, "2": 7}
    assert stats["c_punctuations"]["value"] == {
        "comma": 1,
        "period": 3,
        "exclamation": 1,
        "dash": 1,
    }
    assert not BASIC_DISTRIBUTIONS.keys() & basic_stats(TEXT).keys()


UKRAINIAN = "Він прийшов додому пізно ввечері, і мати вже спала. Київ засинав."


@pytest.mark.parametrize(
    ("text", "start"),
    [
        ("Hello world", "Букв русского алфавита - только 0%: "),
        ("ab" * 501 + "аб" * 499, "Букв русского алфавита - только 49%: "),
        ("аб abc", "Букв русского алфавита - только 40%: "),
        ("а" * 29 + " " + "a" * 71, "Букв русского алфавита - только 29%: "),
        (UKRAINIAN, "Букв кириллицы не из русского алфавита - 9% (і, ї): "),
        ("Србија и Југославија", "Букв кириллицы не из русского алфавита - 16% (ј): "),
    ],
    ids=["latin", "floor", "mixed", "exact", "ukrainian", "serbian"],
)
def test_language_warnings(text, start):
    (warning,) = language_warnings(text)
    assert warning.startswith(start)


@pytest.mark.parametrize(
    "text",
    [
        TEXT,
        "абв abc",
        "Это API для LLM-агента, а не SDK",
        "Он вернулся из Киева поздно вечером и вспоминал Київ.",
        "12345 !!!",
    ],
    ids=["russian", "half", "terms", "name", "digits"],
)
def test_no_language_warnings(text):
    assert language_warnings(text) == []


def test_both_language_warnings():
    assert len(language_warnings("Він hello world")) == 2
