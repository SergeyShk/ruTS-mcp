# Word dispersion

``` {.python .signature}
dispersion(text="", path=null, words=null, parts=10, lemmatize=true, top_n=20)
```

Dispersion - how evenly a word is spread over the text: it tells a word that runs through the whole text from a word concentrated in one place, although their frequency does not. The text is split into `parts` parts of about equal size, and the measures of Gries and other dispersion measures are computed for every word.

A word with a frequency below `parts` cannot fall into all the parts, and its measures show concentration even with the most even spread: the response warns about such words. A word absent from the text has frequency 0 and `null` measures.

Errors - [those common to the tools](index.md#errors), a text without words, more parts than words and a word in `words` that is not one word.

=== "Call"

    ``` json
    {
      "name": "dispersion",
      "arguments": {
        "text": "Кот сидел на окне и смотрел на птиц. Птицы улетели, и кот уснул на окне. Завтра кот снова будет сидеть на окне и смотреть на птиц.",
        "words": ["кот", "птица"],
        "parts": 3
      }
    }
    ```

=== "Result"

    ``` json
    {
      "n_words": 26,
      "words": [
        {
          "word": "кот",
          "freq": 3,
          "dp": 0.3205,
          "dp_norm": 0.463,
          "juilland_d": 0.4226,
          "carroll_d2": 0.5794,
          "rosengren_s": 0.6725,
          "kl_divergence": 0.6122
        },
        {
          "word": "птица",
          "freq": 3,
          "dp": 0.3462,
          "dp_norm": 0.5,
          "juilland_d": 0.4443,
          "carroll_d2": 0.5948,
          "rosengren_s": 0.641,
          "kl_divergence": 0.6689
        }
      ],
      "warnings": []
    }
    ```

## Parameters

| Parameter | Type | Default | Description |
| :-------- | :--- | :------ | :---------- |
| `text` | `string` | `""` | Text |
| `path` | `string` | `null` | Absolute path to a file with the text instead of `text` |
| `words` | `array[string]` | `null` | Words whose dispersion is needed, up to 200; not given - the most frequent words |
| `parts` | `integer` | `10` | Number of parts of the text, from 2 to 100 |
| `lemmatize` | `boolean` | `true` | Compare lemmas: the forms of a word count as one word |
| `top_n` | `integer` | `20` | Number of the most frequent words if `words` is not given, up to 200 |

## Result { #result }

| Field | Type | Description |
| :---- | :--- | :---------- |
| `n_words` | `integer` | Number of words in the text |
| `words` | `array[object]` | Words in the order of the request or by descending frequency: the word `word`, the frequency `freq` and the dispersion measures below |
| `warnings` | `array[string]` | The text is not in Russian, words are not in the text, word frequencies are below the number of parts |

| Measure | Values |
| :------ | :----- |
| `dp` | Deviation of proportions DP of Gries, the main measure: 0 - the word is spread in proportion to the part sizes, the greatest value about 1 - 1/`parts` - all occurrences in one part |
| `dp_norm` | DP divided by its greatest possible value: 1 - all occurrences in the smallest part |
| `juilland_d` | Juilland's D: 1 - even, 0 - in one part |
| `carroll_d2` | Carroll's D2 by the entropy of the distribution: 1 - even, 0 - in one part |
| `rosengren_s` | Rosengren's S: 1 - proportional, about 1/`parts` - in one part |
| `kl_divergence` | Kullback-Leibler divergence in bits: 0 - proportional, grows with concentration |
