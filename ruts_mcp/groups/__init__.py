from collections.abc import Callable
from typing import Literal

from ..analysis import Analysis, GroupResult
from .basic import basic_group
from .diversity import diversity_group
from .readability import readability_group

Group = Literal["basic", "readability", "diversity"]

DEFAULT_GROUPS: tuple[Group, ...] = ("basic", "readability")
GROUPS: dict[Group, Callable[[Analysis], GroupResult]] = {
    "basic": basic_group,
    "readability": readability_group,
    "diversity": diversity_group,
}
