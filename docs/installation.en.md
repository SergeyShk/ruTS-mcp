# Installation

## Requirements { #requirements }

The server works over stdio: the client runs it as the `ruts-mcp` command. The easiest way is to run it with `uvx` from [uv](https://docs.astral.sh/uv/getting-started/installation/): `uvx` downloads the package and a suitable Python itself. Without uv, the server is installed into an environment with Python 3.11 or newer:

```bash
pip install ruts-mcp
```

Then the client configuration names `ruts-mcp` instead of `uvx ruts-mcp`.

## Connecting to a client { #clients }

### Claude Code { #claude-code }

```bash
claude mcp add ruts -- uvx ruts-mcp
```

This connects the server to the current project; add `--scope user` to make it available in all projects. The `/mcp` command in a Claude Code session shows whether it is connected.

### Claude Desktop { #claude-desktop }

Add the server to `claude_desktop_config.json` (Settings - Developer - Edit Config): on macOS it is in `~/Library/Application Support/Claude/`, on Windows in `%APPDATA%\Claude\`.

```json
{
  "mcpServers": {
    "ruts": {
      "command": "uvx",
      "args": ["ruts-mcp"]
    }
  }
}
```

Restart Claude Desktop after the change. If the server fails to start with an error about the `uvx` command, give the full path to it, which `which uvx` prints (`where uvx` on Windows).

### Cursor { #cursor }

Add the same `mcpServers` entry to `~/.cursor/mcp.json` to make the server available in all projects, or to `.cursor/mcp.json` of a project.

### Other clients { #other-clients }

Any MCP client that runs servers over stdio connects ruTS-mcp with the `uvx ruts-mcp` command.

## Dictionaries and the spaCy model { #data }

Most groups and tools work right away. Three groups and one tool need data that the package does not contain:

| Data | Used by | Download | On disk |
| :--- | :------ | :------: | :-----: |
| Frequency dictionary of Lyashevskaya and Sharoff | the `lexical` group, `keyness` against the dictionary | 0.5 MB | 2 MB |
| Stress dictionary of Koziev | the `verse` group | 11 MB | 84 MB |
| spaCy model `ru_core_news_sm` | the `syntax` group | 15 MB | 44 MB |

One command downloads all of them:

```bash
uvx ruts-mcp download
```

A repeated run skips what is already downloaded, `--force` downloads it again. Without the data a group does not fail: the metrics that need it are not computed, and a warning in the result names this command. Without the dictionary the `lexical` group still computes the shares of frequency bands and lexical density. The [`ruts://data`](resources.md#resources) resource shows what is downloaded.

The data is kept in the user data directory and survives server updates:

| System | Directory |
| :----- | :-------- |
| macOS | `~/Library/Application Support/ruts-mcp` |
| Linux | `~/.local/share/ruts-mcp` |
| Windows | `%LOCALAPPDATA%\ruts-mcp` |

The `RUTS_DATA_DIR` variable sets another directory by an absolute path, for example the one where the ruTS library has already downloaded its dictionaries. If the `ru_core_news_sm` package is installed in the server environment, the model is taken from it.

## Settings { #settings }

Settings are environment variables:

| Variable | Default | Description |
| :------- | :-----: | :---------- |
| `RUTS_MCP_MAX_TEXT_LENGTH` | `500000` | Greatest number of characters of a text or a corpus that a tool accepts |
| `RUTS_DATA_DIR` | user data directory | Directory of the dictionaries and the spaCy model, an absolute path |

In Claude Code a variable is passed with `-e`:

```bash
claude mcp add ruts -e RUTS_MCP_MAX_TEXT_LENGTH=1000000 -- uvx ruts-mcp
```

In Claude Desktop and Cursor - with the `env` field of the server entry:

```json
{
  "mcpServers": {
    "ruts": {
      "command": "uvx",
      "args": ["ruts-mcp"],
      "env": {"RUTS_MCP_MAX_TEXT_LENGTH": "1000000"}
    }
  }
}
```

`uvx ruts-mcp --version` prints the versions of the server and ruTS.
