# Установка

## Требования { #requirements }

Сервер работает по stdio: клиент запускает его как команду `ruts-mcp`. Удобнее всего запускать его через `uvx` из [uv](https://docs.astral.sh/uv/getting-started/installation/): `uvx` сам скачает пакет и подходящий Python. Без uv сервер ставится в окружение с Python 3.11 или новее:

```bash
pip install ruts-mcp
```

Тогда в конфигурации клиента вместо `uvx ruts-mcp` указывается `ruts-mcp`.

## Подключение к клиенту { #clients }

### Claude Code { #claude-code }

```bash
claude mcp add ruts -- uvx ruts-mcp
```

Так сервер подключается к текущему проекту; чтобы он был доступен во всех проектах, добавьте `--scope user`. Проверить подключение можно командой `/mcp` в сессии Claude Code.

### Claude Desktop { #claude-desktop }

Добавьте сервер в файл `claude_desktop_config.json` (Settings - Developer - Edit Config): на macOS он лежит в `~/Library/Application Support/Claude/`, на Windows - в `%APPDATA%\Claude\`.

```json
{
  "mcpServers": {
    "ruts": {
      "command": "uvx",
      "args": ["ruts-mcp"]
    }
  }
}
```

После правки перезапустите Claude Desktop. Если сервер не запускается с ошибкой о команде `uvx`, укажите полный путь к ней: его выводит `which uvx` (на Windows - `where uvx`).

### Cursor { #cursor }

Добавьте ту же запись `mcpServers` в `~/.cursor/mcp.json`, чтобы сервер был доступен во всех проектах, или в `.cursor/mcp.json` проекта.

### Другие клиенты { #other-clients }

Любой клиент MCP, который запускает серверы по stdio, подключает ruTS-mcp командой `uvx ruts-mcp`.

## Словари и модель spaCy { #data }

Большинство групп и инструментов работают сразу. Трем группам и одному инструменту нужны данные, которых нет в пакете:

| Данные | Для чего | Скачивается | На диске |
| :----- | :------- | :---------: | :------: |
| Частотный словарь Ляшевской и Шарова | группа `lexical`, инструмент `keyness` со словарем | 0,5 МБ | 2 МБ |
| Словарь ударений Козиева | группа `verse` | 11 МБ | 84 МБ |
| Модель spaCy `ru_core_news_sm` | группа `syntax` | 15 МБ | 44 МБ |

Все они скачиваются одной командой:

```bash
uvx ruts-mcp download
```

Повторный запуск пропускает уже скачанное, `--force` скачивает заново. Без данных группа не падает: метрики, которым они нужны, не считаются, а предупреждение в ответе называет эту команду. Группа `lexical` и без словаря считает доли частотных полос и лексическую плотность. Что уже скачано, показывает ресурс [`ruts://data`](resources.md#resources).

Данные хранятся в каталоге данных пользователя и не пропадают при обновлении сервера:

| Система | Каталог |
| :------ | :------ |
| macOS | `~/Library/Application Support/ruts-mcp` |
| Linux | `~/.local/share/ruts-mcp` |
| Windows | `%LOCALAPPDATA%\ruts-mcp` |

Переменная `RUTS_DATA_DIR` задает другой каталог, например тот, куда словари уже скачала библиотека ruTS. Если пакет `ru_core_news_sm` установлен в окружение сервера, модель берется из него.

## Настройки { #settings }

Настройки задаются переменными окружения:

| Переменная | По умолчанию | Описание |
| :--------- | :----------: | :------- |
| `RUTS_MCP_MAX_TEXT_LENGTH` | `500000` | Наибольшее число символов текста или корпуса, который принимает инструмент |
| `RUTS_DATA_DIR` | каталог данных пользователя | Каталог словарей и модели spaCy |

В Claude Code переменная передается ключом `-e`:

```bash
claude mcp add ruts -e RUTS_MCP_MAX_TEXT_LENGTH=1000000 -- uvx ruts-mcp
```

В Claude Desktop и Cursor - полем `env` записи сервера:

```json
{
  "mcpServers": {
    "ruts": {
      "command": "uvx",
      "args": ["ruts-mcp"],
      "env": {"RUTS_MCP_MAX_TEXT_LENGTH": "1000000"}
    }
  }
}
```

Версии сервера и ruTS выводит `uvx ruts-mcp --version`.
