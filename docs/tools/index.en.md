# Tools

The tools of the server measure a text with the statistics of [ruTS](https://sergeyshk.github.io/ruTS/en/). All of them only read the given text: they store nothing and do not go to the network.

| Tool | What it does | Data |
| :--- | :----------- | :--- |
| [`analyze_text`](analyze_text.md) | Statistics of a text in ten groups with readings by scales | dictionaries and the spaCy model for the `lexical`, `verse` and `syntax` groups |
| [`kwic`](kwic.md) | All occurrences of a word or a phrase with their context | - |
| [`collocations`](collocations.md) | Pairs of words that occur together more often than by chance | - |
| [`dispersion`](dispersion.md) | How evenly words are spread over the text | - |
| [`keyness`](keyness.md) | Keywords against the Russian language or another text | frequency dictionary if no reference is given |
| [`compare_texts`](compare_texts.md) | How two corpora of texts differ by style features | - |

How to download the data is described in [Dictionaries and the spaCy model](../installation.md#data). The definitions and formulas of the metrics are in the ruTS documentation: the server passes the values of ruTS as they are.

## Text { #text }

A text is given by the `text` argument or by the path to a file `path` - an absolute path to a UTF-8 file on the machine where the server runs. A file is handier for a long text: the agent does not have to send it in an argument, and the statistics are computed on the original text rather than on its retelling. A text and a corpus are limited in length: `RUTS_MCP_MAX_TEXT_LENGTH`, 500,000 characters by default (see [Settings](../installation.md#settings)).

Stress marks and soft hyphens inside words do not get in the way: words are compared without them, `kwic` shows the text as written, and the `verse` group takes the stress from the mark. Like ruTS, `analyze_text` counts «ещё» and «еще» as different words, while `kwic`, `collocations`, `dispersion` and `keyness` reduce ё to е.

## Response { #response }

Every response has the `warnings` key - the reasons why values may be unstable or meaningless for this text: a short text, a text not in Russian, dictionaries or the model not downloaded, a statistic undefined on the text. The agent should read them before drawing conclusions. Numbers are rounded to four significant digits, an undefined value is `null`. Descriptions, readings and warnings are in Russian.

## Errors { #errors }

An error reaches the agent as a tool error with a message saying what is wrong with the call. Common to all tools:

- an argument does not pass the schema of the tool: a wrong type, a number out of the allowed range, a value not in the list;
- no text is given, or it is given together with a path to a file;
- the path is not absolute, the file cannot be read, is not in UTF-8 or exceeds the limit;
- the text is longer than the `RUTS_MCP_MAX_TEXT_LENGTH` limit;
- the text has lone UTF-16 surrogate characters: this happens when a string is cut in the middle of an emoji.

The errors that depend on a tool are listed on its page.
