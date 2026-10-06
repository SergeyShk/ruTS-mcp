import json
import shutil
import tempfile
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING

from .settings import Settings

if TYPE_CHECKING:
    from ruts.datasets import FreqDict, StressDict
    from spacy.language import Language

FREQ_DICT_TITLE = "Частотный словарь Ляшевской и Шарова"
STRESS_DICT_TITLE = "Словарь ударений Козиева"
SPACY_MODEL = "ru_core_news_sm"
SPACY_MODEL_TITLE = f"Модель spaCy {SPACY_MODEL}"
SPACY_MODEL_URL = (
    "https://github.com/explosion/spacy-models/releases/download/"
    "{name}-{version}/{name}-{version}-py3-none-any.whl"
)


def dicts_dir() -> Path:
    """Каталог словарей: подкаталог dicts каталога данных, как в ruTS"""
    return Settings.from_env().data_dir / "dicts"


def freq_dict() -> "FreqDict":
    """Частотный словарь ruTS из каталога словарей сервера"""
    from ruts.datasets import FreqDict

    return FreqDict(dicts_dir())


def stress_dict() -> "StressDict":
    """Словарь ударений ruTS из каталога словарей сервера"""
    from ruts.datasets import StressDict

    return StressDict(dicts_dir())


def missing_warning(title: str, consequence: str, missing: str = "не скачан") -> str:
    """
    Предупреждение о не скачанном словаре или модели

    Аргументы:
        title (str): Название словаря или модели
        consequence (str): Что не посчитано без них
        missing (str): Сказуемое в роде названия

    Вывод:
        str: Предупреждение с командой, которая скачивает словари

    Пример использования:
        >>> missing_warning("Словарь ударений Козиева", "группа verse не посчитана")[:63]
        'Словарь ударений Козиева не скачан: группа verse не посчитана. '
    """
    return (
        f"{title} {missing}: {consequence}. Словари и модель скачивает команда ruts-mcp "
        f"download (при запуске через uvx - uvx ruts-mcp download) в каталог "
        f"{Settings.from_env().data_dir}"
    )


class SpacyModel:
    """
    Модель spaCy ru_core_news_sm: установленный пакет или каталог, скачанный сервером

    Описание:
        Модели нет на PyPI, поэтому она не может быть зависимостью пакета.
        download скачивает wheel версии, совместимой с установленным spaCy
        (compatibility.json spaCy), распаковывает модель в каталог data_dir
        и удаляет модели других версий; установленный пакет ru_core_news_sm
        важнее скачанной модели, каталог с нечитаемым meta.json пропускается

    Аргументы:
        data_dir (Path): Каталог скачанных моделей

    Атрибуты:
        data_dir (Path): Каталог скачанных моделей
    """

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir

    @property
    def installed(self) -> bool:
        """Установлен ли пакет модели"""
        import spacy

        return spacy.util.is_package(SPACY_MODEL)

    @property
    def filepath(self) -> str | None:
        """
        Имя пакета или каталог скачанной модели, совместимой с установленным spaCy

        Вывод:
            str | None: То, что принимает spacy.load; None - модели нет
        """
        import spacy

        if self.installed:
            return SPACY_MODEL
        for path in sorted(self.data_dir.glob(f"{SPACY_MODEL}-*"), reverse=True):
            try:
                required = json.loads((path / "meta.json").read_text("utf-8"))["spacy_version"]
            except (OSError, ValueError, KeyError, TypeError):
                continue
            if spacy.util.is_compatible_version(spacy.about.__version__, required):
                return str(path)
        return None

    def download(self, force: bool = False) -> None:
        """
        Загрузка модели, совместимой с установленным spaCy

        Аргументы:
            force (bool): Загрузить модель, даже если она уже загружена

        Исключения:
            DownloadError: Если не удалось загрузить или распаковать файл или в нем нет модели
        """
        import spacy
        from anyts.datasets import download_file, extract_archive
        from ruts.constants import USER_AGENT
        from ruts.exceptions import DataFileError, DownloadError

        self.data_dir.mkdir(parents=True, exist_ok=True)
        compatibility = download_file(
            spacy.about.__compatibility__, self.data_dir, force=True, user_agent=USER_AGENT
        )
        minor = spacy.util.get_minor_version(spacy.about.__version__)
        try:
            table = json.loads(Path(compatibility).read_text("utf-8"))["spacy"]
            version = table[minor][SPACY_MODEL][0]
        except (KeyError, IndexError, ValueError) as error:
            raise DownloadError(f"Нет версии {SPACY_MODEL} для spaCy {minor}") from error
        finally:
            Path(compatibility).unlink()
        target = self.data_dir / f"{SPACY_MODEL}-{version}"
        if target.is_dir() and not force:
            return
        wheel = Path(
            download_file(
                SPACY_MODEL_URL.format(name=SPACY_MODEL, version=version),
                self.data_dir,
                force=True,
                user_agent=USER_AGENT,
            )
        )
        # Скрытый каталог не похож на модель: оборванная распаковка не находится в filepath
        staging = Path(tempfile.mkdtemp(prefix=f".{SPACY_MODEL}-", dir=self.data_dir))
        try:
            extract_archive(wheel, staging)
            source = staging / SPACY_MODEL / target.name
            if not (source / "meta.json").is_file():
                raise DownloadError(f"В архиве {wheel.name} нет модели {SPACY_MODEL}")
            shutil.rmtree(target, ignore_errors=True)
            source.rename(target)
        except (OSError, DataFileError) as error:
            raise DownloadError(f"Не удалось распаковать модель из {wheel.name}") from error
        finally:
            shutil.rmtree(staging, ignore_errors=True)
            wheel.unlink(missing_ok=True)
        for path in self.data_dir.glob(f"{SPACY_MODEL}-*"):
            if path != target:
                shutil.rmtree(path, ignore_errors=True)


def models_dir() -> Path:
    """Каталог моделей spaCy: подкаталог spacy каталога данных"""
    return Settings.from_env().data_dir / "spacy"


def spacy_model() -> "Language | None":
    """Модель spaCy из пакета или каталога сервера; None, если модели нет"""
    path = SpacyModel(models_dir()).filepath
    return None if path is None else load_spacy(path)


@lru_cache(maxsize=2)
def load_spacy(name: str) -> "Language":
    """Загрузка модели spaCy один раз на процесс"""
    import spacy

    # Синтаксису не нужны сущности и леммы spaCy, а без них разбор быстрее
    return spacy.load(name, exclude=["ner", "lemmatizer"])
