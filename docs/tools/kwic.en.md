# KWIC concordance

``` {.python .signature}
kwic(keyword, text="", path=null, window=5, by_lemma=false, limit=50)
```

All occurrences of a word or a phrase with the context on the left and on the right - a concordance the agent quotes the text by and sees how a word is used. Words are compared ignoring case and the letter ё, with `by_lemma` - by lemmas: «окно» finds «окне» and «окна». A phrase does not run across the end of a sentence. How occurrences are found is described on the ruTS page [KWIC concordance](https://sergeyshk.github.io/ruTS/en/corpus/kwic/).

The lines are limited by the `limit` parameter and by the size of the response - about 40,000 characters of context; if not all occurrences are shown, a warning tells how many there are.

Errors - [those common to the tools](index.md#errors) and a keyword without words.

=== "Call"

    ``` json
    {
      "name": "kwic",
      "arguments": {
        "keyword": "окно",
        "text": "Кот сидел на окне и смотрел на птиц. Птицы улетели, и кот уснул на окне. Завтра кот снова будет сидеть на окне и смотреть на птиц.",
        "window": 3,
        "by_lemma": true
      }
    }
    ```

=== "Result"

    ``` json
    {
      "n_matches": 3,
      "matches": [
        {"left": "Кот сидел на", "keyword": "окне", "right": "и смотрел на"},
        {"left": "кот уснул на", "keyword": "окне", "right": ". Завтра кот снова"},
        {"left": "будет сидеть на", "keyword": "окне", "right": "и смотреть на"}
      ],
      "warnings": []
    }
    ```

## Parameters

| Parameter | Type | Default | Description |
| :-------- | :--- | :------ | :---------- |
| `keyword` | `string` | - | Word or phrase |
| `text` | `string` | `""` | Text |
| `path` | `string` | `null` | Absolute path to a file with the text instead of `text` |
| `window` | `integer` | `5` | Number of context words on each side, up to 50 |
| `by_lemma` | `boolean` | `false` | Find all forms of the word by its lemma |
| `limit` | `integer` | `50` | Greatest number of lines in the response, up to 500 |

## Result { #result }

| Field | Type | Description |
| :---- | :--- | :---------- |
| `n_matches` | `integer` | Number of occurrences |
| `matches` | `array[object]` | Lines in the order of the text: the left context `left`, the occurrence `keyword` as written in the text and the right context `right` |
| `warnings` | `array[string]` | The text is not in Russian, not all occurrences are shown, there are no occurrences of a word form |
