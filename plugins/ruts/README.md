# ruTS

Плагин дает Claude инструменты MCP-сервера [ruTS-mcp](https://github.com/SergeyShk/ruTS-mcp), чтобы измерять русский текст, а не оценивать его на глаз: удобочитаемость с классом и возрастом читателя, канцелярит, SEO-метрики, метр и рифму стихотворения, лексическое разнообразие, морфологию, синтаксис, ключевые слова, конкорданс, коллокации и сравнение текстов по стилю. Скилл `ruts` подсказывает Claude, какой инструмент вызвать под задачу и как читать ответ, и содержит готовые разборы: удобочитаемость, канцелярит, стихотворение, SEO-проверка, сравнение двух текстов.

## Что запускает плагин

- MCP-сервер `ruts` командой `uvx ruts-mcp` с версией, закрепленной в `.mcp.json`. Нужен [uv](https://docs.astral.sh/uv/getting-started/installation/): при первом запуске он скачивает пакет `ruts-mcp` и его зависимости с PyPI.
- Сервер работает в Claude Code и в Cowork на компьютере пользователя. В чате claude.ai и Claude Desktop плагин дает только скилл, а сервер в Claude Desktop подключается вручную, как описано в [документации](https://sergeyshk.github.io/ruTS-mcp/installation/#clients).
- Сервер считает статистики локально и никуда не отправляет тексты.
- Группам `lexical`, `verse` и `syntax` нужны словари и модель spaCy. Их скачивает команда `uvx ruts-mcp download` - только когда ее запускает пользователь: частотный словарь с dict.ruslang.ru, словарь ударений и модель spaCy с GitHub.

## Установка в Claude Code

```
/plugin marketplace add SergeyShk/ruTS-mcp
/plugin install ruts@ruts-mcp
```

Документация: https://sergeyshk.github.io/ruTS-mcp/. Лицензия MIT.

## In English

The plugin gives Claude the tools of the [ruTS-mcp](https://github.com/SergeyShk/ruTS-mcp) server for measuring Russian texts: readability with school grade and reader age, officialese, SEO metrics, verse meter and rhyme, lexical diversity, morphology, syntax, keywords, concordance, collocations and comparison of texts by style. The `ruts` skill tells Claude which tool to call for a task and how to read the result.

The plugin runs the server with `uvx ruts-mcp` at the version pinned in `.mcp.json`; uv downloads the package and its dependencies from PyPI on first start. The server runs in Claude Code and in Cowork on the user's computer; in claude.ai and Claude Desktop chat the plugin gives only the skill, and in Claude Desktop the server is connected manually as the [documentation](https://sergeyshk.github.io/ruTS-mcp/en/installation/#clients) describes. The server computes everything locally and sends texts nowhere. Dictionaries and the spaCy model for the `lexical`, `verse` and `syntax` groups are downloaded only when the user runs `uvx ruts-mcp download`: from dict.ruslang.ru and GitHub.
