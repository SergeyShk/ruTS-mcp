import math
from dataclasses import dataclass
from functools import cached_property
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from ruts import BasicStats

Preset = Literal["plainrussian", "fiction", "academic"]
GroupResult = tuple[dict[str, Any], list[str]]

SIGNIFICANT_DIGITS = 4
# Группы lexical и verse не считают числа словами, остальные считают
NO_WORDS_WARNING = "Группа {group} не посчитана: в тексте нет слов, а числа словами не считаются"


@dataclass(frozen=True)
class Options:
    """
    Настройки групп статистик

    Атрибуты:
        distributions (bool): Добавить распределения в группу basic
        preset (str): Пресет коэффициентов формул удобочитаемости ruTS
    """

    distributions: bool = False
    preset: Preset = "plainrussian"


class Analysis:
    """
    Текст с настройками и объектами ruTS, общими для групп статистик

    Описание:
        Базовые статистики нужны группам basic и readability, поэтому они
        считаются один раз за вызов инструмента, при первом обращении

    Аргументы:
        text (str): Текст на русском языке
        options (Options): Настройки групп; None - по умолчанию

    Атрибуты:
        text (str): Текст на русском языке
        options (Options): Настройки групп
    """

    def __init__(self, text: str, options: Options | None = None) -> None:
        self.text = text
        self.options = Options() if options is None else options

    @cached_property
    def basic(self) -> "BasicStats":
        """Базовые статистики текста с нормированными долями"""
        from ruts import BasicStats

        return BasicStats(self.text, normalize=True)


def clean(value: Any) -> Any:
    """
    Значение статистики, готовое для JSON

    Описание:
        Дробное число округляется до четырех значащих цифр; nan и бесконечность,
        которых нет в JSON, становятся None. Остальные значения не меняются

    Аргументы:
        value (Any): Значение статистики ruTS

    Вывод:
        Any: Значение для ответа инструмента

    Пример использования:
        >>> clean(0.0061549), clean(1771.13), clean(float("nan")), clean(7)
        (0.006155, 1771.0, None, 7)
    """
    if isinstance(value, float):
        if not math.isfinite(value):
            return None
        return float(f"{value:.{SIGNIFICANT_DIGITS}g}")
    return value


def plural(number: int, forms: tuple[str, str, str]) -> str:
    """
    Число с существительным, согласованным с ним

    Аргументы:
        number (int): Неотрицательное целое число
        forms (tuple[str, str, str]): Формы существительного при 1, 2 и 5

    Вывод:
        str: Число и существительное через пробел

    Пример использования:
        >>> [plural(number, ("слово", "слова", "слов")) for number in (1, 3, 11, 61, 112, 114)]
        ['1 слово', '3 слова', '11 слов', '61 слово', '112 слов', '114 слов']
    """
    if number % 10 == 1 and number % 100 != 11:
        form = forms[0]
    elif 2 <= number % 10 <= 4 and not 12 <= number % 100 <= 14:
        form = forms[1]
    else:
        form = forms[2]
    return f"{number} {form}"


def stat(
    value: Any,
    description: str,
    share: float | None = None,
    interpretation: str | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Статистика в ответе инструмента

    Аргументы:
        value (Any): Значение статистики
        description (str): Что считает статистика
        share (float): Доля от всех слов или символов; None - без доли
        interpretation (str): Прочтение значения по шкале; None - без шкалы
        details (dict[str, Any]): Другие ключи статистики перед описанием

    Вывод:
        dict[str, Any]: Значение, доля, прочтение, другие ключи и описание

    Пример использования:
        >>> stat(0.85714, "Доля", interpretation="высокая")
        {'value': 0.8571, 'interpretation': 'высокая', 'description': 'Доля'}
    """
    item: dict[str, Any] = {"value": clean(value)}
    if share is not None:
        item["share"] = clean(share)
    if interpretation is not None:
        item["interpretation"] = interpretation
    item |= details or {}
    item["description"] = description
    return item


def undefined_warnings(stats: dict[str, dict[str, Any]], reason: str) -> list[str]:
    """
    Предупреждение о статистиках, не определенных на тексте

    Аргументы:
        stats (dict[str, dict[str, Any]]): Статистики группы
        reason (str): Почему значения не определены

    Вывод:
        list[str]: Предупреждение со списком статистик со значением None или пустой список

    Пример использования:
        >>> undefined_warnings({"hdd": {"value": None}, "ttr": {"value": 1.0}}, "текст короткий")
        ['Не определены на этом тексте: hdd - текст короткий']
    """
    names = [name for name, item in stats.items() if item["value"] is None]
    if not names:
        return []
    return [f"Не определены на этом тексте: {', '.join(names)} - {reason}"]
