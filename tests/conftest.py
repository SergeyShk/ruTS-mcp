from pathlib import Path

import pytest

PUSHKIN = """Мой дядя самых честных правил,
Когда не в шутку занемог,
Он уважать себя заставил
И лучше выдумать не мог."""
CAT = "Кот сидел на окне и смотрел на птиц"
# Лемма, часть речи, ipm, диапазон R, коэффициент D, число текстов - как в словаре Ляшевской и Шарова
FREQ_ROWS = (
    ("и", "conj", 35000.0, 100, 98, 30000),
    ("кот", "s", 40.3, 98, 90, 1500),
    ("на", "pr", 30000.0, 100, 98, 30000),
    ("окно", "s", 100.0, 90, 80, 3000),
    ("птица", "s", 50.0, 80, 70, 1200),
    ("сидеть", "v", 200.0, 100, 95, 6000),
    ("смотреть", "v", 300.0, 100, 96, 7000),
)
STRESS_ROWS = (
    ("выдумать", "в^ыдумать"),
    ("дядя", "д^ядя"),
    ("заставил", "заст^авил"),
    ("занемог", "занем^ог"),
    ("когда", "когд^а"),
    ("лучше", "л^учше"),
    ("правил", "пр^авил"),
    ("самых", "с^амых"),
    ("себя", "себ^я"),
    ("уважать", "уваж^ать"),
    ("честных", "ч^естных"),
    ("шутку", "ш^утку"),
)


@pytest.fixture(scope="session")
def chekhov():
    """Начало рассказа Чехова «Толстый и тонкий»: 241 слово, 37 предложений"""
    return (Path(__file__).parent / "data" / "chekhov.txt").read_text(encoding="utf-8")


@pytest.fixture(autouse=True)
def data_dir(tmp_path, monkeypatch):
    """Каталог данных теста вместо каталога пользователя: словарей в нем нет, пока их не запишут"""
    path = tmp_path / "data"
    monkeypatch.setenv("RUTS_DATA_DIR", str(path))
    return path


@pytest.fixture
def dicts(data_dir):
    """Маленькие частотный словарь и словарь ударений в каталоге данных теста"""
    path = data_dir / "dicts"
    path.mkdir(parents=True)
    freq = ["Lemma\tPoS\tFreq(ipm)\tR\tD\tDoc"] + ["\t".join(map(str, row)) for row in FREQ_ROWS]
    path.joinpath("freqrnc2011.csv").write_text("\n".join(freq) + "\n", encoding="utf-8")
    stress = ["\t".join(row) for row in sorted(STRESS_ROWS)]
    path.joinpath("all_accents.tsv").write_text("\n".join(stress) + "\n", encoding="utf-8")
    return path
