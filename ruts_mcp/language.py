import re

MIN_RUSSIAN_SHARE = 0.5
MAX_FOREIGN_CYRILLIC_SHARE = 0.03
RUSSIAN = re.compile(r"[а-яё]", re.IGNORECASE)
FOREIGN_CYRILLIC = re.compile(r"(?![а-яё])[\u0400-\u052f]", re.IGNORECASE)
NO_LETTERS = (
    "В тексте нет букв: ruTS считает статистики по словам, и для текста из чисел и знаков "
    "их значения не имеют смысла"
)


def language_warnings(text: str) -> list[str]:
    """
    Предупреждения о тексте не на русском языке

    Описание:
        ruTS считает слоги и слова по правилам русского языка, поэтому для
        текста на другом языке и текста без букв ее значения не имеют смысла.
        Предупреждение дают текст без букв, меньше половины букв
        русского алфавита и от 3 % букв кириллицы не из него (і, ї, ў, ј, қ),
        как в украинском, белорусском, сербском или казахском тексте; доля
        в сообщении округляется вниз. Буквы считаются без знаков ударения
        (strip_marks): ѐ, ѝ и «чтó» - русские

    Аргументы:
        text (str): Текст, переданный инструменту

    Вывод:
        list[str]: Предупреждения для модели; для русского текста - пустой список

    Пример использования:
        >>> language_warnings("Мама мыла раму")
        []
        >>> language_warnings("Mama washed the frame")
        ['Букв русского алфавита - только 0%: ruTS считает статистики по правилам русского языка, для текста на другом языке значения не имеют смысла']
        >>> language_warnings("Він прийшов додому")
        ['Букв кириллицы не из русского алфавита - 6% (і): текст, похоже, не на русском языке, а ruTS считает слоги и слова по правилам русского, так что значения могут быть неверны']
    """
    from ruts.utils import strip_marks

    text = strip_marks(text)
    letters = sum(char.isalpha() for char in text)
    if not letters:
        return [NO_LETTERS]
    warnings = []
    russian = len(RUSSIAN.findall(text))
    if russian / letters < MIN_RUSSIAN_SHARE:
        warnings.append(
            f"Букв русского алфавита - только {_percent(russian, letters)}: ruTS считает статистики "
            "по правилам русского языка, для текста на другом языке значения не имеют смысла"
        )
    foreign = FOREIGN_CYRILLIC.findall(text)
    if len(foreign) / letters >= MAX_FOREIGN_CYRILLIC_SHARE:
        examples = ", ".join(sorted({char.lower() for char in foreign}))
        warnings.append(
            f"Букв кириллицы не из русского алфавита - {_percent(len(foreign), letters)} "
            f"({examples}): текст, похоже, не на русском языке, а ruTS считает слоги "
            "и слова по правилам русского, так что значения могут быть неверны"
        )
    return warnings


def _percent(count: int, total: int) -> str:
    """Доля в процентах с округлением вниз, чтобы 49,9 % не выглядели как пороговые 50 %; в целых числах, без погрешности float"""
    return f"{100 * count // total}%"
