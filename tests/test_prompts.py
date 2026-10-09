import pytest

from ruts_mcp.prompts import (
    READ_WARNINGS,
    compare_review,
    officialese_review,
    readability_review,
    seo_review,
    verse_review,
)

TEXT = "Мама мыла раму."


@pytest.mark.parametrize(
    ("prompt", "calls"),
    [
        (readability_review, ["analyze_text с группами basic, readability и syntax"]),
        (officialese_review, ["analyze_text с группами style и syntax", "kwic"]),
        (verse_review, ["analyze_text с группами verse и phon"]),
        (seo_review, ["analyze_text с группой style", "keyness без reference"]),
    ],
)
def test_text_prompts(prompt, calls):
    message = prompt(TEXT)
    assert message.endswith(f"Текст:\n\n{TEXT}")
    assert READ_WARNINGS in message
    for call in calls:
        assert call in message


def test_compare_review():
    message = compare_review("Текст первый.", "Текст второй.")
    assert "compare_texts с a = [текст A] и b = [текст B]" in message
    assert "keyness с текстом A и reference = текст B" in message
    assert "половине числа его слов, но не меньше 100" in message
    assert "меньше 150 слов, compare_texts не подойдет" in message
    assert message.endswith("Текст A:\n\nТекст первый.\n\nТекст B:\n\nТекст второй.")
