import pytest

from ruts_mcp.prompts import (
    COMPARE_FROM_CONVERSATION,
    COMPARE_ONE_FROM_CONVERSATION,
    FROM_CONVERSATION,
    READ_WARNINGS,
    TRUNCATED,
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
    assert "compare_texts с a = [текст A] и b = [текст B]: размер окна подбирается" in message
    assert "keyness с текстом A и reference = текст B" in message
    assert "окон меньше двух (в тексте меньше 200 слов)" in message
    assert message.endswith("Текст A:\n\nТекст первый.\n\nТекст B:\n\nТекст второй.")


@pytest.mark.parametrize(
    "prompt", [readability_review, officialese_review, verse_review, seo_review]
)
def test_text_from_conversation(prompt):
    """Без текста промпт берет его из разговора: Claude Code делит аргументы по пробелам"""
    assert prompt().endswith(FROM_CONVERSATION)
    assert prompt("  ") == prompt()
    assert "Текст:" not in prompt()


@pytest.mark.parametrize(
    "prompt", [readability_review, officialese_review, verse_review, seo_review]
)
def test_truncated_argument(prompt):
    """Claude Code делит аргументы по пробелам: из текста в кавычках приходит первое слово"""
    message = prompt(' "Мой ')
    assert message.endswith(
        TRUNCATED.format(arguments='"Мой', from_conversation=FROM_CONVERSATION)
    )
    assert "Текст:" not in message


@pytest.mark.parametrize(
    ("arguments", "truncated"),
    [((), None), (('"текст', 'A"'), '"текст, A"')],
    ids=["empty", "truncated"],
)
def test_compare_from_conversation(arguments, truncated):
    """Без полных текстов сравнение берет оба текста из разговора; обрезанным считается слово"""
    message = compare_review(*arguments)
    if truncated is None:
        assert message.endswith(COMPARE_FROM_CONVERSATION)
    else:
        assert message.endswith(
            TRUNCATED.format(arguments=truncated, from_conversation=COMPARE_FROM_CONVERSATION)
        )
    assert "Текст A:" not in message


@pytest.mark.parametrize(
    ("arguments", "given", "missing", "truncated"),
    [
        (("Текст первый.",), "A", "B", None),
        (("", "Текст второй."), "B", "A", None),
        (('"текст', "Текст второй."), "B", "A", '"текст'),
    ],
    ids=["a", "b", "truncated-a"],
)
def test_compare_one_text(arguments, given, missing, truncated):
    """Полный аргумент - текст сравнения, а из разговора берется только недостающий"""
    message = compare_review(*arguments)
    instruction = COMPARE_ONE_FROM_CONVERSATION.format(label=missing)
    if truncated is not None:
        instruction = TRUNCATED.format(arguments=truncated, from_conversation=instruction)
    text = next(argument for argument in arguments if len(argument.split()) > 1)
    assert message.endswith(f"{instruction}\n\nТекст {given}:\n\n{text}")
    assert f"Текст {missing}:" not in message
