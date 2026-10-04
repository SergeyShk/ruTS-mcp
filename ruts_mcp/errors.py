from collections.abc import Iterator
from contextlib import contextmanager

from fastmcp.exceptions import ToolError

from .settings import Settings


def check_text(text: str) -> None:
    """
    Checking that a text fits the limit of the server

    Arguments:
        text (str): Text passed to a tool

    Raises:
        ToolError: If the text is longer than Settings.max_text_length
    """
    limit = Settings.from_env().max_text_length
    if len(text) > limit:
        raise ToolError(
            f"The text has {len(text):,} characters, more than the limit of {limit:,}: "
            "pass a shorter text or a part of it (the limit is set by RUTS_MCP_MAX_TEXT_LENGTH)"
        )


@contextmanager
def ruts_errors() -> Iterator[None]:
    """
    Turning the exceptions of ruTS into errors of a tool

    Description:
        The message of RutsError and its subclasses says what is wrong with
        the input, so the model gets it as the error of the tool, not as
        a failure of the server. ruTS is imported on entry

    Raises:
        ToolError: If ruTS raises RutsError
    """
    from ruts import RutsError

    try:
        yield
    except RutsError as error:
        raise ToolError(str(error)) from error
