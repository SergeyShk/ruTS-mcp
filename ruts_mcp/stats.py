import re
from collections.abc import Callable
from typing import Any, Literal

Group = Literal["basic"]

PRECISION = 3
MIN_CYRILLIC_SHARE = 0.5
CYRILLIC = re.compile(r"[а-яё]", re.IGNORECASE)

# The thresholds of ruts.constants are written out to leave ruTS unimported until a call
BASIC_STATS = {
    "n_sents": "Sentences that contain words",
    "n_words": "Words",
    "n_unique_words": "Unique words, case ignored; share of all words",
    "n_long_words": "Long words, of 6 or more letters; share of all words",
    "n_complex_words": "Complex words, of 4 or more syllables; share of all words",
    "n_simple_words": "Simple words, of 1 to 3 syllables; share of all words",
    "n_monosyllable_words": "Words of one syllable; share of all words",
    "n_polysyllable_words": "Words of two or more syllables; share of all words",
    "n_chars": "Characters, line breaks excluded",
    "n_letters": "Letters; share of all characters",
    "n_spaces": "Spaces and tabs; share of all characters",
    "n_syllables": "Syllables",
    "n_punctuations": "Punctuation marks; share of all characters",
}
BASIC_DISTRIBUTIONS = {
    "c_letters": "Number of words by their number of letters",
    "c_syllables": "Number of words by their number of syllables",
    "c_punctuations": "Number of punctuation marks by type",
}


def basic_stats(text: str, distributions: bool = False) -> dict[str, Any]:
    """
    Basic statistics of a text with their descriptions

    Description:
        The counts of BasicStats of ruTS; a count of words or of characters
        comes with its share of all words or of all characters. The keys
        of the distributions are strings, as in JSON, and the types of
        punctuation marks absent from the text are left out

    Arguments:
        text (str): Text in Russian
        distributions (bool): Add the distributions of words by letters and
            by syllables and of punctuation marks by type

    Returns:
        dict[str, Any]: Name of a statistic of ruTS - its value, share and description

    Raises:
        SourceError: If the text has no words

    Example:
        >>> stats = basic_stats("Мама мыла раму.")
        >>> stats["n_words"]
        {'value': 3, 'description': 'Words'}
        >>> stats["n_long_words"]["share"]
        0.0
    """
    from ruts import BasicStats

    stats = BasicStats(text, normalize=True).get_stats()
    result: dict[str, Any] = {}
    for name, description in BASIC_STATS.items():
        item: dict[str, Any] = {"value": stats[name]}
        share = stats.get("p" + name[1:])
        if share is not None:
            item["share"] = round(share, PRECISION)
        result[name] = item | {"description": description}
    if distributions:
        for name, description in BASIC_DISTRIBUTIONS.items():
            counts = {str(key): count for key, count in stats[name].items() if count}
            result[name] = {"value": counts, "description": description}
    return result


GROUPS: dict[Group, Callable[[str, bool], dict[str, Any]]] = {"basic": basic_stats}


def language_warnings(text: str) -> list[str]:
    """
    Warnings about a text that is not in Russian

    Description:
        ruTS counts syllables and reads words by the rules of Russian, so its
        values for a text in another language are not meaningful. A text
        without letters gets no warning

    Arguments:
        text (str): Text passed to a tool

    Returns:
        list[str]: Warnings for the model; empty for a Russian text

    Example:
        >>> language_warnings("Мама мыла раму")
        []
        >>> language_warnings("Mama washed the frame")
        ['Only 0% of the letters are Cyrillic: ruTS measures Russian texts, its values for a text in another language are not meaningful']
    """
    letters = sum(char.isalpha() for char in text)
    if not letters:
        return []
    share = len(CYRILLIC.findall(text)) / letters
    if share >= MIN_CYRILLIC_SHARE:
        return []
    return [
        f"Only {share:.0%} of the letters are Cyrillic: ruTS measures Russian texts, "
        "its values for a text in another language are not meaningful"
    ]
