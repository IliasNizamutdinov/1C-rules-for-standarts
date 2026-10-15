# Установка правил в OpenCode

Документация, на которую опирается инструкция, проверена 2026-10-15:

- [Rules](https://opencode.ai/docs/rules/) — `AGENTS.md` и поле `instructions` в `opencode.json`.
- [Instructions (V2)](https://opencode.ai/v2/docs/instructions/) — порядок загрузки `AGENTS.md` и `instructions`.

OpenCode V2 читает `AGENTS.md` и не подставляет `CLAUDE.md` вместо него. Поле `instructions` загружает дополнительные файлы, шаблоны и URL после `AGENTS.md`. Упоминание пути внутри `AGENTS.md` само по себе файл не загружает. Поэтому правила 1С перечислены в `opencode.json`.

Удаленный URL OpenCode забирает при загрузке конфигурации с таймаутом около пяти секунд. Если сеть недоступна, файл пропускается или остается прошлая удачная копия. Для работы без сети держите файлы локально.

## 1. Что нужно заранее

- OpenCode, который понимает `AGENTS.md` и `opencode.json`.
- Проект открыт в своем корне, а не во внешней папке: иначе проектный `AGENTS.md` может не найтись.
- Не устанавливайте переменную `OPENCODE_DISABLE_PROJECT_CONFIG=1`, если нужны проектные инструкции.

## 2. Какие файлы должны лежать в проекте

- `AGENTS.md` — короткий порядок работы и напоминание проверить `instructions`.
- `opencode.json` — список загружаемых файлов. В этом репозитории других настроек нет.
- `opencode/instructions/00-policy.md`
- `opencode/instructions/10-modules.md`
- `opencode/instructions/11-language.md`
- `opencode/instructions/20-queries.md`
- `opencode/instructions/30-data-architecture.md`
- `opencode/instructions/40-client-server-security.md`
- `opencode/instructions/50-forms-applied.md`

`opencode/instructions/90-project-template.md` в список не входит.

Если в проекте уже есть `AGENTS.md` или `opencode.json`, не заменяйте их целиком.

## 3. Вариант А. Установка в один проект

Bash, если своих файлов еще нет:

```bash
git clone https://github.com/IliasNizamutdinov/1C-rules-for-standarts.git /tmp/1c-rules
cp /tmp/1c-rules/AGENTS.md ./AGENTS.md
cp /tmp/1c-rules/opencode.json ./opencode.json
mkdir -p opencode/instructions
cp /tmp/1c-rules/opencode/instructions/00-policy.md opencode/instructions/
cp /tmp/1c-rules/opencode/instructions/10-modules.md opencode/instructions/
cp /tmp/1c-rules/opencode/instructions/11-language.md opencode/instructions/
cp /tmp/1c-rules/opencode/instructions/20-queries.md opencode/instructions/
cp /tmp/1c-rules/opencode/instructions/30-data-architecture.md opencode/instructions/
cp /tmp/1c-rules/opencode/instructions/40-client-server-security.md opencode/instructions/
cp /tmp/1c-rules/opencode/instructions/50-forms-applied.md opencode/instructions/
```

PowerShell:

```powershell
git clone https://github.com/IliasNizamutdinov/1C-rules-for-standarts.git $env:TEMP\1c-rules
Copy-Item "$env:TEMP\1c-rules\AGENTS.md" .\AGENTS.md
Copy-Item "$env:TEMP\1c-rules\opencode.json" .\opencode.json
New-Item -ItemType Directory -Force -Path opencode\instructions | Out-Null
Copy-Item "$env:TEMP\1c-rules\opencode\instructions\00-policy.md" opencode\instructions\
Copy-Item "$env:TEMP\1c-rules\opencode\instructions\10-modules.md" opencode\instructions\
Copy-Item "$env:TEMP\1c-rules\opencode\instructions\11-language.md" opencode\instructions\
Copy-Item "$env:TEMP\1c-rules\opencode\instructions\20-queries.md" opencode\instructions\
Copy-Item "$env:TEMP\1c-rules\opencode\instructions\30-data-architecture.md" opencode\instructions\
Copy-Item "$env:TEMP\1c-rules\opencode\instructions\40-client-server-security.md" opencode\instructions\
Copy-Item "$env:TEMP\1c-rules\opencode\instructions\50-forms-applied.md" opencode\instructions\
```

### Уже есть AGENTS.md

Допишите в конец существующего файла раздел со ссылкой на эту инструкцию и не удаляйте прежние команды сборки. Текст правил при этом остается в `opencode/instructions`: дублировать его в `AGENTS.md` не нужно.

### Уже есть opencode.json

Откройте JSON и добавьте пути в массив `instructions`, не удаляя `provider`, `mcp` и другие ключи. Пример слияния:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "instructions": [
    "CONTRIBUTING.md",
    "opencode/instructions/00-policy.md",
    "opencode/instructions/10-modules.md",
    "opencode/instructions/11-language.md",
    "opencode/instructions/20-queries.md",
    "opencode/instructions/30-data-architecture.md",
    "opencode/instructions/40-client-server-security.md",
    "opencode/instructions/50-forms-applied.md"
  ]
}
```

Путь, которого нет на диске, OpenCode пропускает. Ошибка в JSON отключает весь файл конфигурации, поэтому после правки проверьте, что файл разбирается:

```bash
python3 -c "import json; json.load(open('opencode.json', encoding='utf-8'))"
```

PowerShell:

```powershell
python -c "import json; json.load(open('opencode.json', encoding='utf-8'))"
```

Допустимо имя `opencode.jsonc`, если им уже пользуется проект. Механизм `instructions` тот же. Не создавайте второй конфиг рядом без необходимости: смотрите, какой файл проект уже читает.

## 4. Вариант Б. Несколько проектов

### Локальная копия или подмодуль

Как и для Cursor, подмодуль хранит историю, но OpenCode ищет относительный путь от корня проекта вверх до корня репозитория. Путь `vendor/1c-rules/opencode/instructions/00-policy.md` можно записать в `instructions`, если подмодуль лежит внутри проекта. Тогда копировать markdown в каждый проект не нужно.

```json
{
  "instructions": [
    "vendor/1c-rules/opencode/instructions/00-policy.md",
    "vendor/1c-rules/opencode/instructions/10-modules.md",
    "vendor/1c-rules/opencode/instructions/11-language.md",
    "vendor/1c-rules/opencode/instructions/20-queries.md",
    "vendor/1c-rules/opencode/instructions/30-data-architecture.md",
    "vendor/1c-rules/opencode/instructions/40-client-server-security.md",
    "vendor/1c-rules/opencode/instructions/50-forms-applied.md"
  ]
}
```

Обновление: `git submodule update --remote vendor/1c-rules`. Свой `AGENTS.md` и остальные ключи `opencode.json` не перезаписываются.

Символическая ссылка на каталог `opencode/instructions` тоже работает, пока OpenCode открывает реальный файл по пути из конфигурации. На Windows без права создавать ссылки используйте подмодуль с прямыми путями или копию.

### Удаленный URL

```json
{
  "instructions": [
    "https://raw.githubusercontent.com/IliasNizamutdinov/1C-rules-for-standarts/main/opencode/instructions/00-policy.md"
  ]
}
```

Так можно подключить каждый из семи файлов. Это зависит от сети и от того, что ветка `main` доступна без авторизации. Для постоянной разработки надежнее локальные файлы: их видно в ревью и они не меняются посередине сеанса из-за чужого коммита.

Глобальный файл `~/.config/opencode/AGENTS.md` лучше оставить для личных предпочтений. Общие правила 1С кладите в проект, чтобы их видела вся команда.

## 5. Проверка загрузки

1. Запустите OpenCode в корне проекта.
2. Начните новый сеанс. Уже открытый сеанс V2 подхватывает правку `AGENTS.md` перед следующим запросом, но вложенные файлы после первой загрузки сами могут не обновиться: для них нужен новый сеанс.
3. Спросите: «Перечисли файлы инструкций, которые загружены из opencode.json, и назови тип правила STD-QRY-003».
4. В ответе должны быть семь путей `opencode/instructions/*.md` из `opencode.json` и тип `OFFICIAL_STANDARD` у `STD-QRY-003`. Шаблон `90-project-template.md` в этот список не входит.

Если модель говорит, что видит только `AGENTS.md`, массив `instructions` пуст, JSON не разобран или сеанс запущен не из корня проекта.

## 6. Пример запроса

```text
Добавь проведение документа РеализацияТоваров по регистру ОстаткиТоваров.
Соблюдай загруженные правила 1С.
В конце перечисли идентификаторы примененных правил и отдели официальные требования от рекомендаций.
```

Проверка результата: в проведении нет `Записать()` набора без причины из `STD-DATA-006`, есть проверка `ОбменДанными.Загрузка` в записи, а рекомендации `ENG-*` не названы стандартом фирмы «1С».

## 7. Обновление

Повторите копирование семи markdown-файлов и при необходимости обновите пути в `instructions`. Свои ключи `opencode.json` и текст собственного `AGENTS.md` сохраните. Шаблон `90-project-template.md` обновляйте только если вы его не редактировали.

После обновления откройте новый сеанс.

## 8. Удаление

Уберите семь путей из `instructions`. Затем удалите скопированные файлы, если они больше не используются. Существующий `AGENTS.md` правьте точечно: удалите добавленный раздел про 1С и оставьте прежние инструкции проекта.

PowerShell для файлов набора:

```powershell
Remove-Item opencode\instructions\00-policy.md, opencode\instructions\10-modules.md, opencode\instructions\11-language.md, opencode\instructions\20-queries.md, opencode\instructions\30-data-architecture.md, opencode\instructions\40-client-server-security.md, opencode\instructions\50-forms-applied.md
```

Не удаляйте `opencode.json`, если в нем остались настройки модели, MCP или другие инструкции.

## 9. Типичные сбои

| Что видно | Что проверить |
| --- | --- |
| Правила не меняют ответы | Новый сеанс открыт в корне; `instructions` содержит существующие пути |
| Загружается старая редакция | Сеанс начат до обновления файлов |
| Удаленный URL пустой | Сеть, таймаут 5 секунд, путь `raw.githubusercontent.com` и ветка `main` |
| Пропали настройки модели | `opencode.json` был заменен целиком. Верните свои ключи из Git |
| Применился выключенный шаблон | В `instructions` добавлен `90-project-template.md` |
| V2 не видит старый `CLAUDE.md` | Перенесите нужный текст в `AGENTS.md`. V2 не использует `CLAUDE.md` как замену |
