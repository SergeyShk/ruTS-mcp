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

The arguments of the prompts are optional: without them a prompt takes the text from the earlier messages of the conversation. This is the way to go in Claude Code, since Claude Code splits the arguments of a command on whitespace and a long text cannot be passed as an argument. Paste the text as a message or attach a file with `@`, then call the prompt without arguments:

```text
/mcp__ruts__readability_review
```

For a comparison paste both texts, text A first. Other clients show MCP prompts in their own way.
