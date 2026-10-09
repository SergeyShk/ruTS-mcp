<p align="center">
  <img src="https://raw.githubusercontent.com/SergeyShk/ruTS-mcp/master/docs/img/ruts-mcp.png" alt="ruTS-mcp" width="480">
</p>

<h1 align="center">ruTS-mcp</h1>

<p align="center">
  <b>MCP-сервер для <a href="https://github.com/SergeyShk/ruTS">ruTS</a></b> - статистики русского текста как инструменты для LLM-агентов
</p>

<p align="center">
  <a href="https://sergeyshk.github.io/ruTS-mcp/">Документация</a> ·
  <a href="https://pypi.org/project/ruts-mcp/">PyPI</a> ·
  <a href="https://github.com/SergeyShk/ruTS-mcp/blob/master/README.en.md">English</a>
</p>

<p align="center">
  <a href="https://pypi.org/project/ruts-mcp/"><img src="https://img.shields.io/pypi/v/ruts-mcp?logo=pypi&logoColor=FFE873" alt="Версия"></a>
  <a href="https://pypi.org/project/ruts-mcp/"><img src="https://img.shields.io/pypi/pyversions/ruts-mcp.svg?logo=python&logoColor=FFE873" alt="Поддерживаемые версии Python"></a>
  <a href="https://github.com/SergeyShk/ruTS-mcp/actions/workflows/ci.yml"><img src="https://github.com/SergeyShk/ruTS-mcp/actions/workflows/ci.yml/badge.svg" alt="Сборка"></a>
  <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="Ruff"></a>
  <a href="https://github.com/SergeyShk/ruTS-mcp/blob/master/LICENSE.txt"><img src="https://img.shields.io/badge/license-MIT-green.svg" alt="Лицензия"></a>
</p>

---

**ruTS-mcp** дает LLM-агенту инструменты библиотеки [ruTS](https://github.com/SergeyShk/ruTS), чтобы измерить русский текст, а не оценивать его на глаз. Каждое значение приходит вместе с описанием, прочтением по шкале, если она есть, и предупреждениями, когда значение неустойчиво или не имеет смысла для текста.

* **[`analyze_text`](https://sergeyshk.github.io/ruTS-mcp/tools/#analyze_text)** - статистики текста по группам: базовые, удобочитаемость с классом и возрастом читателя, лексическое разнообразие, морфология, фоностатистики, связность, стиль и канцелярит, лексическая сложность, стих, синтаксис
* **[`kwic`](https://sergeyshk.github.io/ruTS-mcp/tools/#kwic)** - вхождения слова или словосочетания с контекстом
* **[`collocations`](https://sergeyshk.github.io/ruTS-mcp/tools/#collocations)** - устойчивые сочетания и сочетаемость слова
* **[`dispersion`](https://sergeyshk.github.io/ruTS-mcp/tools/#dispersion)** - насколько равномерно слова распределены по тексту
* **[`keyness`](https://sergeyshk.github.io/ruTS-mcp/tools/#keyness)** - ключевые слова относительно русского языка или другого текста
* **[`compare_texts`](https://sergeyshk.github.io/ruTS-mcp/tools/#compare_texts)** - чем различаются два корпуса текстов по признакам стиля
* **[Ресурсы и промпты](https://sergeyshk.github.io/ruTS-mcp/resources/)** - шкалы удобочитаемости и нормы стиля, готовые разборы: удобочитаемость, канцелярит, стихотворение, SEO-проверка, сравнение двух текстов

## Установка

Сервер запускается через `uvx` из [uv](https://docs.astral.sh/uv/getting-started/installation/), который сам скачает пакет и Python. Подключение к Claude Code:

```bash
claude mcp add ruts -- uvx ruts-mcp
```

Для групп `lexical`, `verse` и `syntax` нужны словари и модель spaCy, их скачивает одна команда:

```bash
uvx ruts-mcp download
```

Подключение к Claude Desktop, Cursor и другим клиентам и настройки - в [документации](https://sergeyshk.github.io/ruTS-mcp/installation/).

## Лицензия

[MIT](https://github.com/SergeyShk/ruTS-mcp/blob/master/LICENSE.txt). Словари, которые скачивает `ruts-mcp download`, распространяются на условиях их авторов: [частотный словарь](http://dict.ruslang.ru/freq.php) Ляшевской и Шарова, [словарь ударений](https://github.com/Koziev/NLP_Datasets) Козиева (CC0), [модель spaCy](https://github.com/explosion/spacy-models) (MIT).
