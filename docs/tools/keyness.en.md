# Keywords

``` {.python .signature}
keyness(text="", path=null, reference=null, reference_path=null, measure="log_likelihood", positive=true, min_freq=2, lemmatize=true, top_n=20)
```

Keywords - words that are significantly more (or, with `positive=false`, less) frequent in the text than in a reference. The default reference is the frequency dictionary of Lyashevskaya and Sharoff (modern Russian, 92 million tokens; downloaded by `ruts-mcp download`), and then the response shows how the vocabulary of the text differs from ordinary language. The reference can also be another text: `reference` or `reference_path`.

Words are compared in lower case and with е instead of ё. Against the dictionary lemmas are always compared, numbers and words with Latin letters are dropped, and a word outside the dictionary gets its least frequency: names, terms and typos become keywords. Dictionary entries that no word of the text is reduced to (его, ее, их, во, со - forms of the lemmas он, она, они, в, с) do not appear among the words more frequent in the reference. If the reference lacks a word, Log Ratio is an estimate with the 0.5 correction and can be below zero although the word is more frequent in the text. The p-value is not corrected for the number of words tested: p < 0.0001 (`g2` from 15.13) is more reliable.

Errors - [those common to the tools](index.md#errors) and:

- no reference is given, and the frequency dictionary is not downloaded or is damaged;
- no reference is given, and the text has no words of Cyrillic letters;
- the text or the reference has no words.

=== "Call"

    ``` json
    {
      "name": "keyness",
      "arguments": {
        "text": "Кот сидел на окне и смотрел на птиц. Птицы улетели, и кот уснул на окне. Завтра кот снова будет сидеть на окне и смотреть на птиц.",
        "reference": "Кот спал на диване, а собака лежала у двери и ждала хозяина. Хозяин пришел поздно, и собака обрадовалась.",
        "min_freq": 2,
        "top_n": 3
      }
    }
    ```

=== "Result"

    ``` json
    {
      "n_words": 26,
      "reference": "текст-эталон, 18 слов",
      "measure": "log_likelihood: логарифм правдоподобия G² (Rayson и Garside 2000): значимость различия, со знаком минус - слово чаще в эталоне; критические значения: 3.84 - p < 0.05, 6.63 - p < 0.01, 10.83 - p < 0.001, 15.13 - p < 0.0001",
      "keywords": [
        {
          "word": "окно",
          "freq_target": 3,
          "freq_reference": 0.0,
          "ipm_target": 115400.0,
          "ipm_reference": 0.0,
          "g2": 3.157,
          "p_value": 0.07562,
          "log_ratio": 2.054,
          "score": 3.157
        },
        {
          "word": "птица",
          "freq_target": 3,
          "freq_reference": 0.0,
          "ipm_target": 115400.0,
          "ipm_reference": 0.0,
          "g2": 3.157,
          "p_value": 0.07562,
          "log_ratio": 2.054,
          "score": 3.157
        },
        {
          "word": "сидеть",
          "freq_target": 2,
          "freq_reference": 0.0,
          "ipm_target": 76920.0,
          "ipm_reference": 0.0,
          "g2": 2.104,
          "p_value": 0.1469,
          "log_ratio": 1.469,
          "score": 2.104
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
| `reference` | `string` | `null` | Reference text; not given - the frequency dictionary |
| `reference_path` | `string` | `null` | Absolute path to a file with the reference text instead of `reference` |
| `measure` | `string` | `"log_likelihood"` | Sorting measure: `log_likelihood`, `log_ratio`, `chi2`, `diff`, `bic`, `ell`, `odds_ratio`; `log_likelihood` - significance of the difference, `log_ratio` - how many times more frequent the word is |
| `positive` | `boolean` | `true` | Words more frequent in the text; `false` - more frequent in the reference |
| `min_freq` | `integer` | `2` | Least frequency of a word where it is more frequent |
| `lemmatize` | `boolean` | `true` | Compare lemmas; against the dictionary lemmas are always compared |
| `top_n` | `integer` | `20` | Number of words in the response, up to 200 |

## Result { #result }

| Field | Type | Description |
| :---- | :--- | :---------- |
| `n_words` | `integer` | Number of words of the text compared with the reference |
| `reference` | `string` | The reference |
| `measure` | `string` | The sorting measure and how to read its values |
| `keywords` | `array[object]` | Words by descending measure with the fields below |
| `warnings` | `array[string]` | The text or the reference is not in Russian, there are no keywords |

| Word field | Description |
| :--------- | :---------- |
| `word` | Word or lemma |
| `freq_target`, `freq_reference` | Frequency in the text and in the reference |
| `ipm_target`, `ipm_reference` | The same per million words |
| `g2` | Log-likelihood G²: significance of the difference, with a minus sign - the word is more frequent in the reference |
| `p_value` | p-value of G² |
| `log_ratio` | Log Ratio: binary logarithm of the frequency ratio, the effect size; 1 - the word is twice as frequent in the text |
| `score` | Value of the sorting measure |
