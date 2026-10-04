from typing import get_args

from ruts_mcp.groups import DEFAULT_GROUPS, GROUPS, Group


def test_groups():
    assert list(GROUPS) == list(get_args(Group))
    assert DEFAULT_GROUPS == ("basic", "readability")
