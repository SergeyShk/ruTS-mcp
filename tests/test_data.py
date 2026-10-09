import json
import re
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import anyts.datasets
import pytest
import spacy
from ruts.exceptions import DownloadError

from ruts_mcp.data import (
    SPACY_MODEL,
    SpacyModel,
    _load_spacy,
    load_spacy,
    models_dir,
    spacy_model,
)

VERSION = "9.9.9"
PREFIX = f"{SPACY_MODEL}/{SPACY_MODEL}-{VERSION}/"


@pytest.fixture
def not_installed(monkeypatch):
    """Пакета модели нет: модель ищется только в каталоге данных"""
    monkeypatch.setattr(spacy.util, "is_package", lambda name: False)
    _load_spacy.cache_clear()
    yield
    _load_spacy.cache_clear()


@pytest.fixture
def blank(tmp_path):
    """Файлы пустой русской модели spaCy, совместимой с установленным spaCy"""
    path = tmp_path / "blank"
    spacy.blank("ru").to_disk(path)
    return {
        file.relative_to(path).as_posix(): file.read_bytes()
        for file in path.rglob("*")
        if file.is_file()
    }


@pytest.fixture
def network(monkeypatch, blank):
    """download_file без сети; в wheel, как в настоящем, два корня: модель и .dist-info"""
    calls = []
    state = {
        "compatibility": {
            "spacy": {
                spacy.util.get_minor_version(spacy.about.__version__): {SPACY_MODEL: [VERSION]}
            }
        },
        "members": {PREFIX: b"", f"{SPACY_MODEL}-{VERSION}.dist-info/METADATA": b""}
        | {PREFIX + name: data for name, data in blank.items()},
    }

    def download_file(url, dirpath, filename=None, force=False, user_agent=""):
        calls.append(url)
        path = Path(dirpath) / url.rsplit("/", 1)[-1]
        if url.endswith(".json"):
            path.write_text(json.dumps(state["compatibility"]), encoding="utf-8")
        else:
            with zipfile.ZipFile(path, "w") as archive:
                for name, data in state["members"].items():
                    archive.writestr(name, data)
        return str(path)

    monkeypatch.setattr(anyts.datasets, "download_file", download_file)
    return calls, state


def test_installed_package():
    model = SpacyModel(models_dir())
    assert model.installed
    assert model.filepath == SPACY_MODEL


def test_download(not_installed, network, data_dir):
    calls, _ = network
    model = SpacyModel(models_dir())
    assert model.filepath is None
    model.download()
    target = data_dir / "spacy" / f"{SPACY_MODEL}-{VERSION}"
    assert model.filepath == str(target)
    assert sorted(path.name for path in target.parent.iterdir()) == [target.name]
    assert len(calls) == 2
    model.download()
    assert len(calls) == 3
    model.download(force=True)
    assert len(calls) == 5
    nlp = spacy_model()
    assert nlp is not None
    assert spacy_model() is nlp


def test_incompatible_model(not_installed, data_dir):
    target = data_dir / "spacy" / f"{SPACY_MODEL}-2.0.0"
    target.mkdir(parents=True)
    (target / "meta.json").write_text(json.dumps({"spacy_version": ">=2.0.0,<2.1.0"}))
    assert SpacyModel(models_dir()).filepath is None
    assert spacy_model() is None


def test_download_unknown_spacy(not_installed, network):
    _, state = network
    state["compatibility"] = {"spacy": {}}
    with pytest.raises(DownloadError, match=rf"^Нет версии {SPACY_MODEL} для spaCy "):
        SpacyModel(models_dir()).download()


def test_download_without_model(not_installed, network):
    _, state = network
    state["members"] = {"other/file.txt": b""}
    with pytest.raises(DownloadError, match=r"нет модели ru_core_news_sm$"):
        SpacyModel(models_dir()).download()
    assert list(models_dir().iterdir()) == []


@pytest.mark.parametrize("name", [PREFIX + "../../escape.txt", "/escape.txt"])
def test_download_outside(not_installed, network, data_dir, name):
    """Файл архива с путем за каталог отвергается, ничего не распаковывается"""
    _, state = network
    state["members"][name] = b""
    with pytest.raises(DownloadError, match=r"^Не удалось распаковать модель из "):
        SpacyModel(models_dir()).download()
    assert list(models_dir().iterdir()) == []
    assert not list(data_dir.parent.rglob("escape.txt"))


def test_download_interrupted(not_installed, network, monkeypatch):
    """Оборванная распаковка не оставляет каталогов, которые filepath принял бы за модель"""

    def extract_archive(archive, directory):
        model = Path(directory) / SPACY_MODEL / f"{SPACY_MODEL}-{VERSION}"
        model.mkdir(parents=True)
        (model / "meta.json").write_text(json.dumps({"spacy_version": ">=0"}))
        raise OSError(28, "No space left on device")

    monkeypatch.setattr(anyts.datasets, "extract_archive", extract_archive)
    model = SpacyModel(models_dir())
    with pytest.raises(DownloadError, match=r"^Не удалось распаковать модель из "):
        model.download()
    assert list(models_dir().iterdir()) == []
    assert model.filepath is None


def test_broken_meta(not_installed, network):
    """Каталог с нечитаемым meta.json пропускается и не мешает скачать модель заново"""
    broken = models_dir() / f"{SPACY_MODEL}-{VERSION}"
    broken.mkdir(parents=True)
    (broken / "meta.json").write_text("{")
    model = SpacyModel(models_dir())
    assert model.filepath is None
    model.download()
    assert model.filepath == str(broken)


def test_download_removes_other_versions(not_installed, network):
    old = models_dir() / f"{SPACY_MODEL}-1.0.0"
    old.mkdir(parents=True)
    SpacyModel(models_dir()).download()
    assert [path.name for path in models_dir().iterdir()] == [f"{SPACY_MODEL}-{VERSION}"]


def test_load_spacy_concurrent(monkeypatch):
    """Одновременные первые вызовы загружают модель один раз"""
    _load_spacy.cache_clear()
    loads = []

    def load(name, exclude):
        loads.append(name)
        time.sleep(0.05)
        return name

    monkeypatch.setattr(spacy, "load", load)
    with ThreadPoolExecutor(8) as pool:
        results = list(pool.map(load_spacy, ["model"] * 8))
    _load_spacy.cache_clear()
    assert results == ["model"] * 8
    assert loads == ["model"]


def test_download_unwritable(not_installed, tmp_path):
    """Каталог данных не создается: ошибка загрузки с причиной, а не трейсбек"""
    blocker = tmp_path / "file"
    blocker.write_text("", encoding="utf-8")
    target = blocker / "spacy"
    with pytest.raises(
        DownloadError, match=rf"^Не удалось создать каталог {re.escape(str(target))} - "
    ):
        SpacyModel(target).download()
