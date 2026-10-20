# Corpus comparison

``` {.python .signature}
compare_texts(a=[], b=[], a_paths=[], b_paths=[], window=null, whole_texts=false, top_n=15)
```

Comparison of two corpora by style features - for authorship attribution, comparing genres and translations, human and model texts. The texts are cut into windows of `window` words, about 110 features of ruTS are computed for every window, and the distributions of every feature in the corpora A and B are compared. With `whole_texts` whole texts are compared, without windows.

A text is cut in a row into windows of exactly `window` words; a remainder shorter than a window and a text shorter than a window are left out of the comparison. The response warns about such texts and about a loss of more than 10% of the words of a corpus on remainders, and a smaller window loses less text. When whole texts are compared, the response warns if the mean text length differs noticeably between the corpora: features that depend on the text length differ because of it as well.

Each corpus needs at least two windows. Several texts per corpus are more reliable: the windows of one text are not independent, and with few texts `p_holm` is understated.

Errors - [those common to the tools](index.md#errors) and:

- a corpus is empty or its texts have no words;
- a corpus has fewer than two windows;
- a corpus is longer than the `RUTS_MCP_MAX_TEXT_LENGTH` limit: the limit applies to the sum of the lengths of its texts.

=== "Call"

    ``` json
    {
      "name": "compare_texts",
      "arguments": {
        "a": [
          "Кот сидел на окне и смотрел на птиц. Птицы улетели, и кот уснул на окне. Завтра кот снова будет сидеть на окне и смотреть на птиц.",
          "Кот лежал на диване и смотрел в окно. Потом кот уснул."
        ],
        "b": [
          "Собака лежала у двери и ждала хозяина. Хозяин пришел поздно.",
          "Собака бегала по двору и лаяла на прохожих. Вечером собака уснула."
        ],
        "whole_texts": true,
        "top_n": 3
      }
    }
    ```

=== "Result"

    ``` json
    {
      "window": null,
      "n_windows": {"a": 2, "b": 2},
      "n_texts": {"a": 2, "b": 2},
      "features": [
        {
          "feature": "readability_flesch_kincaid_grade",
          "mean_a": -6.079,
          "mean_b": 4.281,
          "median_diff": -10.36,
          "ci_low": -11.62,
          "ci_high": -9.102,
          "cliff_delta": -1.0,
          "p_holm": 1.0
        },
        {
          "feature": "readability_consensus_grade",
          "mean_a": -2.0,
          "mean_b": 1.25,
          "median_diff": -3.25,
          "ci_low": -4.0,
          "ci_high": -2.5,
          "cliff_delta": -1.0,
          "p_holm": 1.0
        },
        {
          "feature": "readability_automated_readability_index",
          "mean_a": -4.943,
          "mean_b": 1.135,
          "median_diff": -6.078,
          "ci_low": -6.829,
          "ci_high": -5.328,
          "cliff_delta": -1.0,
          "p_holm": 1.0
        }
      ],
      "warnings": [
        "Средняя длина текста в A - 18 слов, в B - 10: признаки, которые зависят от длины текста (лексическое разнообразие, доли и частоты слов), различаются и из-за нее; чтобы сравнивать отрывки одной длины, сравнивайте окнами (whole_texts=false)",
        "Ни одно различие не значимо после поправки Холма (p_holm < 0.05): окон в A - 2, в B - 2. Нужно больше текстов; дельта Клиффа на таком числе окон - грубая оценка",
        "Еще 15 признаков с тем же модулем дельты Клиффа 1.0 - за пределами top_n: при равной дельте признаки упорядочены по относительной разности медиан; больше признаков дает top_n"
      ]
    }
    ```

## Parameters

| Parameter | Type | Default | Description |
| :-------- | :--- | :------ | :---------- |
| `a` | `array[string]` | `[]` | Texts of the first corpus, up to 1000 |
| `b` | `array[string]` | `[]` | Texts of the second corpus, up to 1000 |
| `a_paths` | `array[string]` | `[]` | Absolute paths to files with texts of the first corpus, together with `a` or instead of it |
| `b_paths` | `array[string]` | `[]` | Absolute paths to files with texts of the second corpus, together with `b` or instead of it |
| `window` | `integer` | `null` | Window size in words, from 100 to 10,000; not given - at most 1000 and such that the shortest text splits into at least two windows |
| `whole_texts` | `boolean` | `false` | Compare whole texts, without windows; at least two texts per corpus are needed |
| `top_n` | `integer` | `15` | Number of features with the largest difference, up to 200 |

## Features { #features }

| Prefix | Features |
| :----- | :------- |
| `basic_` | Shares of long, complex, mono- and polysyllabic words, of letters, spaces and marks, letters and syllables per word |
| `readability_` | Readability formulas |
| `diversity_` | Lexical diversity measures |
| `morph_` | Shares of parts of speech, negations and short forms among words (`morph_pos_NOUN`, `morph_polarity_Neg`) and of the values of the other features within the feature (`morph_case_Gen`, `morph_tense_Past`) |
| `sents_` | Mean sentence length in words, its standard deviation, coefficient of variation and autocorrelation of adjacent lengths |
| `punct_` | Marks by type per 1000 words and the share of the letter ё |

## Result { #result }

| Field | Type | Description |
| :---- | :--- | :---------- |
| `window` | `integer` | Window size; `null` - whole texts |
| `n_windows` | `object` | Number of windows in A and B |
| `n_texts` | `object` | Number of texts in A and B |
| `features` | `array[object]` | Features by descending absolute Cliff's delta, with equal deltas by the relative difference of medians, with the fields below |
| `warnings` | `array[string]` | A corpus is not in Russian, the texts of the corpora differ in length, texts or their remainders are left out of the comparison, a corpus has one text, no difference is significant |

| Feature field | Description |
| :------------ | :---------- |
| `feature` | Name of the feature |
| `mean_a`, `mean_b` | Means over the windows of A and B |
| `median_diff` | Difference of medians A - B |
| `ci_low`, `ci_high` | 95% bootstrap interval of the difference of medians; the bootstrap resamples whole texts |
| `cliff_delta` | Cliff's delta from -1 to 1: the share of window pairs where A is greater minus the share where it is smaller; in absolute value from 0.147 - small, from 0.33 - medium, from 0.474 - large effect |
| `p_holm` | p-value of the Mann-Whitney U test with the Holm correction for the number of features |
