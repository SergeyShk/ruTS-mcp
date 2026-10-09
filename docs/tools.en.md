# Tools

## Common { #common }

All tools only read the given text: they store nothing and do not go to the network. A text and a corpus are limited in length (`RUTS_MCP_MAX_TEXT_LENGTH`, 500,000 characters by default, see [Settings](installation.md#settings)).

Every result has the `warnings` key - the reasons why values may be unstable or meaningless for this text: a short text, a text not in Russian, dictionaries or the model not downloaded, a statistic undefined on the text. The agent should read them before drawing conclusions. Numbers are rounded to four significant digits, an undefined value is `null`. Descriptions, readings and warnings are in Russian.

The definitions and formulas of the metrics are in the [ruTS documentation](https://sergeyshk.github.io/ruTS/en/); the server passes the values of ruTS as they are.

## analyze_text { #analyze_text }

Statistics of a text by groups; only the requested groups are computed.

| Parameter | Default | Description |
| :-------- | :-----: | :---------- |
| `text` | - | Text in Russian |
| `groups` | `["basic", "readability"]` | Groups of statistics; each is a key of the result |
| `distributions` | `false` | Add the distributions of words by letters and syllables and of punctuation marks by type (the `basic` group) |
| `readability_preset` | `plainrussian` | Coefficients of the readability formulas: `plainrussian` - general texts, `fiction` - fiction, `academic` - educational texts |

| Group | What it computes | Data |
| :---- | :--------------- | :--: |
| `basic` | Sentences, words, syllables, characters, long and complex words ([BasicStats](https://sergeyshk.github.io/ruTS/en/stats/basic_stats/)) | - |
| `readability` | Consensus grade and readability formulas with the school grade and reader age, reading time ([ReadabilityStats](https://sergeyshk.github.io/ruTS/en/stats/readability_stats/)) | - |
| `diversity` | Lexical diversity: TTR and its corrections, MATTR, MTLD, HD-D, the laws of Zipf and Heaps ([DiversityStats](https://sergeyshk.github.io/ruTS/en/stats/diversity_stats/)) | - |
| `morph` | Parts of speech, grammatical features, verb forms ([MorphStats](https://sergeyshk.github.io/ruTS/en/stats/morph_stats/)) | - |
| `phon` | Sound classes, consonant clusters, alliteration and assonance ([PhonStats](https://sergeyshk.github.io/ruTS/en/stats/phon_stats/)) | - |
| `cohesion` | Cohesion: overlaps between sentences, givenness, connectives ([CohesionStats](https://sergeyshk.github.io/ruTS/en/stats/cohesion_stats/)) | - |
| `style` | Nausea, water content, spam score read by the norms of SEO services, officialese markers ([StyleStats](https://sergeyshk.github.io/ruTS/en/stats/style_stats/)) | - |
| `lexical` | Word frequency, frequency bands, surprisal, lexical density ([LexicalStats](https://sergeyshk.github.io/ruTS/en/stats/lexical_stats/)) | frequency dictionary |
| `verse` | Meter, number of feet, rhyme schemes, line endings ([VerseStats](https://sergeyshk.github.io/ruTS/en/stats/verse_stats/)) | stress dictionary |
| `syntax` | Dependency lengths, tree depth, clauses, participial and adverbial phrases, passive, split predicates ([SyntaxStats](https://sergeyshk.github.io/ruTS/en/stats/syntax_stats/)) | spaCy model |

How to download the data is described in [Dictionaries and the spaCy model](installation.md#data).

Every statistic in the result is an object with the fields:

| Field | Description |
| :---- | :---------- |
| `value` | Value |
| `share` | Share of all words or characters, if there is one |
| `interpretation` | Reading by a scale or a norm of ruTS, if there is a scale: the grade and age of the reader, the band of the Flesch index, the Text.ru norm |
| `description` | What the statistic computes |

The reading scales are provided by the [resources](resources.md#resources) `ruts://scales/readability` and `ruts://scales/style`.

## kwic { #kwic }

All occurrences of a word or a phrase with the context on the left and on the right - a concordance the agent quotes the text by.

| Parameter | Default | Description |
| :-------- | :-----: | :---------- |
| `text` | - | Text |
| `keyword` | - | Word or phrase |
| `window` | `5` | Number of context words on each side, up to 50 |
| `by_lemma` | `false` | Find all forms of the word: «кот» finds «кота» and «коты» |
| `limit` | `50` | Greatest number of lines in the result, up to 500 |

The result is the number of occurrences `n_matches` and the lines `matches` with the fields `left`, `keyword` and `right`.

## collocations { #collocations }

Collocations - pairs of words that occur together more often than by chance: set phrases, terms, the collocates of a word.

| Parameter | Default | Description |
| :-------- | :-----: | :---------- |
| `text` | - | Text |
| `window` | `5` | Greatest distance between the words of a pair, from 1 to 10 |
| `measure` | `logdice` | Association measure: `logdice`, `mi`, `mi3`, `t_score`, `dice`, `log_likelihood`, `npmi`, `min_sensitivity` |
| `min_freq` | `2` | Least frequency of a pair |
| `node` | - | Word whose collocates are needed; not given - all pairs |
| `lemmatize` | `true` | Compare lemmas: «точка зрения» and «точки зрения» are one pair |
| `top_n` | `20` | Number of pairs in the result, up to 200 |

The result is the pairs by descending measure with the frequencies of the words and of the pair, and the `measure` line that tells how to read the values of the measure.

## dispersion { #dispersion }

Dispersion - how evenly a word is spread over the text: it tells a word that runs through the whole text from a word concentrated in one place. The text is split into equal parts, and the measures of Gries are computed for every word; the main one is DP, from 0 (even) to almost 1 (in one part).

| Parameter | Default | Description |
| :-------- | :-----: | :---------- |
| `text` | - | Text |
| `words` | - | Words whose dispersion is needed, up to 200; not given - the most frequent words |
| `parts` | `10` | Number of parts of the text, from 2 to 100 |
| `lemmatize` | `true` | Compare lemmas |
| `top_n` | `20` | Number of the most frequent words if `words` is not given |

## keyness { #keyness }

Keywords - words that are significantly more (or less) frequent in the text than in a reference. The default reference is the frequency dictionary of modern Russian (downloaded by `ruts-mcp download`), so the result shows how the vocabulary of the text differs from ordinary language; the reference can also be another text.

| Parameter | Default | Description |
| :-------- | :-----: | :---------- |
| `text` | - | Text |
| `reference` | - | Reference text; not given - the frequency dictionary |
| `measure` | `log_likelihood` | Sorting measure: `log_likelihood`, `log_ratio`, `chi2`, `diff`, `bic`, `ell`, `odds_ratio` |
| `positive` | `true` | Words more frequent in the text; `false` - more frequent in the reference |
| `min_freq` | `2` | Least frequency of a word where it is more frequent |
| `lemmatize` | `true` | Compare lemmas; against the dictionary lemmas are always compared |
| `top_n` | `20` | Number of words in the result, up to 200 |

For every word the result gives the frequencies in the text and the reference, the log-likelihood G² with its p-value and Log Ratio - how many times more frequent the word is. Against the dictionary, names, terms and typos that it lacks become keywords.

## compare_texts { #compare_texts }

Comparison of two corpora by style features - for authorship attribution, comparing genres and translations, human and model texts. The texts are cut into windows of equal length, about 110 features of ruTS are computed for every window, and the distributions of every feature in the corpora are compared.

| Parameter | Default | Description |
| :-------- | :-----: | :---------- |
| `a` | - | Texts of the first corpus |
| `b` | - | Texts of the second corpus |
| `window` | `1000` | Window size in words, from 100 to 10,000; `null` - whole texts |
| `top_n` | `15` | Number of features with the largest difference, up to 200 |

The result is the features by descending difference: the means over windows, the difference of medians with a 95% confidence interval, Cliff's delta (in absolute value from 0.147 - small, from 0.33 - medium, from 0.474 - large effect) and the p-value with the Holm correction. Each corpus needs at least two windows; several texts per corpus are more reliable, since the windows of one text are not independent.
