from pathlib import Path
from typing import get_args

import pytest
from anyts.constants import G2_CRITICAL_VALUES, KEYNESS_MEASURES as CORE_KEYNESS_MEASURES
from fastmcp.exceptions import ToolError
from ruts.corpus import compare_corpora, keyness as ruts_keyness
from ruts.datasets import FreqDict

from ruts_mcp.analysis import clean
from ruts_mcp.compare import (
    COMPARISON_FIELDS,
    KEYNESS_MEASURES,
    KEYWORD_FIELDS,
    KeynessMeasure,
    auto_window,
    compare_texts,
    keyness,
)
from ruts_mcp.corpus import text_words
from tests.conftest import CAT, PUSHKIN

REFERENCE = "Кот спал. Собака лаяла на кота, а кот спал на окне. Собака ушла."
CHEKHOV_LONG = (Path(__file__).parent / "data" / "chekhov.txt").read_text(encoding="utf-8") * 4


def rows(keywords):
    return [
        {"word": item.word} | {f: clean(getattr(item, f)) for f in KEYWORD_FIELDS}
        for item in keywords
    ]


def test_keyness_dictionary(dicts):
    """Эталон по умолчанию - частотный словарь: словоформы приводятся к его леммам"""
    result = keyness(CAT, min_freq=1)
    expected = ruts_keyness(text_words(CAT, lemmatize=False), FreqDict(dicts), top_n=20)
    assert result["n_words"] == 8
    assert result["reference"] == "частотный словарь Ляшевской и Шарова (НКРЯ, 92 млн слов)"
    assert result["keywords"] == rows(expected)
    assert result["keywords"][0]["word"] == "кот"
    assert result["warnings"] == []


def test_keyness_without_dictionary(data_dir):
    with pytest.raises(ToolError) as info:
        keyness(CAT)
    message = str(info.value)
    assert message.startswith("Частотный словарь Ляшевской и Шарова не скачан: ключевые слова")
    assert "ruts-mcp download" in message
    assert message.endswith("эталоном может быть и другой текст (reference)")


def test_keyness_reference():
    result = keyness(REFERENCE, reference=CAT, min_freq=1)
    expected = ruts_keyness(
        text_words(REFERENCE, lemmatize=True), text_words(CAT, lemmatize=True), top_n=20
    )
    assert result["reference"] == "текст-эталон, 8 слов"
    assert result["keywords"] == rows(expected)
    assert result["keywords"][0]["word"] == "собака"
    negative = keyness(REFERENCE, reference=CAT, positive=False, min_freq=1)
    assert all(item["g2"] < 0 for item in negative["keywords"])


def test_keyness_measures():
    assert list(get_args(KeynessMeasure)) == list(KEYNESS_MEASURES)
    assert set(KEYNESS_MEASURES) == set(CORE_KEYNESS_MEASURES)
    measure = keyness(REFERENCE, reference=CAT)["measure"]
    for level, value in G2_CRITICAL_VALUES.items():
        assert f"{value} - p < {level}" in measure
    result = keyness(REFERENCE, reference=CAT, measure="log_ratio", min_freq=1)
    assert result["measure"].startswith("log_ratio: Log Ratio (Hardie 2014)")
    assert [item["score"] for item in result["keywords"]] == [
        item["log_ratio"] for item in result["keywords"]
    ]


def test_keyness_no_keywords():
    """При min_freq=1 уменьшать нечего: предупреждение говорит, что таких слов нет"""
    assert keyness(CAT, reference=CAT, min_freq=1)["warnings"] == [
        "Слов, которые в тексте чаще, чем в эталоне, нет"
    ]
    assert keyness(CAT, reference=CAT, positive=False, min_freq=1)["warnings"] == [
        "Слов, которые в тексте реже, чем в эталоне, нет"
    ]


def test_keyness_dictionary_words(dicts):
    """Со словарем числа и латиница не сравниваются и не входят в n_words"""
    assert keyness(f"{CAT} 2020 Python", min_freq=1)["n_words"] == 8


def test_keyness_warnings():
    result = keyness(REFERENCE, reference="The cat sleeps", min_freq=10)
    assert result["warnings"] == [
        "Эталон: Букв русского алфавита - только 0%: ruTS считает статистики по правилам "
        "русского языка, для текста на другом языке значения не имеют смысла",
        "Ключевых слов с частотой от 10 нет: уменьшите min_freq",
    ]


def test_compare_texts(chekhov):
    a, b = [chekhov] * 5, [PUSHKIN * 12] * 5
    result = compare_texts(a, b, window=100, top_n=5)
    table = compare_corpora(a, b, window=100, labels=("A", "B"))
    assert result["window"] == 100
    assert result["n_windows"] == {"a": 10, "b": 10}
    assert result["n_texts"] == {"a": 5, "b": 5}
    by_feature = dict(table.iterrows())
    for item in result["features"]:
        row = by_feature[item["feature"]]
        assert item == {"feature": item["feature"]} | {
            field: clean(float(row[column])) for field, column in COMPARISON_FIELDS.items()
        }
    assert abs(result["features"][0]["cliff_delta"]) == table["cliff_delta"].abs().max()
    assert result["features"][0]["p_holm"] < 0.05


def test_compare_texts_ties(chekhov):
    """При равной дельте Клиффа выше признак с большей относительной разностью медиан"""
    result = compare_texts([chekhov], [PUSHKIN * 12], window=100, top_n=10)
    features = result["features"]
    assert all(abs(item["cliff_delta"]) == 1 for item in features)
    relative = [
        abs(item["median_diff"]) / max(abs(item["mean_a"]), abs(item["mean_b"]))
        for item in features
    ]
    assert relative == sorted(relative, reverse=True)
    assert result["warnings"][-1].startswith(
        "Еще 57 признаков с тем же модулем дельты Клиффа 1.0 не показаны"
    )
    everything = compare_texts([chekhov], [PUSHKIN * 12], window=100, top_n=200)
    assert not any(item.startswith("Еще ") for item in everything["warnings"])


def test_compare_texts_single_texts(chekhov):
    """По два окна из одного текста: оговорка об одном тексте и о незначимости"""
    result = compare_texts([chekhov], [PUSHKIN * 12], window=100)
    assert result["n_windows"] == {"a": 2, "b": 2}
    assert result["n_texts"] == {"a": 1, "b": 1}
    assert result["features"][0]["ci_low"] is None
    one_text, _, not_significant, _ = result["warnings"]
    assert one_text.startswith("В корпусе A один текст: интервал разности медиан не определен")
    assert not_significant.startswith("Ни одно различие не значимо после поправки Холма")
    assert "окон в A - 2, в B - 2" in not_significant


def test_compare_texts_auto_window(chekhov):
    """Окно по самому короткому тексту: в нем 228 слов, и он делится на два окна по 114"""
    result = compare_texts([chekhov], [PUSHKIN * 12])
    assert result["window"] == auto_window(228) == 114
    assert result["n_windows"] == {"a": 2, "b": 2}


def test_compare_texts_whole(chekhov):
    result = compare_texts([chekhov, chekhov * 2], [PUSHKIN * 12, PUSHKIN * 20], whole_texts=True)
    assert result["window"] is None
    assert result["n_windows"] == result["n_texts"] == {"a": 2, "b": 2}


def test_compare_texts_paths(tmp_path, chekhov):
    paths = []
    for name, text in (("a.txt", chekhov), ("b.txt", PUSHKIN * 12)):
        paths.append(str(tmp_path / name))
        Path(paths[-1]).write_text(text, encoding="utf-8")
    expected = compare_texts([chekhov, chekhov], [PUSHKIN * 12, PUSHKIN * 12], window=100)
    assert (
        compare_texts(
            [chekhov], b_paths=[paths[1]], a_paths=[paths[0]], b=[PUSHKIN * 12], window=100
        )
        == expected
    )


def test_compare_texts_dropped(chekhov):
    result = compare_texts([chekhov, chekhov, "Короткий текст."], [PUSHKIN * 12] * 2, window=100)
    assert result["n_texts"] == {"a": 2, "b": 2}
    assert (
        "1 из 3 текстов корпуса A короче окна в 100 слов и не вошли в сравнение"
        in (result["warnings"])
    )
    whole = compare_texts([chekhov, chekhov, "..."], [chekhov, PUSHKIN * 12], whole_texts=True)
    assert "1 из 3 текстов корпуса A без слов и не вошли в сравнение" in whole["warnings"]


def test_compare_texts_text_lengths():
    """Тексты корпусов разной длины: признаки, зависящие от длины, различаются и из-за нее"""
    whole = compare_texts([CHEKHOV_LONG] * 2, [PUSHKIN] * 2, whole_texts=True)
    warning = next(item for item in whole["warnings"] if "Средняя длина" in item)
    assert warning.startswith("Средняя длина текста в A - ")
    assert warning.endswith("сравнивайте окнами (whole_texts=false)")
    windows = compare_texts([PUSHKIN * 7] * 3, [CHEKHOV_LONG] * 2, window=100)
    assert not any("Средняя длина" in item for item in windows["warnings"])


def test_compare_texts_one_window(chekhov):
    with pytest.raises(
        ToolError, match=r"^Окон в A - 1, в B - 1: .*передайте хотя бы по два текста"
    ):
        compare_texts([chekhov], [PUSHKIN * 6], whole_texts=True)


def test_compare_texts_no_words(chekhov):
    with pytest.raises(ToolError, match=r"^Корпус B: в текстах нет слов$"):
        compare_texts([chekhov], ["", "..."])


def test_compare_texts_empty(chekhov):
    with pytest.raises(
        ToolError, match=r"^Корпус A пуст: передайте тексты в a или пути к файлам в a_paths$"
    ):
        compare_texts(b=[chekhov])


def test_compare_texts_language(chekhov):
    """Язык проверяется у каждого корпуса: короткий английский корпус не теряется в склейке"""
    english = "The cat sleeps on the window and the dog barks at the cat. " * 20
    result = compare_texts([chekhov] * 2, [english] * 2, window=100)
    assert result["warnings"][0].startswith("Корпус B: Букв русского алфавита - только 0%")


def test_compare_texts_short():
    """Окно уже наименьшее: совет - сравнить тексты целиком, а не уменьшить окно"""
    with pytest.raises(
        ToolError, match=r"наименьшего окна в 100 слов: сравните тексты целиком \(whole_texts=true"
    ):
        compare_texts(["Короткий текст"], ["Другой текст"])


def test_compare_texts_window_too_large(chekhov):
    with pytest.raises(ToolError, match=r"окна в 1000 слов: задайте window поменьше"):
        compare_texts([chekhov] * 2, [PUSHKIN * 12] * 2, window=1000)


def test_compare_texts_limit(monkeypatch, chekhov):
    """Лимит длины действует на сумму длин текстов корпуса, без разделителей"""
    monkeypatch.setenv("RUTS_MCP_MAX_TEXT_LENGTH", str(2 * len(chekhov)))
    compare_texts([chekhov, chekhov], [PUSHKIN * 12] * 2, window=100)
    with pytest.raises(
        ToolError, match=rf"^Корпус B длиннее лимита сервера \(символов: {2 * len(chekhov) + 1},"
    ):
        compare_texts([chekhov, chekhov], [chekhov, chekhov + "."])


@pytest.fixture
def pronouns(data_dir):
    """Словарь со статьями, которые лемматизатор не дает: «его» и «во» приводятся к «он» и «в»"""
    rows = (
        ("в", "pr", 30000.0),
        ("во", "pr", 600.0),
        ("его", "apro", 2000.0),
        ("ее", "apro", 1500.0),
        ("она", "spro", 9000.0),
        ("род", "s", 300.0),
        ("родиться", "v", 200.0),
        ("кот", "s", 40.3),
        ("он", "spro", 15000.0),
        ("сон", "s", 100.0),
        ("черт", "s", 50.0),
        ("черта", "s", 60.0),
        ("видеть", "v", 800.0),
    )
    path = data_dir / "dicts"
    path.mkdir(parents=True)
    lines = ["Lemma\tPoS\tFreq(ipm)\tR\tD\tDoc"] + [
        f"{lemma}\t{pos}\t{ipm}\t90\t90\t1000" for lemma, pos, ipm in rows
    ]
    path.joinpath("freqrnc2011.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def test_keyness_unreachable_entries(pronouns):
    """«Его» в тексте - форма «он», поэтому статья «его» не бывает реже в тексте"""
    text = "Кот видел его во сне. Его кот спал."
    words = [item["word"] for item in keyness(text, positive=False, min_freq=1)["keywords"]]
    assert "его" not in words
    assert "во" not in words


def test_keyness_reachable_entries(pronouns):
    """Статья остается, если к ней приводится другая форма: «род» - «родиться», но «рода» - «род»"""
    words = [item["word"] for item in keyness("Кот спал.", positive=False, min_freq=1)["keywords"]]
    assert {"род", "черт", "черта", "она"} <= set(words)
    assert not {"его", "во", "ее"} & set(words)


def test_keyness_yo_pronoun(pronouns):
    """«Её» и «ее» - одно слово «она», как в тексте без ё"""
    with_yo = keyness("Её кот видел её.", min_freq=1)
    without_yo = keyness("Ее кот видел ее.", min_freq=1)
    assert with_yo["keywords"] == without_yo["keywords"]
    assert "она" in [item["word"] for item in with_yo["keywords"]]


def test_keyness_dictionary_yo(pronouns):
    """Слово с ё лемматизируется до замены ё: «чёрт» - «черт», а не «черта»"""
    words = [item["word"] for item in keyness("Чёрт, чёрт побери!", min_freq=1)["keywords"]]
    assert "черт" in words
    assert "черта" not in words


def test_keyness_damaged_dictionary(damaged_dict):
    with pytest.raises(
        ToolError, match=r"^Частотный словарь Ляшевской и Шарова поврежден: ключевые слова"
    ):
        keyness(CAT)


def test_keyness_no_cyrillic(dicts):
    with pytest.raises(
        ToolError, match=r"^Со словарем сравниваются только слова из кириллических"
    ):
        keyness("iPhone iPhone Wi-Fi 2020")


def test_keyness_rare_hint():
    """Совет уменьшить min_freq - только когда с min_freq=1 ключевые слова есть"""
    assert keyness(CAT, reference=CAT)["warnings"] == [
        "Слов, которые в тексте чаще, чем в эталоне, нет"
    ]


@pytest.mark.parametrize(
    ("text", "reference", "message"),
    [
        ("...", CAT, r"^В тексте нет слов$"),
        (CAT, "...", r"^В эталоне нет слов$"),
        (CAT, "", r"^Эталон не задан: передайте текст или путь к файлу$"),
    ],
    ids=["text", "reference", "empty-reference"],
)
def test_keyness_reference_errors(text, reference, message):
    with pytest.raises(ToolError, match=message):
        keyness(text, reference=reference)


def test_keyness_paths(tmp_path):
    text, reference = tmp_path / "text.txt", tmp_path / "reference.txt"
    text.write_text(REFERENCE, encoding="utf-8")
    reference.write_text(CAT, encoding="utf-8")
    result = keyness(path=str(text), reference_path=str(reference), min_freq=1)
    assert result == keyness(REFERENCE, reference=CAT, min_freq=1)


def test_keyness_log_ratio_note():
    measure = keyness(REFERENCE, reference=CAT, measure="log_ratio")["measure"]
    assert "при нулевой частоте в эталоне она заменяется на 0,5" in measure
