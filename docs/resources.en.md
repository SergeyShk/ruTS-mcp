# Resources and prompts

## Resources { #resources }

Resources are reference data that a client can attach to a conversation. All of them are in Markdown (in Russian) and are built from the data of ruTS when read.

| URI | Contents |
| :-- | :------- |
| `ruts://scales/readability` | School grade and reader age for the grade formulas, the bands of the Flesch index and LIX, the grades of RIX |
| `ruts://scales/style` | Norms of SEO services for nausea, water content, spam score and naturalness by Zipf's law |
| `ruts://data` | The data directory and which dictionaries and spaCy model are downloaded |

In Claude Code a resource is attached by a mention, for example `@ruts:ruts://scales/readability`.

## Prompts { #prompts }

Prompts are ready review scenarios: which tools to call, how to read the result and how to conclude.

| Prompt | Arguments | What it does |
| :----- | :-------- | :----------- |
| `readability_review` | `text` | What reader the text is written for and how to simplify it |
| `officialese_review` | `text` | Officialese in the text and plain replacements |
| `verse_review` | `text` | Meter, rhyme schemes, line endings and sound patterns of a poem |
| `seo_review` | `text` | Norms of SEO services and keywords of a text for a website |
| `compare_review` | `text_a`, `text_b` | How two texts differ by style and vocabulary |

In Claude Code a prompt is called as a command with the text in quotes:

```text
/mcp__ruts__readability_review "В целях повышения качества обслуживания..."
```

Other clients show MCP prompts in their own way; the arguments are the same.
