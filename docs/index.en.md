# ruTS-mcp

**ruTS-mcp** is an [MCP](https://modelcontextprotocol.io) server for [ruTS](https://sergeyshk.github.io/ruTS/en/), a library of statistics of Russian texts. It gives an LLM agent tools to measure a text instead of judging it by eye: readability, lexical diversity, morphology, syntax, verse, comparison of corpora - each value with the scale to read it by and the limits of its applicability.

## Features { #features }

| Tool | What it does |
| :--- | :----------- |
| [`analyze_text`](tools.md#analyze_text) | Statistics of a text by groups: basic, readability, lexical diversity, morphology, phonetics, cohesion, style and officialese, lexical sophistication, verse, syntax |
| [`kwic`](tools.md#kwic) | All occurrences of a word or a phrase with their context |
| [`collocations`](tools.md#collocations) | Set phrases and the collocates of a word |
| [`dispersion`](tools.md#dispersion) | How evenly words are spread over the text |
| [`keyness`](tools.md#keyness) | Keywords of a text against the Russian language or another text |
| [`compare_texts`](tools.md#compare_texts) | How two corpora of texts differ by style features |

Besides the tools, the server provides [resources](resources.md#resources) - readability scales, style norms, the state of the dictionaries - and [prompts](resources.md#prompts) for typical reviews: readability, officialese, a poem, an SEO check, a comparison of two texts.

## Example { #example }

Asked "what reader is this text written for?", the agent calls `analyze_text` with the `readability` group and gets not just the numbers but their reading and caveats (the server answers in Russian):

```json
{
  "readability": {
    "consensus_grade": {
      "value": 25.5,
      "interpretation": "аспирантура (старше 22 лет)",
      "description": "Сводный класс: медиана формул класса и индекса Флеша, переведенного в класс; число лет обучения, нужное для понимания текста"
    },
    "flesch_reading_easy": {
      "value": -39.95,
      "interpretation": "выпускник университета",
      "description": "Индекс Флеша: номинально от 0 до 100, чем выше, тем легче текст; прочтение по шкале Флеша"
    }
  },
  "warnings": [
    "Предложений в тексте: 1, меньше 30. Формулы удобочитаемости опираются на среднюю длину предложения, исходный SMOG - на выборку из 30 предложений: на коротком тексте значения неустойчивы, включая сводный класс, это грубая оценка"
  ]
}
```

This is a single sentence of bureaucratese: «В целях повышения качества обслуживания клиентов в кратчайшие сроки осуществляется проведение мероприятий по модернизации оборудования, предусмотренных утвержденным планом развития организации на текущий период.» The consensus grade reads as postgraduate level, and the warning says one sentence is too little for the formulas.

## Quick start { #quickstart }

Connecting to Claude Code and downloading the dictionaries and the spaCy model for the `lexical`, `verse` and `syntax` groups:

```bash
claude mcp add ruts -- uvx ruts-mcp
uvx ruts-mcp download
```

Connecting to Claude Desktop, Cursor and other clients and the server settings are on the [Installation](installation.md) page.
