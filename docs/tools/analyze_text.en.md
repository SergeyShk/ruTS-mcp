# Text statistics

``` {.python .signature}
analyze_text(text="", path=null, groups=["basic", "readability"], distributions=false, readability_preset="plainrussian", descriptions=true)
```

Measures a text with the statistics of ruTS by groups: only the requested groups are computed, and each one becomes a key of the response. A statistic comes with its value, share or reading by a scale, if there is one, and with a description of what it computes. The `warnings` key tells when the values are unstable or meaningless for this text. Descriptions known from a previous call need not be requested again: `descriptions=false` gives a shorter response.

Errors - [those common to the tools](index.md#errors) and a text without words.

=== "Call"

    ``` json
    {
      "name": "analyze_text",
      "arguments": {
        "text": "В целях повышения качества обслуживания клиентов в кратчайшие сроки осуществляется проведение мероприятий по модернизации оборудования, предусмотренных утвержденным планом развития организации на текущий период.",
        "groups": ["style"],
        "descriptions": false
      }
    }
    ```

=== "Result"

    ``` json
    {
      "style": {
        "n_words": {"value": 23},
        "top_words": {
          "value": {
            "в": 2,
            "целях": 1,
            "повышения": 1,
            "качества": 1,
            "обслуживания": 1,
            "клиентов": 1,
            "кратчайшие": 1,
            "сроки": 1,
            "осуществляется": 1,
            "проведение": 1
          }
        },
        "nausea_words": {
          "value": {
            "целях": 1,
            "повышения": 1,
            "качества": 1,
            "обслуживания": 1,
            "клиентов": 1,
            "кратчайшие": 1,
            "сроки": 1,
            "осуществляется": 1,
            "проведение": 1,
            "мероприятий": 1
          }
        },
        "classic_nausea": {"value": 1.414, "interpretation": "норма Advego"},
        "academic_nausea": {"value": 43.48, "interpretation": "выше нормы Advego"},
        "water": {"value": 0.0, "interpretation": "естественная водность по Text.ru"},
        "spam": {"value": 4.348, "interpretation": "естественный текст по Text.ru"},
        "zipf_naturalness": {"value": 100.0, "interpretation": "норма pr-cy и megaindex"},
        "verbal_nouns": {
          "value": 57.14,
          "count": 8,
          "found": {
            "повышения": 1,
            "обслуживания": 1,
            "проведение": 1,
            "мероприятий": 1,
            "модернизации": 1,
            "оборудования": 1,
            "развития": 1,
            "организации": 1
          }
        },
        "compound_prepositions": {"value": 4.348, "count": 1, "found": {"в целях": 1}},
        "parentheticals": {"value": 0.0, "count": 0, "found": {}},
        "cliches": {"value": 4.348, "count": 1, "found": {"в кратчайшие сроки": 1}}
      },
      "warnings": [
        "Слов в тексте: 23, меньше 200. Нормы сервисов рассчитаны на тексты сайтов в несколько сотен слов: на коротком тексте тошнота, заспамленность и естественность по Ципфу неинформативны, их прочтение по нормам - грубая оценка"
      ]
    }
    ```

## Parameters

| Parameter | Type | Default | Description |
| :-------- | :--- | :------ | :---------- |
| `text` | `string` | `""` | Text in Russian |
| `path` | `string` | `null` | Absolute path to a file with the text instead of `text` |
| `groups` | `array[string]` | `["basic", "readability"]` | [Groups](#groups) of statistics; each is a key of the response |
| `distributions` | `boolean` | `false` | Add the distributions of words by letters and syllables and of punctuation marks by type (the `basic` group) |
| `readability_preset` | `string` | `"plainrussian"` | Coefficients of the Flesch-Kincaid test (with `academic` also of the Flesch index), on which the consensus grade depends as well: `plainrussian` is calibrated by school grades and fits any text; `fiction` - Oborneva's coefficients from fiction, gives a grade several years higher; `academic` - the coefficients of Solovyev, Ivanov and Solnyshkina from textbooks for grades 5-11 |
| `descriptions` | `boolean` | `true` | Add descriptions to the statistics |

## Groups { #groups }

| Group | What it computes | Data |
| :---- | :--------------- | :--- |
| [`basic`](#basic) | Sentences, words, syllables, characters, long and complex words | - |
| [`readability`](#readability) | Consensus grade and readability formulas with the school grade and reader age | - |
| [`diversity`](#diversity) | Lexical diversity | - |
| [`morph`](#morph) | Parts of speech, grammatical features, verb forms | - |
| [`phon`](#phon) | Sound classes, consonant clusters, alliteration and assonance | - |
| [`cohesion`](#cohesion) | Cohesion: overlaps between sentences, givenness, connectives | - |
| [`style`](#style) | SEO metrics with the norms of services and officialese markers | - |
| [`lexical`](#lexical) | Word frequency, frequency bands, surprisal | frequency dictionary |
| [`verse`](#verse) | Meter, rhyme schemes, line endings | stress dictionary |
| [`syntax`](#syntax) | Syntax by the dependency tree | spaCy model |

How to download the data is described in [Dictionaries and the spaCy model](../installation.md#data). Without the data a group does not fail: the metrics that need them are not computed, and a warning names the command that downloads them.

<div class="metric-card" markdown>

### Basic statistics { #basic }

`basic` · [BasicStats](https://sergeyshk.github.io/ruTS/en/stats/basic_stats/)
{ .metric-meta }

Sentences, words, syllables, characters, letters, spaces and punctuation marks; unique, long (from 6 letters), complex (from 4 syllables), simple, monosyllabic and polysyllabic words. A count of words or characters comes with its share of all words or characters (`share`). With `distributions=true` the group adds the distributions of words by letters and syllables and of punctuation marks by type.

</div>

<div class="metric-card" markdown>

### Readability { #readability }

`readability` · [ReadabilityStats](https://sergeyshk.github.io/ruTS/en/stats/readability_stats/) · [`ruts://scales/readability`](../resources.md#resources)
{ .metric-meta }

Consensus grade and the formulas of Flesch-Kincaid, Flesch, Coleman-Liau, SMOG, ARI, LIX, RIX, Solovyev-Ivanov-Solnyshkina, Matskovsky, Dale-Chall and Gunning, reading time. The grade formulas and the consensus grade read as a school grade and reader age, the Flesch index, LIX and RIX as a band of their own scale; the Matskovsky formula and the reading time have no scale. The coefficients of the Flesch-Kincaid test and the Flesch index are set by `readability_preset`, the other formulas do not depend on it. On a text shorter than 30 sentences the formulas are unstable, and the response warns about it.

</div>

<div class="metric-card" markdown>

### Lexical diversity { #diversity }

`diversity` · [DiversityStats](https://sergeyshk.github.io/ruTS/en/stats/diversity_stats/)
{ .metric-meta }

TTR and its corrections, MATTR, MSTTR, MTLD, HD-D, the indices of Simpson, Yule and Honoré, entropy, the laws of Zipf and Heaps. On a text shorter than 50 words the measures are unstable, and on a text shorter than 200 words texts are better compared by MATTR, MTLD and HD-D: the response warns about it.

</div>

<div class="metric-card" markdown>

### Morphology { #morph }

`morph` · [MorphStats](https://sergeyshk.github.io/ruTS/en/stats/morph_stats/)
{ .metric-meta }

Parts of speech and grammatical features by pymorphy3 without disambiguation and the shares of verb forms: moods, infinitive, participles, converbs, perfective aspect, passive and reflexive forms. The value of a feature is the number of words with each of its values, labeled as in ruTS, and `share` gives their shares of all words.

</div>

<div class="metric-card" markdown>

### Phonostatistics { #phon }

`phon` · [PhonStats](https://sergeyshk.github.io/ruTS/en/stats/phon_stats/)
{ .metric-meta }

Shares of vowels, sonorant, voiced and voiceless consonants, heavy consonant clusters, hiatuses, harshness, open syllables, the indices of alliteration and assonance. Computed by letters, without stress, devoicing and reduction.

</div>

<div class="metric-card" markdown>

### Cohesion { #cohesion }

`cohesion` · [CohesionStats](https://sergeyshk.github.io/ruTS/en/stats/cohesion_stats/)
{ .metric-meta }

Cohesion after Coh-Metrix: overlaps of nouns, arguments and content words between sentences, pronouns, givenness, repetition of tense and aspect, connectives by class per 1000 words.

</div>

<div class="metric-card" markdown>

### Style { #style }

`style` · [StyleStats](https://sergeyshk.github.io/ruTS/en/stats/style_stats/) · [`ruts://scales/style`](../resources.md#resources)
{ .metric-meta }

SEO metrics by word forms - classic and academic nausea, water content, spam score and naturalness by Zipf's law read by the norms of Advego, Text.ru, pr-cy and megaindex - and the lexical markers of officialese: verbal nouns, compound prepositions, parenthetical words, clichés. The norms are meant for website texts of a few hundred words and do not apply to fiction; on a text shorter than 200 or longer than 1000 words the response warns about it.

Beyond the metrics of ruTS the group gives the number of words `n_words`, the most frequent word forms `top_words` and the most frequent content words `nausea_words`, by which the academic nausea is computed. The officialese markers come with the number of occurrences `count` and the words and phrases found `found`. The syntactic markers of officialese are in the [`syntax`](#syntax) group: to check a text for officialese, take both groups.

</div>

<div class="metric-card" markdown>

### Lexical sophistication { #lexical }

`lexical` · [LexicalStats](https://sergeyshk.github.io/ruTS/en/stats/lexical_stats/) · frequency dictionary
{ .metric-meta }

Share of words found in the frequency dictionary of Lyashevskaya and Sharoff, mean frequency (ipm) and its logarithm, range and dispersion over the corpus, surprisal and perplexity, shares of words from the 1000-10000 most frequent lemmas, lexical density. Without the dictionary the group computes only the shares of frequency bands and the lexical density.

</div>

<div class="metric-card" markdown>

### Verse { #verse }

`verse` · [VerseStats](https://sergeyshk.github.io/ruTS/en/stats/verse_stats/) · stress dictionary
{ .metric-meta }

Lines and stanzas, meter and number of feet, deviations from the meter and skipped stresses, share of rhymed lines and rhyme schemes, masculine, feminine and dactylic endings. A stress mark in the text («замо́к») outweighs the dictionary.

</div>

<div class="metric-card" markdown>

### Syntax { #syntax }

`syntax` · [SyntaxStats](https://sergeyshk.github.io/ruTS/en/stats/syntax_stats/) · spaCy model
{ .metric-meta }

Syntax by the dependency tree of the spaCy model: dependency length, depth and branching of the tree, verb valency, clauses and subordinate clauses, coordination chains, noun modifiers, chains of genitives, participial and adverbial phrases, passive, infinitives, negations, split predicates («оказать помощь»), the ratio of nouns to verbs. On a long text parsing takes seconds.

</div>

## Result { #result }

A key for each requested group and `warnings`. A statistic of a group is an object with the fields:

| Field | Type | Description |
| :---- | :--- | :---------- |
| `value` | `number` / `string` / `object` | Value; `null` - the statistic is undefined on this text |
| `share` | `number` / `object` | Share of all words or characters, if there is one |
| `interpretation` | `string` | Reading by a scale or a norm of ruTS, if there is a scale: the grade and age of the reader, the band of the Flesch index, the Text.ru norm |
| `count` | `integer` | For the officialese markers of the `style` group: the number of occurrences |
| `found` | `object` | For the officialese markers of the `style` group: the words and phrases found with their frequencies, up to the 20 most frequent |
| `description` | `string` | What the statistic computes; absent with `descriptions=false` |
