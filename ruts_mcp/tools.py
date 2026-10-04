from typing import Annotated, Any

from pydantic import Field

from .errors import check_text, ruts_errors
from .stats import GROUPS, Group, language_warnings


def analyze_text(
    text: Annotated[str, Field(description="Text in Russian")],
    groups: Annotated[
        tuple[Group, ...],
        Field(
            description="Groups of statistics to compute, each a key of the result", min_length=1
        ),
    ] = ("basic",),
    distributions: Annotated[
        bool,
        Field(
            description="Add the distributions of words by number of letters and of syllables "
            "and of punctuation marks by type (group basic)"
        ),
    ] = False,
) -> dict[str, Any]:
    """Measure a Russian text with the statistics of the ruTS library.

    Use it to get exact numbers about a text instead of estimating them by eye.

    Groups of statistics:
    - basic: sentences, words, syllables, characters, letters, spaces and punctuation marks; unique, long (6+ letters), complex (4+ syllables), simple, monosyllabic and polysyllabic words with their share of all words.

    The result has a key per requested group that maps a statistic to its "value", its "share" where it has one and a "description" of what it counts, and "warnings": the reasons the values may not be meaningful for this text, such as a text that is not in Russian. Read the warnings before drawing conclusions.
    """
    check_text(text)
    with ruts_errors():
        result = {group: GROUPS[group](text, distributions) for group in dict.fromkeys(groups)}
    return result | {"warnings": language_warnings(text)}
