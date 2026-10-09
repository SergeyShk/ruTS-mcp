# Tools

## Common { #common }

All tools only read the given text: they store nothing and do not go to the network. A text and a corpus are limited in length (`RUTS_MCP_MAX_TEXT_LENGTH`, 500,000 characters by default, see [Settings](installation.md#settings)).

A text is given by the `text` argument or by the path to a file `path` - an absolute path to a UTF-8 file on the machine where the server runs. A file is handier for a long text: the agent does not have to send it in an argument, and the statistics are computed on the original text rather than on its retelling. Stress marks and soft hyphens inside words do not get in the way: words are compared without them, `kwic` shows the text as written, and the `verse` group takes the stress from the mark.

Every result has the `warnings` key - the reasons why values may be unstable or meaningless for this text: a short text, a text not in Russian, dictionaries or the model not downloaded, a statistic undefined on the text. The agent should read them before drawing conclusions. Numbers are rounded to four significant digits, an undefined value is `null`. Descriptions, readings and warnings are in Russian.

The definitions and formulas of the metrics are in the [ruTS documentation](https://sergeyshk.github.io/ruTS/en/); the server passes the values of ruTS as they are.

## analyze_text { #analyze_text }

Statistics of a text by groups; only the requested groups are computed.

| Parameter | Default | Description |
| :-------- | :-----: | :---------- |
| `text` | - | Text in Russian |
| `path` | - | Path to a file with the text instead of `text` |
| `groups` | `["basic", "readability"]` | Groups of statistics; each is a key of the result |
| `distributions` | `false` | Add the distributions of words by letters and syllables and of punctuation marks by type (the `basic` group) |
| `readability_preset` | `plainrussian` | Coefficients of the readability formulas: `plainrussian` is calibrated by school grades and fits any text; `fiction` - Oborneva's coefficients from fiction, gives a grade several years higher; `academic` - the coefficients of Solovyev, Ivanov and Solnyshkina from textbooks for grades 5-11 |
| `descriptions` | `true` | Add descriptions to the statistics; `false` - a shorter result when the descriptions are known from a previous call |

| Group | What it computes | Data |
| :---- | :--------------- | :--: |
| `basic` | Sentences, words, syllables, characters, long and complex words ([BasicStats](https://sergeyshk.github.io/ruTS/en/stats/basic_stats/)) | - |
| `readability` | Consensus grade and readability formulas with the school grade and reader age, reading time ([ReadabilityStats](https://sergeyshk.github.io/ruTS/en/stats/readability_stats/)) | - |
| `diversity` | Lexical diversity: TTR and its corrections, MATTR, MTLD, HD-D, the laws of Zipf and Heaps ([DiversityStats](https://sergeyshk.github.io/ruTS/en/stats/diversity_stats/)) | - |
| `morph` | Parts of speech, grammatical features, verb forms ([MorphStats](https://sergeyshk.github.io/ruTS/en/stats/morph_stats/)) | - |
| `phon` | Sound classes, consonant clusters, alliteration and assonance ([PhonStats](https://sergeyshk.github.io/ruTS/en/stats/phon_stats/)) | - |
| `cohesion` | Cohesion: overlaps between sentences, givenness, connectives ([CohesionStats](https://sergeyshk.github.io/ruTS/en/stats/cohesion_stats/)) | - |
| `style` | Nausea, water content, spam score read by the norms of SEO services, the most frequent word forms, officialese markers with the words and phrases found ([StyleStats](https://sergeyshk.github.io/ruTS/en/stats/style_stats/)) | - |
| `lexical` | Word frequency, frequency bands, surprisal, lexical density ([LexicalStats](https://sergeyshk.github.io/ruTS/en/stats/lexical_stats/)) | frequency dictionary for frequency and surprisal |
| `verse` | Meter, number of feet, rhyme schemes, line endings; a stress mark in the text («замо́к») outweighs the dictionary ([VerseStats](https://sergeyshk.github.io/ruTS/en/stats/verse_stats/)) | stress dictionary |
| `syntax` | Dependency lengths, tree depth, clauses, participial and adverbial phrases, passive, split predicates ([SyntaxStats](https://sergeyshk.github.io/ruTS/en/stats/syntax_stats/)) | spaCy model |

How to download the data is described in [Dictionaries and the spaCy model](installation.md#data).

Every statistic in the result is an object with the fields:

| Field | Description |
| :---- | :---------- |
| `value` | Value |
| `share` | Share of all words or characters, if there is one |
| `interpretation` | Reading by a scale or a norm of ruTS, if there is a scale: the grade and age of the reader, the band of the Flesch index, the Text.ru norm |
| `count`, `found` | For the officialese markers of the `style` group: the number of occurrences and the words and phrases found with their frequencies |
| `description` | What the statistic computes |

Like ruTS, `analyze_text` counts «ещё» and «еще» as different words, while `kwic`, `collocations`, `dispersion` and `keyness` reduce ё to е.

The reading scales are provided by the [resources](resources.md#resources) `ruts://scales/readability` and `ruts://scales/style`.

## kwic { #kwic }

All occurrences of a word or a phrase with the context on the left and on the right - a concordance the agent quotes the text by.

| Parameter | Default | Description |
| :-------- | :-----: | :---------- |
| `keyword` | - | Word or phrase |
| `text` | - | Text |
| `path` | - | Path to a file with the text instead of `text` |
| `window` | `5` | Number of context words on each side, up to 50 |
| `by_lemma` | `false` | Find all forms of the word: «кот» finds «кота» and «коты» |
| `limit` | `50` | Greatest number of lines in the result, up to 500 |

The result is the number of occurrences `n_matches` and the lines `matches` with the fields `left`, `keyword` and `right`. Besides `limit`, the lines are limited by size: about 40,000 characters of context per result; if not all occurrences are shown, a warning tells how many.

## collocations { #collocations }

Collocations - pairs of words that occur together more often than by chance: set phrases, terms, the collocates of a word.

| Parameter | Default | Description |
| :-------- | :-----: | :---------- |
| `text` | - | Text |
| `path` | - | Path to a file with the text instead of `text` |
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
| `path` | - | Path to a file with the text instead of `text` |
| `words` | - | Words whose dispersion is needed, up to 200; not given - the most frequent words |
| `parts` | `10` | Number of parts of the text, from 2 to 100 |
| `lemmatize` | `true` | Compare lemmas |
| `top_n` | `20` | Number of the most frequent words if `words` is not given |

## keyness { #keyness }

Keywords - words that are significantly more (or less) frequent in the text than in a reference. The default reference is the frequency dictionary of modern Russian (downloaded by `ruts-mcp download`), so the result shows how the vocabulary of the text differs from ordinary language; the reference can also be another text.

| Parameter | Default | Description |
| :-------- | :-----: | :---------- |
| `text` | - | Text |
| `path` | - | Path to a file with the text instead of `text` |
| `reference` | - | Reference text; not given - the frequency dictionary |
| `reference_path` | - | Path to a file with the reference text instead of `reference` |
| `measure` | `log_likelihood` | Sorting measure: `log_likelihood`, `log_ratio`, `chi2`, `diff`, `bic`, `ell`, `odds_ratio` |
| `positive` | `true` | Words more frequent in the text; `false` - more frequent in the reference |
| `min_freq` | `2` | Least frequency of a word where it is more frequent |
| `lemmatize` | `true` | Compare lemmas; against the dictionary lemmas are always compared |
| `top_n` | `20` | Number of words in the result, up to 200 |

For every word the result gives the frequencies in the text and the reference, the log-likelihood G² with its p-value and Log Ratio - how many times more frequent the word is. If the reference lacks the word, Log Ratio is an estimate with the 0.5 correction and can be below zero although the word is more frequent in the text. Against the dictionary, names, terms and typos that it lacks become keywords, while dictionary entries that no word of the text is reduced to (его, ее, их, во, со - forms of the lemmas он, она, они, в, с) do not appear among the words more frequent in the reference.

## compare_texts { #compare_texts }

Comparison of two corpora by style features - for authorship attribution, comparing genres and translations, human and model texts. The texts are cut into windows of `window` words, about 110 features of ruTS are computed for every window, and the distributions of every feature in the corpora are compared.

| Parameter | Default | Description |
| :-------- | :-----: | :---------- |
| `a` | - | Texts of the first corpus, up to 1000 |
| `b` | - | Texts of the second corpus, up to 1000 |
| `a_paths` | - | Paths to files with texts of the first corpus, together with `a` or instead of it |
| `b_paths` | - | Paths to files with texts of the second corpus, together with `b` or instead of it |
| `window` | - | Window size in words, from 100 to 10,000; not given - at most 1000 and such that the shortest text splits into at least two windows |
| `whole_texts` | `false` | Compare whole texts, without windows |
| `top_n` | `15` | Number of features with the largest difference, up to 200 |

A text is cut in a row into windows of exactly `window` words; a remainder shorter than a window and a text shorter than a window are left out of the comparison (the result warns about such texts and about a loss of more than 10% of the words of a corpus on remainders; a smaller window loses less text). When whole texts are compared, the result warns if the mean text length differs noticeably between the corpora: features that depend on the text length differ because of it as well.

The result is the features by descending absolute Cliff's delta, with equal deltas by the relative difference of medians: the means over windows, the difference of medians with a 95% confidence interval, Cliff's delta (in absolute value from 0.147 - small, from 0.33 - medium, from 0.474 - large effect) and the p-value with the Holm correction. Each corpus needs at least two windows; several texts per corpus are more reliable, since the windows of one text are not independent.
