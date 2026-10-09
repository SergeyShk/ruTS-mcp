import pytest
from fastmcp.exceptions import ToolError
from ruts import BasicStats, SourceError

from ruts_mcp.errors import ruts_errors


def test_ruts_errors():
    with pytest.raises(ToolError, match=r"^The data source has no words$") as info, ruts_errors():
        BasicStats("")
    assert isinstance(info.value.__cause__, SourceError)


def test_other_errors_pass():
    with pytest.raises(ZeroDivisionError), ruts_errors():
        _ = 1 / 0
