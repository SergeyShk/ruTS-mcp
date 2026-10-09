import json

import pytest
import spacy
from ruts import ReadabilityStats
from ruts.constants import GRADE_AGE_LEVELS, POSTGRADUATE_LEVEL, STYLE_NORMS

from ruts_mcp.data import SPACY_MODEL
from ruts_mcp.resources import data_status, readability_scales, style_norms


def test_readability_scales():
    text = readability_scales()
    _, last, stage, age = GRADE_AGE_LEVELS[0]
    assert f"| до {last} | {stage} | {age} |" in text
    for first, last, stage, age in GRADE_AGE_LEVELS[1:]:
        assert f"| {first}-{last} | {stage} | {age} |" in text
    assert "округляется арифметически (6,5 - до 7)" in text
    assert f"| больше 17 | {' | '.join(POSTGRADUATE_LEVEL)} |" in text
    for scale in ReadabilityStats.level_scales.values():
        for _, label in scale:
            assert f" | {label} |" in text
    assert "| [90; ∞) | 5-й класс |" in text
    assert "| (-∞; 30) | выпускник университета |" in text
    assert "| [7,2; ∞) | 13 |" in text
    assert "| (-∞; 0,2) | 1 |" in text


def test_style_norms():
    """Полосы «больше X» читаются без включения X, как в таблице норм документации ruTS"""
    text = style_norms()
    for name, bands in STYLE_NORMS.items():
        assert f"## {name}: " in text
        for _, label in bands:
            assert f" | {label} |" in text
    assert "| (7; ∞) | выше нормы Advego |" in text
    assert "| (5; 7] | у верхней границы нормы Advego |" in text
    assert "| [5; 15] | норма Advego |" in text
    assert "| [30; 60] | SEO-оптимизированный текст по Text.ru |" in text
    assert "| [50; ∞) | норма pr-cy и megaindex |" in text


def test_data_status(data_dir):
    text = data_status()
    assert f"Каталог данных: {data_dir}" in text
    assert "| lexical, keyness | не скачан |" in text
    assert "| verse | не скачан |" in text
    assert f"| syntax | установлена пакетом {SPACY_MODEL} |" in text
    assert "`ruts-mcp download`" in text


def test_data_status_downloaded(dicts, data_dir, monkeypatch):
    monkeypatch.setattr(spacy.util, "is_package", lambda name: False)
    assert "| syntax | не скачана |" in data_status()
    model = data_dir / "spacy" / f"{SPACY_MODEL}-1.0.0"
    model.mkdir(parents=True)
    meta = {"spacy_version": f"=={spacy.about.__version__}"}
    (model / "meta.json").write_text(json.dumps(meta), encoding="utf-8")
    text = data_status()
    assert "| lexical, keyness | скачан |" in text
    assert "| verse | скачан |" in text
    assert "| syntax | скачана |" in text


def test_data_status_damaged(damaged_dict):
    assert "| lexical, keyness | поврежден, скачайте заново с --force |" in data_status()


@pytest.mark.parametrize("resource", [readability_scales, style_norms, data_status])
def test_markdown(resource):
    assert resource().startswith("# ")
    assert resource().endswith("\n")
