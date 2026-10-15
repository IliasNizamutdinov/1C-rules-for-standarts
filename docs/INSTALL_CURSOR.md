# Установка правил в Cursor

Документация механизма, на которую опирается инструкция: [Rules](https://cursor.com/docs/rules). Проверено 2026-10-15.

Cursor читает правила проекта из `.cursor/rules/*.mdc`. Обычный `.md` в этой папке не считается правилом: у него нет полей `description`, `globs` и `alwaysApply`.

## 1. Что нужно заранее

- Cursor с поддержкой Project Rules.
- Корень проекта открыт как workspace. Правила ищутся только в `.cursor/rules` корня, а не во вложенных папках.
- Git, если правила ставят копией репозитория или подмодулем.

Правила влияют на Agent. Они не меняют Tab и не подставляются в Inline Edit.

## 2. Какие файлы должны появиться в проекте

Обязательный минимум:

| Файл | Когда попадает в контекст |
| --- | --- |
| `.cursor/rules/00-policy.mdc` | Каждый чат Agent: `alwaysApply: true` |
| `.cursor/rules/10-modules.mdc` | Когда в контексте есть `*.bsl` или `*.os` |
| `.cursor/rules/11-language.mdc` | Когда в контексте есть `*.bsl` или `*.os` |
| `.cursor/rules/20-queries.mdc` | Когда Agent считает описание задачи запросом |
| `.cursor/rules/30-data-architecture.mdc` | Когда речь о проведении, транзакциях, регистрах, общих модулях |
| `.cursor/rules/40-client-server-security.mdc` | Когда речь о клиенте, сервере, правах и безопасном коде |
| `.cursor/rules/50-forms-applied.mdc` | Когда речь о формах, сообщениях, печати, `НСтр` |

Файл `.cursor/rules/90-project-template.mdc` в чат сам не попадает. Его подключают через `@90-project-template`, и только после замены шаблона на требования проекта.

Канонические JSON из `rules/` сами по себе Cursor не загружает. Они нужны, чтобы пересобрать `.mdc` и проверить, что текст не разъехался.

## 3. Вариант А. Правила внутри одного проекта

Подходит, если репозиторий конфигурации должен хранить правила рядом с кодом.

Bash:

```bash
git clone https://github.com/IliasNizamutdinov/1C-rules-for-standarts.git /tmp/1c-rules
mkdir -p .cursor/rules
cp /tmp/1c-rules/.cursor/rules/*.mdc .cursor/rules/
```

PowerShell:

```powershell
git clone https://github.com/IliasNizamutdinov/1C-rules-for-standarts.git $env:TEMP\1c-rules
New-Item -ItemType Directory -Force -Path .cursor\rules | Out-Null
Copy-Item "$env:TEMP\1c-rules\.cursor\rules\*.mdc" .cursor\rules\
```

Если в проекте уже есть свои `.mdc`, копирование с заменой затрет файл с тем же именем. Сначала посмотрите `git status` и не заменяйте чужие правила. Файлы этого набора названы с числовым префиксом `00`–`90`, чтобы реже совпасть с существующими именами.

Закоммитьте `.cursor/rules` в репозиторий проекта. Тогда правила получат все, кто клонирует проект.

## 4. Вариант Б. Один набор на несколько проектов

### Подмодуль

Общий каталог обновляется отдельным коммитом подмодуля. История правил видна. Недостаток: разработчику нужно уметь обновлять submodule, а Cursor не читает `.cursor/rules` из вложенной папки подмодуля. Поэтому после обновления подмодуля файлы все равно копируют или связывают в корень.

```bash
git submodule add https://github.com/IliasNizamutdinov/1C-rules-for-standarts.git vendor/1c-rules
mkdir -p .cursor/rules
ln -s ../../vendor/1c-rules/.cursor/rules/00-policy.mdc .cursor/rules/00-policy.mdc
```

Повторите `ln -s` для остальных `.mdc`. В Windows для символической ссылки нужны права на них; иначе используйте копирование из варианта А.

### Копия без подмодуля

Проще для команды, которая не работает с submodule. Обновление — повторное копирование. Локальные правки `.mdc` при следующем копировании пропадут, поэтому свои требования храните в отдельном файле, например `.cursor/rules/95-acme.mdc`, и не перезаписывайте его из этого репозитория.

### Плагин Cursor

По документации Cursor правила из чужого GitHub-репозитория сами не подхватываются. Их можно доставить плагином через marketplace, если у репозитория есть описание плагина. Этот проект такой пакет не публикует. Для установки используйте копирование или подмодуль.

## 5. Проверка, что Cursor видит правила

1. Перезапустите чат Agent, чтобы он заново прочитал правила.
2. Откройте Customize → Rules. В списке проекта должны быть файлы из `.cursor/rules`.
3. У `00-policy` тип Always Apply.
4. У `10-modules` и `11-language` тип Apply to Specific Files и шаблон `**/*.bsl,**/*.os`.
5. У `20-queries`, `30-data-architecture`, `40-client-server-security`, `50-forms-applied` тип Apply Intelligently.
6. У `90-project-template` тип Apply Manually. В редакторе правила не должно быть `description` и `globs`.

Если интерфейс показывает другой тип, откройте сам `.mdc`: для ручного правила фронтматер состоит только из `alwaysApply: false`.

## 6. Пример запроса

Откройте модуль с расширением `.bsl` и отправьте Agent:

```text
Проверь процедуру проведения по правилам 1С.
Раздели замечания на официальные стандарты, методические рекомендации,
инженерные рекомендации и вопросы без источника.
Для каждого замечания укажи идентификатор правила.
```

Ожидание: в ответе есть идентификаторы вида `STD-...` или явная оговорка, что источник не подтвержден. Фразы «нарушен стандарт 1С» без идентификатора и ссылки быть не должно.

## 7. Как понять, что ответ опирается на правила

- Есть идентификатор из `catalog/adapter-manifest.json`.
- У официального замечания есть ссылка `https://its.1c.ru/db/v8std/content/<номер>/hdoc`.
- Рекомендация `ENG-...` названа рекомендацией.
- Шаблон `PRJ-TPL-001` не требует префикс расширения, пока вы сами не упомянули `@90-project-template` и не включили правило.

Если идентификаторов нет, откройте новый чат, убедитесь, что workspace — корень с `.cursor/rules`, и повторите запрос. Для задачи без открытого `.bsl` Agent может не подключить `10-modules.mdc` и `11-language.mdc` по шаблону. Тогда напишите: «Прочитай `.cursor/rules/10-modules.mdc` и `.cursor/rules/11-language.mdc`». Ссылка в другом правиле не вставляет текст файла сама.

## 8. Обновление

Bash:

```bash
git -C /tmp/1c-rules pull
cp /tmp/1c-rules/.cursor/rules/00-policy.mdc .cursor/rules/
cp /tmp/1c-rules/.cursor/rules/10-modules.mdc .cursor/rules/
cp /tmp/1c-rules/.cursor/rules/11-language.mdc .cursor/rules/
cp /tmp/1c-rules/.cursor/rules/20-queries.mdc .cursor/rules/
cp /tmp/1c-rules/.cursor/rules/30-data-architecture.mdc .cursor/rules/
cp /tmp/1c-rules/.cursor/rules/40-client-server-security.mdc .cursor/rules/
cp /tmp/1c-rules/.cursor/rules/50-forms-applied.mdc .cursor/rules/
cp /tmp/1c-rules/.cursor/rules/90-project-template.mdc .cursor/rules/
```

Не копируйте поверх `.cursor/rules/95-*.mdc` и других собственных файлов. Если свой файл назван как файл набора, переименуйте его до обновления.

Подмодуль:

```bash
git submodule update --remote vendor/1c-rules
```

После обновления откройте новый чат Agent.

## 9. Удаление

Удалите только файлы этого набора:

```bash
rm .cursor/rules/00-policy.mdc \
   .cursor/rules/10-modules.mdc \
   .cursor/rules/11-language.mdc \
   .cursor/rules/20-queries.mdc \
   .cursor/rules/30-data-architecture.mdc \
   .cursor/rules/40-client-server-security.mdc \
   .cursor/rules/50-forms-applied.mdc \
   .cursor/rules/90-project-template.mdc
```

PowerShell:

```powershell
Remove-Item .cursor\rules\00-policy.mdc, .cursor\rules\10-modules.mdc, .cursor\rules\11-language.mdc, .cursor\rules\20-queries.mdc, .cursor\rules\30-data-architecture.mdc, .cursor\rules\40-client-server-security.mdc, .cursor\rules\50-forms-applied.mdc, .cursor\rules\90-project-template.mdc
```

Чужие правила, исходники конфигурации и `.cursor/rules`, которых нет в списке, не трогайте. Каталог `rules/` в проекте конфигурации удаляйте только если вы копировали и его.

## 10. Если правила не работают

| Что видно | Что проверить |
| --- | --- |
| В Rules пусто | Папка `.cursor/rules` лежит в корне workspace, файлы имеют расширение `.mdc` |
| Правило есть, но помечено как обычный markdown | Файл начинается с `---` и содержит `alwaysApply` |
| Запросы не проверяются | В чате нет темы запроса, Agent не выбрал `20-queries.mdc`. Назовите запрос явно или попросите прочитать файл |
| Применяется чужой префикс метаданных | В контекст попал `90-project-template.mdc`. Не упоминайте его, пока шаблон не заменен |
| После обновления старое поведение | Закройте прежний чат. Уже начатый чат хранит прежний текст правил |
