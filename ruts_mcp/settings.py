from collections.abc import Mapping
from dataclasses import dataclass
from os import environ as os_environ
from typing import Self

ENV_PREFIX = "RUTS_MCP_"


@dataclass(frozen=True)
class Settings:
    """
    Settings of the server

    Description:
        A setting is read from the environment variable of its name in upper
        case with the prefix RUTS_MCP_ (RUTS_MCP_MAX_TEXT_LENGTH); a variable
        that is not set keeps the default

    Attributes:
        max_text_length (int): Maximum number of characters of a text a tool takes
    """

    max_text_length: int = 500_000

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> Self:
        """
        Reading the settings from the environment

        Arguments:
            environ (Mapping[str, str]): Environment variables; None - os.environ

        Returns:
            Settings: Settings of the server

        Raises:
            ValueError: If a variable is not a positive integer

        Example:
            >>> Settings.from_env({"RUTS_MCP_MAX_TEXT_LENGTH": "1000"})
            Settings(max_text_length=1000)
        """
        environ = os_environ if environ is None else environ
        return cls(
            max_text_length=_positive_int(environ, "MAX_TEXT_LENGTH", cls.max_text_length),
        )


def _positive_int(environ: Mapping[str, str], name: str, default: int) -> int:
    """The positive integer of a variable or the default when it is not set"""
    variable = ENV_PREFIX + name
    if variable not in environ:
        return default
    raw = environ[variable]
    try:
        value = int(raw)
    except ValueError:
        value = 0
    if value < 1:
        raise ValueError(f"{variable} must be a positive integer, got {raw!r}")
    return value
