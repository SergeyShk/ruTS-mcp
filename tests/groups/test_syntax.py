import pytest
import spacy
from ruts import BasicStats, SyntaxStats
from ruts.constants import SYNTAX_STATS_DESC
from ruts.exceptions import SourceError
from ruts.utils import iter_text_sents, set_sent_starts

from ruts_mcp.analysis import Analysis, clean
from ruts_mcp.data import load_spacy
from ruts_mcp.groups.syntax import (
    CHUNK_SIZE,
    SYNTAX_NOTES,
    SYNTAX_REASONS,
    parse,
    syntax_group,
    text_chunks,
)


def test_syntax_group(chekhov):
    stats, warnings = syntax_group(Analysis(chekhov))
    nlp = spacy.load("ru_core_news_sm")
    text = chekhov.strip()
    doc = set_sent_starts(nlp.make_doc(text), [start for start, _, _ in iter_text_sents(text)])
    assert set(SYNTAX_NOTES) | set(SYNTAX_REASONS) <= set(SYNTAX_STATS_DESC)
    assert {name: item["value"] for name, item in stats.items()} == {
        name: clean(value) for name, value in SyntaxStats(nlp(doc)).get_stats().items()
    }
    for name, item in stats.items():
        assert item["description"].startswith(SYNTAX_STATS_DESC[name])
    assert stats["tree_depth"]["description"].endswith("от вершины предложения до слова")
    assert stats["infinitive_clauses_per_sent"]["description"].endswith(
        "входит в клаузы, но не в придаточные"
    )
    description = stats["complex_nominals_per_clause"]["description"]
    assert "клаузы - без однородных сказуемых с общим подлежащим" in description
    assert warnings == []


def test_parse_sentences(chekhov):
    """Предложения разбора - предложения razdel, как у групп по строке, а не модели"""
    nlp = load_spacy("ru_core_news_sm")
    assert SyntaxStats(parse(nlp, chekhov)).n_sents == BasicStats(chekhov).n_sents == 37
    assert SyntaxStats(nlp(chekhov.strip())).n_sents != 37


def test_syntax_no_words(monkeypatch):
    """Текст без букв и цифр не разбирается моделью: слов в нем нет"""
    monkeypatch.setattr("ruts_mcp.groups.syntax.spacy_model", lambda: pytest.fail("разбор"))
    with pytest.raises(SourceError, match=r"^В источнике данных отсутствуют слова$"):
        syntax_group(Analysis("..." * 1000))


def test_parse_without_tensor(chekhov):
    """Тензоры кусков статистикам не нужны и не склеиваются"""
    text = "\n".join([chekhov] * (CHUNK_SIZE // len(chekhov) + 1))
    assert len(list(text_chunks(text))) == 2
    doc = parse(load_spacy("ru_core_news_sm"), text)
    assert doc.tensor.size == 0
    assert doc.text.split() == text.split()
    assert SyntaxStats(doc).n_sents == BasicStats(text).n_sents


def test_parse_edges():
    """Перевод строки в конце текста не меняет разбор последнего предложения без точки"""
    text = "Вчера мы гуляли в парке. Сегодня идет дождь, и мы сидим дома"
    stats, _ = syntax_group(Analysis(text))
    assert stats["noun_verb_ratio"]["value"] == 0.6667
    assert syntax_group(Analysis(f"\n{text}\n"))[0] == stats


def test_parse_blank_lines():
    """Пустая строка завершает предложение, как в статистиках ruTS по строке"""
    text = "Глава первая\n\nОн пришел домой поздно вечером. Жена уже спала"
    doc = parse(load_spacy("ru_core_news_sm"), text)
    assert [sent.text.strip() for sent in doc.sents] == [
        "Глава первая",
        "Он пришел домой поздно вечером.",
        "Жена уже спала",
    ]
    assert BasicStats(text).n_sents == 3


def test_syntax_model_cached():
    """Модель загружается один раз на процесс, без сущностей и лемм"""
    nlp = load_spacy("ru_core_news_sm")
    assert load_spacy("ru_core_news_sm") is nlp
    assert "ner" not in nlp.pipe_names
    assert "parser" in nlp.pipe_names


def test_syntax_undefined():
    """Неопределенные статистики сгруппированы по причине"""
    _, warnings = syntax_group(Analysis("Мама мыла раму."))
    assert warnings == [
        f"Не определены на этом тексте: {name} - {SYNTAX_REASONS[name]}"
        for name in (
            "mean_coordination_chain_len",
            "mean_participle_clause_len",
            "mean_converb_clause_len",
            "p_agentless_passive",
        )
    ] + [
        "Не определены на этом тексте: pos_edit_distance, syntax_similarity - схожесть "
        "считается по парам соседних предложений, а в тексте одно предложение"
    ]
    _, warnings = syntax_group(Analysis("Дождь."))
    assert warnings[0] == (
        "Не определены на этом тексте: mean_dependency_distance, std_dependency_distance, "
        "max_dependency_distance, p_adjacent_dependencies - в предложениях текста нет связей "
        "между словами"
    )


def test_syntax_without_model(monkeypatch, data_dir):
    monkeypatch.setattr(spacy.util, "is_package", lambda name: False)
    stats, warnings = syntax_group(Analysis("Мама мыла раму."))
    assert stats == {}
    (warning,) = warnings
    assert warning.startswith(
        "Модель spaCy ru_core_news_sm не скачана: группа syntax не посчитана. "
        "Словари и модель скачивает команда ruts-mcp download"
    )
    assert warning.endswith(f"в каталог {data_dir}")


def test_syntax_new_metric(monkeypatch):
    """Статистика новой версии ruTS без пояснения сервера отдается с описанием ruTS"""
    monkeypatch.setitem(SYNTAX_STATS_DESC, "n_ellipses", "Эллипсисов на предложение")
    monkeypatch.setattr(SyntaxStats, "n_ellipses", 0.5, raising=False)
    stats, _ = syntax_group(Analysis("Мама мыла раму."))
    assert stats["n_ellipses"] == {"value": 0.5, "description": "Эллипсисов на предложение"}


@pytest.mark.parametrize(
    ("text", "size", "expected"),
    [
        ("Кот спит.\nПес лает.\n", 12, [("Кот спит.\n", [0]), ("Пес лает.\n", [0])]),
        ("Кот спит.\nПес лает.\n", 100, [("Кот спит.\nПес лает.\n", [0, 10])]),
        ("Кот спит! Пес лает", 12, [("Кот спит! ", [0]), ("Пес лает", [0])]),
        ("  Кот спит.", 100, [("  Кот спит.", [2])]),
        (
            "Кот спит\nпес лает. Дождь.",
            12,
            [("Кот спит\n", [0]), ("пес лает. ", []), ("Дождь.", [0])],
        ),
        ("кот кот кот кот", 8, [("кот кот ", [0]), ("кот кот", [])]),
        # Начало предложения - в куске, где оно стоит, а не в куске из пробелов перед ним
        ("\n\nкот кот кот кот", 8, [("\n\n", []), ("кот кот ", [0]), ("кот кот", [])]),
        ("котопес", 3, [("кот", [0]), ("опе", []), ("с", [])]),
        ("", 10, [("", [])]),
    ],
)
def test_text_chunks(text, size, expected):
    """Куски собираются из предложений, длинное предложение режется по строке, пробелу или длине"""
    assert list(text_chunks(text, size)) == expected


def test_text_chunks_long(chekhov):
    text = (chekhov + "\n") * 40
    chunks = [chunk for chunk, _ in text_chunks(text)]
    assert "".join(chunks) == text
    assert len(chunks) == 4
    assert all(len(chunk) <= CHUNK_SIZE for chunk in chunks)
