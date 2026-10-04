import argparse
from collections.abc import Sequence
from importlib.metadata import version

from . import __version__
from .server import mcp
from .settings import Settings


def main(argv: Sequence[str] | None = None) -> None:
    """
    Running the server over stdio

    Description:
        The settings are checked before the start, so a wrong environment
        variable stops the command with its message

    Arguments:
        argv (list[str]): Arguments of the command line; None - sys.argv
    """
    parser = argparse.ArgumentParser(
        prog="ruts-mcp",
        description="MCP server for ruTS: statistics of Russian texts as tools for LLM agents. "
        "Runs over stdio; the settings are the environment variables RUTS_MCP_*",
    )
    parser.add_argument(
        "--version", action="version", version=f"ruts-mcp {__version__}, ruts {version('ruts')}"
    )
    parser.parse_args(argv)
    try:
        Settings.from_env()
    except ValueError as error:
        parser.error(str(error))
    mcp.run(show_banner=False)
