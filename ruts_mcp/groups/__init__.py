from collections.abc import Callable
from typing import Literal

from ..analysis import Analysis, GroupResult
from .basic import basic_group
from .cohesion import cohesion_group
from .diversity import diversity_group
from .morph import morph_group
from .phon import phon_group
from .readability import readability_group
from .style import style_group

Group = Literal["basic", "readability", "diversity", "morph", "phon", "cohesion", "style"]

DEFAULT_GROUPS: tuple[Group, ...] = ("basic", "readability")
GROUPS: dict[Group, Callable[[Analysis], GroupResult]] = {
    "basic": basic_group,
    "readability": readability_group,
    "diversity": diversity_group,
    "morph": morph_group,
    "phon": phon_group,
    "cohesion": cohesion_group,
    "style": style_group,
}
