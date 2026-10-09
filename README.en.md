<p align="center">
  <img src="https://raw.githubusercontent.com/SergeyShk/ruTS-mcp/master/docs/img/ruts-mcp.png" alt="ruTS-mcp" width="480">
</p>

<h1 align="center">ruTS-mcp</h1>

<p align="center">
  <b>MCP server for <a href="https://github.com/SergeyShk/ruTS">ruTS</a></b> - statistics of Russian texts as tools for LLM agents
</p>

<p align="center">
  <a href="https://sergeyshk.github.io/ruTS-mcp/en/">Documentation</a> ·
  <a href="https://pypi.org/project/ruts-mcp/">PyPI</a> ·
  <a href="https://github.com/SergeyShk/ruTS-mcp/blob/master/README.md">Русский</a>
</p>

<p align="center">
  <a href="https://pypi.org/project/ruts-mcp/"><img src="https://img.shields.io/pypi/v/ruts-mcp?logo=pypi&logoColor=FFE873" alt="Version"></a>
  <a href="https://pypi.org/project/ruts-mcp/"><img src="https://img.shields.io/pypi/pyversions/ruts-mcp.svg?logo=python&logoColor=FFE873" alt="Supported Python versions"></a>
  <a href="https://github.com/SergeyShk/ruTS-mcp/actions/workflows/ci.yml"><img src="https://github.com/SergeyShk/ruTS-mcp/actions/workflows/ci.yml/badge.svg" alt="Build"></a>
  <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="Ruff"></a>
  <a href="https://github.com/SergeyShk/ruTS-mcp/blob/master/LICENSE.txt"><img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License"></a>
</p>

---

**ruTS-mcp** gives an LLM agent the tools of the [ruTS](https://github.com/SergeyShk/ruTS) library to measure a Russian text instead of judging it by eye. Every value comes with a description, a reading by a scale where there is one, and warnings when the value is unstable or meaningless for the text. The server answers in Russian.

* **[`analyze_text`](https://sergeyshk.github.io/ruTS-mcp/en/tools/#analyze_text)** - statistics of a text by groups: basic, readability with the grade and age of the reader, lexical diversity, morphology, phonetics, cohesion, style and officialese, lexical sophistication, verse, syntax
* **[`kwic`](https://sergeyshk.github.io/ruTS-mcp/en/tools/#kwic)** - occurrences of a word or a phrase with their context
* **[`collocations`](https://sergeyshk.github.io/ruTS-mcp/en/tools/#collocations)** - set phrases and the collocates of a word
* **[`dispersion`](https://sergeyshk.github.io/ruTS-mcp/en/tools/#dispersion)** - how evenly words are spread over the text
* **[`keyness`](https://sergeyshk.github.io/ruTS-mcp/en/tools/#keyness)** - keywords against the Russian language or another text
* **[`compare_texts`](https://sergeyshk.github.io/ruTS-mcp/en/tools/#compare_texts)** - how two corpora of texts differ by style features
* **[Resources and prompts](https://sergeyshk.github.io/ruTS-mcp/en/resources/)** - readability scales and style norms, ready reviews: readability, officialese, a poem, an SEO check, a comparison of two texts

## Installation

The server runs with `uvx` from [uv](https://docs.astral.sh/uv/getting-started/installation/), which downloads the package and Python itself. Connecting to Claude Code:

```bash
claude mcp add ruts -- uvx ruts-mcp
```

The `lexical`, `verse` and `syntax` groups need dictionaries and a spaCy model; one command downloads them:

```bash
uvx ruts-mcp download
```

Connecting to Claude Desktop, Cursor and other clients and the settings are in the [documentation](https://sergeyshk.github.io/ruTS-mcp/en/installation/).

## License

[MIT](https://github.com/SergeyShk/ruTS-mcp/blob/master/LICENSE.txt). The dictionaries that `ruts-mcp download` fetches are distributed on the terms of their authors: the [frequency dictionary](http://dict.ruslang.ru/freq.php) of Lyashevskaya and Sharoff, the [stress dictionary](https://github.com/Koziev/NLP_Datasets) of Koziev (CC0), the [spaCy model](https://github.com/explosion/spacy-models) (MIT).
