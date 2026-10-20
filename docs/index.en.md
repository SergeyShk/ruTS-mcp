# ruTS-mcp

![ruTS-mcp](img/ruts-mcp.svg)

**ruTS-mcp** is an [MCP](https://modelcontextprotocol.io) server for [ruTS](https://sergeyshk.github.io/ruTS/en/), a library of statistics of Russian texts. It gives an LLM agent tools to measure a text instead of judging it by eye: readability, lexical diversity, morphology, syntax, verse, comparison of corpora - each value with the scale to read it by and the limits of its applicability.

## Features { #features }

<div class="grid cards" markdown>

-   :material-chart-box-outline:{ .lg .middle } __Text statistics__

    ---

    Ten groups of ruTS statistics: basic, readability with the school grade and reader age, lexical diversity, morphology, phonetics, cohesion, style and officialese, lexical sophistication, verse, syntax

    [:octicons-arrow-right-24: `analyze_text`](tools/analyze_text.md)

-   :material-text-search:{ .lg .middle } __Concordance__

    ---

    All occurrences of a word or a phrase with their context, by word form or by lemma

    [:octicons-arrow-right-24: `kwic`](tools/kwic.md)

-   :material-link-variant:{ .lg .middle } __Collocations__

    ---

    Set phrases and the collocates of a word by eight association measures

    [:octicons-arrow-right-24: `collocations`](tools/collocations.md)

-   :material-chart-scatter-plot:{ .lg .middle } __Word dispersion__

    ---

    How evenly words are spread over the text: the measures of Gries and others

    [:octicons-arrow-right-24: `dispersion`](tools/dispersion.md)

-   :material-key-variant:{ .lg .middle } __Keywords__

    ---

    Words that are more frequent in the text than in the Russian language or in another text

    [:octicons-arrow-right-24: `keyness`](tools/keyness.md)

-   :material-compare-horizontal:{ .lg .middle } __Corpus comparison__

    ---

    How two corpora of texts differ by style features: authorship attribution, genres, human and model texts

    [:octicons-arrow-right-24: `compare_texts`](tools/compare_texts.md)

-   :material-ruler:{ .lg .middle } __Resources__

    ---

    Readability scales, style norms and the state of the dictionaries and the spaCy model

    [:octicons-arrow-right-24: Resources](resources.md#resources)

-   :material-message-text-outline:{ .lg .middle } __Prompts__

    ---

    Typical reviews: readability, officialese, a poem, an SEO check, a comparison of two texts

    [:octicons-arrow-right-24: Prompts](resources.md#prompts)

</div>

## Example { #example }

Asked "what reader is this text written for?", the agent calls `analyze_text` with the `readability` group and gets not just the numbers but their reading and caveats (the server answers in Russian). The text is a single sentence of bureaucratese:

=== "Call"

    ``` json
    {
      "name": "analyze_text",
      "arguments": {
        "text": "В целях повышения качества обслуживания клиентов в кратчайшие сроки осуществляется проведение мероприятий по модернизации оборудования, предусмотренных утвержденным планом развития организации на текущий период.",
        "groups": ["readability"],
        "descriptions": false
      }
    }
    ```

=== "Result"

    ``` json
    {
      "readability": {
        "consensus_grade": {"value": 25.5, "interpretation": "аспирантура (старше 22 лет)"},
        "flesch_kincaid_grade": {"value": 28.06, "interpretation": "аспирантура (старше 22 лет)"},
        "flesch_reading_easy": {"value": -39.95, "interpretation": "выпускник университета"},
        "coleman_liau_index": {"value": 22.87, "interpretation": "аспирантура (старше 22 лет)"},
        "smog_index": {"value": 26.57, "interpretation": "аспирантура (старше 22 лет)"},
        "automated_readability_index": {"value": 26.31, "interpretation": "аспирантура (старше 22 лет)"},
        "lix": {"value": 88.22, "interpretation": "очень сложные тексты, законы и канцелярский язык"},
        "rix": {"value": 15.0, "interpretation": "университет и выше"},
        "sis_grade": {"value": 15.3, "interpretation": "4-6-й курс вуза (20-22 года)"},
        "matskovsky_index": {"value": 20.73},
        "dale_chall_index": {"value": 27.88, "interpretation": "аспирантура (старше 22 лет)"},
        "gunning_fog_index": {"value": 24.85, "interpretation": "аспирантура (старше 22 лет)"},
        "reading_time": {"value": 0.1278}
      },
      "warnings": [
        "Предложений в тексте: 1, меньше 30. Формулы удобочитаемости опираются на среднюю длину предложения, исходный SMOG - на выборку из 30 предложений: на коротком тексте значения неустойчивы, включая сводный класс, это грубая оценка"
      ]
    }
    ```

## Quick start { #quickstart }

Connecting to Claude Code and downloading the dictionaries and the spaCy model for the `lexical`, `verse` and `syntax` groups:

```bash
claude mcp add ruts -- uvx ruts-mcp
uvx ruts-mcp download
```

Connecting to Claude Desktop, Cursor and other clients and the server settings are on the [Installation](installation.md) page.
