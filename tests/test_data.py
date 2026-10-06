import json
import zipfile
from pathlib import Path

import anyts.datasets
import pytest
import spacy
from ruts.exceptions import DownloadError

from ruts_mcp.data import SPACY_MODEL, SpacyModel, load_spacy, models_dir, spacy_model

VERSION = "9.9.9"
PREFIX = f"{SPACY_MODEL}/{SPACY_MODEL}-{VERSION}/"


@pytest.fixture
def not_installed(monkeypatch):
    """Пакета модели нет: модель ищется только в каталоге данных"""
    monkeypatch.setattr(spacy.util, "is_package", lambda name: False)
    load_spacy.cache_clear()
    yield
    load_spacy.cache_clear()


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
    """download_file без сети: compatibility.json spaCy и wheel модели из файлов blank"""
    calls = []
    state = {
        "compatibility": {
            "spacy": {
                spacy.util.get_minor_version(spacy.about.__version__): {SPACY_MODEL: [VERSION]}
            }
        },
        "members": {PREFIX: b""} | {PREFIX + name: data for name, data in blank.items()},
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


def test_download_outside(not_installed, network):
    """Файл архива с .. в пути не выходит за каталог модели"""
    _, state = network
    state["members"][PREFIX + "../escape.txt"] = b""
    with pytest.raises(DownloadError, match=r"ведет за каталог модели$"):
        SpacyModel(models_dir()).download()
    assert not (models_dir() / "escape.txt").exists()
