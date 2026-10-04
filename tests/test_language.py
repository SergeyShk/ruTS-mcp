import pytest

from ruts_mcp.language import language_warnings

TEXT = "Не имей сто рублей, а имей сто друзей. Мама мыла раму — и т. д.!"


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
