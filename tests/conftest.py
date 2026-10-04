from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def chekhov():
    """Начало рассказа Чехова «Толстый и тонкий»: 241 слово, 37 предложений"""
    return (Path(__file__).parent / "data" / "chekhov.txt").read_text(encoding="utf-8")
