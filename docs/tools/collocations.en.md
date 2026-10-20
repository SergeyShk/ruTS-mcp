# Collocations

``` {.python .signature}
collocations(text="", path=null, window=5, measure="logdice", min_freq=2, node=null, lemmatize=true, top_n=20)
```

Collocations - pairs of words that occur together more often than by chance: set phrases, terms, the collocates of a word (`node`). A pair is ordered: the right word stands at most `window` words after the left one. With `lemmatize` lemmas are compared, without disambiguation: «точка зрения» and «точки зрения» are one pair. The definitions and formulas of the measures are on the ruTS page [Collocations](https://sergeyshk.github.io/ruTS/en/corpus/collocations/).

The pair frequency `freq_pair` is the number of position pairs where the right word stands within the window after the left one. A word repeated within the window gives several pairs, so `freq_pair` can exceed the frequency of a word, and such a pair is a repetition rather than a set phrase.

Errors - [those common to the tools](index.md#errors), a text without words and a `node` that is not one word.

=== "Call"

    ``` json
    {
      "name": "collocations",
      "arguments": {
        "text": "Кот сидел на окне и смотрел на птиц. Птицы улетели, и кот уснул на окне. Завтра кот снова будет сидеть на окне и смотреть на птиц.",
        "top_n": 3
      }
    }
    ```

=== "Result"

    ``` json
    {
      "n_words": 26,
      "measure": "logdice: logDice (Rychlý 2008): чем выше, тем устойчивее пара, не зависит от размера текста; пара, которая всегда стоит рядом, получает 11.7, наибольшее значение 14 - у пары, которая встречается на каждом расстоянии в окне, ниже нуля - слабая связь",
      "collocations": [
        {"left": "на", "right": "птица", "freq_left": 5, "freq_right": 3, "freq_pair": 5, "score": 12.0},
        {
          "left": "смотреть",
          "right": "птица",
          "freq_left": 2,
          "freq_right": 3,
          "freq_pair": 3,
          "score": 11.94
        },
        {
          "left": "сидеть",
          "right": "на",
          "freq_left": 2,
          "freq_right": 5,
          "freq_pair": 4,
          "score": 11.87
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
| `window` | `integer` | `5` | Greatest distance between the words of a pair, from 1 to 10; 1 - adjacent words |
| `measure` | `string` | `"logdice"` | Association measure: `logdice`, `mi`, `mi3`, `t_score`, `dice`, `log_likelihood`, `npmi`, `min_sensitivity`; `logdice` does not depend on the text size, `mi` overrates rare pairs, `mi3` and `t_score` favor frequent ones |
| `min_freq` | `integer` | `2` | Least pair frequency `freq_pair` |
| `node` | `string` | `null` | Word whose collocates are needed; not given - all pairs |
| `lemmatize` | `boolean` | `true` | Compare lemmas |
| `top_n` | `integer` | `20` | Number of pairs in the response, up to 200 |

## Result { #result }

| Field | Type | Description |
| :---- | :--- | :---------- |
| `n_words` | `integer` | Number of words in the text |
| `measure` | `string` | The measure and how to read its values |
| `collocations` | `array[object]` | Pairs by descending measure: the left word `left`, the right one `right`, their frequencies `freq_left` and `freq_right`, the pair frequency `freq_pair` and the value of the measure `score` |
| `warnings` | `array[string]` | The text is not in Russian, the `node` word is not in the text, there are no pairs with such a frequency |
