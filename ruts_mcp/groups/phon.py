from ..analysis import Analysis, GroupResult, stat, undefined_warnings

# Пояснения к описаниям ruTS там, где по названию метрику не прочитать
PHON_NOTES = {
    "p_vowels": "среди звуков, ь и ъ не звуки",
    "p_sonorants": "л, м, н, р, й среди звуков",
    "p_voiced": "б, в, г, д, ж, з среди звуков",
    "p_voiceless": "к, п, с, т, ф, х, ц, ч, ш, щ среди звуков",
    "p_heavy_clusters": "среди групп согласных внутри слова, включая одиночные согласные",
    "cv_entropy": "чем выше, тем разнообразнее фонетическая форма слов",
    "hardness": "глухие шумные согласные на гласные и сонорные; чем выше, тем жестче звучание",
    "alliteration": "окна из {window} слов с повтором согласной относительно случайного "
    "порядка слов: около 1 - как при случайном порядке, заметно больше 1 - аллитерация",
    "assonance": "то же для гласных: около 1 - как при случайном порядке, заметно больше 1 - "
    "ассонанс",
}


def phon_group(analysis: Analysis) -> GroupResult:
    """
    Фоностатистики текста

    Описание:
        Метрики PhonStats из ruTS по буквам, без ударения, оглушения и редукции;
        описание ruTS дополнено пояснением, если по названию метрику не прочитать.
        Метрики, не определенные на тексте (текст короче окна аллитерации, ни
        один звук не повторился в двух словах окна, нет гласных), отдаются как
        None и перечисляются в предупреждении

    Аргументы:
        analysis (Analysis): Текст и настройки

    Вывод:
        tuple[dict[str, Any], list[str]]: Имя метрики ruTS - ее значение и описание;
            предупреждения

    Исключения:
        SourceError: Если в тексте нет слов

    Пример использования:
        >>> stats, warnings = phon_group(Analysis("Мама мыла раму"))
        >>> stats["p_vowels"]
        {'value': 0.5, 'description': 'Доля гласных: среди звуков, ь и ъ не звуки'}
    """
    from ruts import PhonStats
    from ruts.constants import PHON_STATS_DESC

    ps = PhonStats(analysis.text)
    stats = {}
    for name, value in ps.get_stats().items():
        note = PHON_NOTES.get(name)
        description = PHON_STATS_DESC[name]
        if note:
            description = f"{description}: {note.format(window=ps.window_len)}"
        stats[name] = stat(value, description)
    warnings = undefined_warnings(
        stats,
        "текст короче окна аллитерации, ни один звук не повторился в двух словах окна "
        "или в тексте нет звуков, от которых считается метрика",
    )
    return stats, warnings
