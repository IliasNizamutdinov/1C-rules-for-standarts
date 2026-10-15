#!/usr/bin/env python3
"""Собирает адаптеры Cursor и OpenCode из канонических JSON-правил.

Канон: rules/official, rules/recommendations, rules/project.
Адаптеры перезаписываются целиком. Править нужно JSON, затем запустить этот скрипт.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / "rules"
CATALOG = ROOT / "catalog" / "standards.json"
CURSOR = ROOT / ".cursor" / "rules"
OPENCODE = ROOT / "opencode" / "instructions"
DOCS = ROOT / "docs"

CHECKED = "2026-10-15"

STRENGTH = {
    "mandatory": "обязательная формулировка источника",
    "requirement": "требование источника",
    "recommended": "рекомендация источника",
    "methodological_recommendation": "официальная методическая рекомендация",
    "mixed": "в статье есть и требование, и рекомендация; см. текст правила",
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_rule_files() -> list[Path]:
    return sorted(RULES.glob("*/*.json"))


def all_rules() -> list[dict]:
    found = []
    for path in iter_rule_files():
        data = load_json(path)
        for rule in data["rules"]:
            item = dict(rule)
            item["_file"] = str(path.relative_to(ROOT))
            item["_topic"] = data.get("topic", "")
            found.append(item)
    return found


def source_lines(rule: dict) -> list[str]:
    lines = []
    source = rule.get("source")
    if source:
        lines.append(format_source(source))
    for extra in rule.get("related_sources") or []:
        lines.append("Дополнительно: " + format_source(extra))
    note = rule.get("source_note")
    if note:
        lines.append("Уточнение источника: " + note)
    basis = rule.get("basis")
    if basis:
        lines.append("Основание: " + basis)
    return lines


def format_source(source: dict) -> str:
    sections = ", ".join(source.get("sections") or [])
    section_text = f", пункты {sections}" if sections else ""
    return (
        f"[{source['title']}]({source['url']}) "
        f"({source['marker']}{section_text})"
    )


def render_rule(rule: dict) -> str:
    strength = rule.get("normative_strength")
    strength_text = STRENGTH.get(strength, strength or "не указана")
    parts = [
        f"### {rule['id']}. {rule['title']}",
        "",
        f"- Тип: `{rule['type']}`",
        f"- Сила: {strength_text}" if strength else "- Сила: не применяется, это не официальный стандарт",
    ]
    if rule["type"] == "OFFICIAL_STANDARD":
        parts.append(
            f"- Проверка источника: {rule['checked_on']}, статус `{rule['verification_status']}`"
        )
        parts.append(f"- Область платформы: {rule.get('applicability', 'не указана')}")
    elif rule["type"] == "ENGINEERING_RECOMMENDATION":
        parts.append("- К стандартам фирмы «1С» это правило не относится.")
    elif rule["type"] == "PROJECT_REQUIREMENT":
        parts.append("- Это требование конкретного проекта, не стандарт фирмы «1С».")
        parts.append(f"- Включено: {'да' if rule.get('enabled') else 'нет'}")
    if rule.get("scope"):
        parts.append("- Область: " + ", ".join(rule["scope"]))
    parts.append("")
    for line in source_lines(rule):
        parts.append(line)
        parts.append("")
    parts.append(rule.get("requirement") or rule.get("rationale") or "")
    parts.append("")
    parts.append("Что делает агент:")
    for action in rule["agent_must"]:
        parts.append(f"- {action}")
    examples = rule.get("examples") or {}
    if examples.get("violation"):
        parts.extend(["", "Пример, которого стоит избегать:", "", "```bsl", examples["violation"].rstrip(), "```"])
    if examples.get("correct"):
        parts.extend(["", "Пример, который соответствует правилу:", "", "```bsl", examples["correct"].rstrip(), "```"])
    parts.append("")
    return "\n".join(parts)


def render_body(title: str, intro: str, rules: list[dict]) -> str:
    chunks = [f"# {title}", "", intro, ""]
    chunks.extend(render_rule(rule) for rule in rules)
    return "\n".join(chunks).rstrip() + "\n"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def cursor_file(name: str, frontmatter: str, body: str) -> None:
    write(CURSOR / name, f"---\n{frontmatter.rstrip()}\n---\n\n{body}")


def assignment(rules: list[dict]) -> dict[str, list[dict]]:
    by_id = {rule["id"]: rule for rule in rules}
    groups = {
        "policy": [
            "ENG-REV-001",
            "ENG-REV-002",
            "ENG-REV-003",
            "ENG-REV-004",
            "ENG-REV-008",
            "ENG-REV-009",
            "ENG-REV-010",
            "ENG-REV-011",
            "ENG-REV-012",
        ],
        "modules": [rule["id"] for rule in rules if rule["id"].startswith("STD-MOD-") or rule["id"] == "ENG-REV-006"],
        "language": [rule["id"] for rule in rules if rule["id"].startswith("STD-LANG-")],
        "queries": [rule["id"] for rule in rules if rule["id"].startswith("STD-QRY-") or rule["id"] == "ENG-REV-005"],
        "data": [rule["id"] for rule in rules if rule["id"].startswith(("STD-DATA-", "STD-ARCH-"))],
        "security": [rule["id"] for rule in rules if rule["id"].startswith(("STD-CS-", "STD-SEC-", "ENG-REV-007"))],
        "forms": [rule["id"] for rule in rules if rule["id"].startswith("STD-UI-")],
        "project": [rule["id"] for rule in rules if rule["id"].startswith("PRJ-")],
    }
    missing = set(by_id) - {rule_id for ids in groups.values() for rule_id in ids}
    if missing:
        raise SystemExit(f"Правила без группы адаптера: {sorted(missing)}")
    return {name: [by_id[rule_id] for rule_id in ids] for name, ids in groups.items()}


def render_catalog() -> None:
    catalog = load_json(CATALOG)
    standards = catalog["standards"]
    rules = [rule for rule in all_rules() if rule["type"] == "OFFICIAL_STANDARD"]
    covered = {}
    for rule in rules:
        covered.setdefault(rule["source"]["standard_id"], []).append(rule["id"])
        for extra in rule.get("related_sources") or []:
            covered.setdefault(extra["standard_id"], []).append(rule["id"])

    folders: list[str] = []
    grouped: dict[str, list[dict]] = {}
    for item in standards:
        title = item["folder_title"]
        if title not in grouped:
            folders.append(title)
            grouped[title] = []
        grouped[title].append(item)

    lines = [
        "# Каталог стандартов фирмы «1С»",
        "",
        f"Источник оглавления: [{catalog['source']}]({catalog['source']}).",
        f"Дата снятия каталога: {catalog['retrieved_on']}.",
        "",
        catalog["note"],
        "",
        "Правило в `rules/official` создается только по статье со статусом `body_reviewed`.",
        "Статус `title_only` означает, что отдельное правило по этому документу не выводилось.",
        "",
        f"Всего документов в оглавлении: {len(standards)}.",
        f"Текст получен: {sum(1 for item in standards if item['verification_status'] == 'body_reviewed')}.",
        f"Только название: {sum(1 for item in standards if item['verification_status'] == 'title_only')}.",
        f"Документов, на которые опирается хотя бы одно правило: {len(covered)}.",
        "",
    ]
    for folder in folders:
        lines.append(f"## {folder}")
        lines.append("")
        lines.append("| ID | Документ | Проверка | Правила |")
        lines.append("| --- | --- | --- | --- |")
        for item in grouped[folder]:
            rule_ids = ", ".join(covered.get(item["id"], [])) or "—"
            lines.append(
                f"| {item['marker']} | [{item['title']}]({item['url']}) | {item['verification_status']} | {rule_ids} |"
            )
        lines.append("")
    write(DOCS / "standards-catalog.md", "\n".join(lines).rstrip() + "\n")

    reviewed_without_rules = [
        item
        for item in standards
        if item["verification_status"] == "body_reviewed" and item["id"] not in covered
    ]
    gap = [
        "# Покрытие проверенных текстов",
        "",
        "Файл показывает границу автоматической и ручной работы.",
        "Скрипт проверяет, что у официального правила есть источник.",
        "Он не проверяет, что из статьи извлечены все пункты.",
        "",
        f"Текстов прочитано: {sum(1 for item in standards if item['verification_status'] == 'body_reviewed')}.",
        f"Из них без отдельного правила в репозитории: {len(reviewed_without_rules)}.",
        "",
        "Эти статьи не пропали из каталога. По ним нельзя говорить «агент соблюдает весь документ»,",
        "пока из текста не выделено отдельное правило.",
        "",
    ]
    for item in reviewed_without_rules:
        gap.append(f"- {item['marker']} [{item['title']}]({item['url']})")
    gap.append("")
    write(DOCS / "coverage.md", "\n".join(gap))


def main() -> None:
    rules = all_rules()
    groups = assignment(rules)
    policy_intro = """\
Этот файл задает, как применять остальные правила. Он не заменяет их.

Официальные требования лежат в `rules/official` и помечены `OFFICIAL_STANDARD`.
Инженерные рекомендации лежат в `rules/recommendations` и помечены `ENGINEERING_RECOMMENDATION`.
Требования проекта подключают отдельно из `rules/project`; шаблон по умолчанию выключен.

Перед написанием или проверкой кода 1С прочитай подходящие файлы, если их еще нет в контексте:

- `.cursor/rules/10-modules.mdc` и `opencode/instructions/10-modules.md` — оформление модулей;
- `.cursor/rules/11-language.mdc` и `opencode/instructions/11-language.md` — конструкции языка;
- `.cursor/rules/20-queries.mdc` и `opencode/instructions/20-queries.md` — запросы;
- `.cursor/rules/30-data-architecture.mdc` и `opencode/instructions/30-data-architecture.md` — данные и архитектура;
- `.cursor/rules/40-client-server-security.mdc` и `opencode/instructions/40-client-server-security.md` — клиент, сервер и безопасность;
- `.cursor/rules/50-forms-applied.mdc` и `opencode/instructions/50-forms-applied.md` — формы и прикладные сценарии.

Упоминание пути само по себе не подставляет текст файла в контекст. Файл нужно прочитать.

Отчет проверки делится на четыре группы. Формулировка «нарушен стандарт 1С» допустима только для `OFFICIAL_STANDARD` с обязательной или смешанной силой и только со ссылкой на правило. Для `methodological_recommendation` пиши «официальная методическая рекомендация».
"""
    modules_intro = "Официальные правила оформления модулей и конструкций языка. Инженерные рекомендации в этом файле отмечены своим типом и не являются стандартом фирмы «1С»."
    queries_intro = "Официальные правила запросов. Правило ENG-REV-005 — инженерное усиление, а не отдельная цитата стандарта."
    data_intro = "Официальные правила записи, проведения, блокировок, регистров и размещения кода."
    security_intro = "Официальные правила клиент-серверного взаимодействия, прав и безопасного кода. ENG-REV-007 описывает асинхронный вызов и не цитирует отдельную статью про оператор Ждать."
    forms_intro = "Официальные правила сообщений, форм, печати и локализуемых строк."
    project_intro = "ШАБЛОН. Эти требования выключены и не являются стандартами фирмы «1С». Не применяй префиксы и ограничения из этого файла, пока проект не включил собственные правила."

    bodies = {
        "00-policy": render_body("Классификация правил и проверка кода", policy_intro, groups["policy"]),
        "10-modules": render_body("Оформление модулей", modules_intro, groups["modules"]),
        "11-language": render_body(
            "Конструкции встроенного языка",
            "Официальные правила конструкций встроенного языка. Методические рекомендации внутри статей отмечены своей силой и не превращаются в обязательный запрет.",
            groups["language"],
        ),
        "20-queries": render_body("Запросы", queries_intro, groups["queries"]),
        "30-data-architecture": render_body("Данные и архитектура", data_intro, groups["data"]),
        "40-client-server-security": render_body("Клиент, сервер и безопасность", security_intro, groups["security"]),
        "50-forms-applied": render_body("Формы и прикладные сценарии", forms_intro, groups["forms"]),
        "90-project-template": render_body("Шаблон требований проекта", project_intro, groups["project"]),
    }

    cursor_file(
        "00-policy.mdc",
        'description: "Классификация правил 1С, формат проверки и границы официальных стандартов"\nalwaysApply: true',
        bodies["00-policy"],
    )
    cursor_file(
        "10-modules.mdc",
        'description: "Оформление модулей 1С: структура, имена, параметры и комментарии"\nglobs: "**/*.bsl,**/*.os"\nalwaysApply: false',
        bodies["10-modules"],
    )
    cursor_file(
        "11-language.mdc",
        'description: "Конструкции встроенного языка 1С: исключения, директивы, типы, коллекции"\nglobs: "**/*.bsl,**/*.os"\nalwaysApply: false',
        bodies["11-language"],
    )
    cursor_file(
        "20-queries.mdc",
        'description: "Запросы 1С: текст запроса, виртуальные таблицы, временные таблицы, ОБЪЕДИНИТЬ, РАЗРЕШЕННЫЕ и индексы"\nalwaysApply: false',
        bodies["20-queries"],
    )
    cursor_file(
        "30-data-architecture.mdc",
        'description: "Проведение документов 1С, транзакции, блокировки, регистры, общие модули и метаданные"\nalwaysApply: false',
        bodies["30-data-architecture"],
    )
    cursor_file(
        "40-client-server-security.mdc",
        'description: "Клиент-сервер 1С, директивы формы, права, привилегированный режим, Выполнить и Вычислить, пароли"\nalwaysApply: false',
        bodies["40-client-server-security"],
    )
    cursor_file(
        "50-forms-applied.mdc",
        'description: "Формы 1С, сообщения пользователю, печать, НСтр и локализация интерфейсных строк"\nalwaysApply: false',
        bodies["50-forms-applied"],
    )
    cursor_file(
        "90-project-template.mdc",
        "alwaysApply: false",
        bodies["90-project-template"],
    )

    opencode_names = {
        "00-policy": "00-policy.md",
        "10-modules": "10-modules.md",
        "11-language": "11-language.md",
        "20-queries": "20-queries.md",
        "30-data-architecture": "30-data-architecture.md",
        "40-client-server-security": "40-client-server-security.md",
        "50-forms-applied": "50-forms-applied.md",
        "90-project-template": "90-project-template.md",
    }
    for key, filename in opencode_names.items():
        write(OPENCODE / filename, bodies[key])

    instructions = [
        "opencode/instructions/00-policy.md",
        "opencode/instructions/10-modules.md",
        "opencode/instructions/11-language.md",
        "opencode/instructions/20-queries.md",
        "opencode/instructions/30-data-architecture.md",
        "opencode/instructions/40-client-server-security.md",
        "opencode/instructions/50-forms-applied.md",
    ]
    write(
        ROOT / "opencode.json",
        json.dumps(
            {
                "$schema": "https://opencode.ai/config.json",
                "instructions": instructions,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )

    manifest = {"generated_on": CHECKED, "rules": {}}
    cursor_names = {
        "policy": ".cursor/rules/00-policy.mdc",
        "modules": ".cursor/rules/10-modules.mdc",
        "language": ".cursor/rules/11-language.mdc",
        "queries": ".cursor/rules/20-queries.mdc",
        "data": ".cursor/rules/30-data-architecture.mdc",
        "security": ".cursor/rules/40-client-server-security.mdc",
        "forms": ".cursor/rules/50-forms-applied.mdc",
        "project": ".cursor/rules/90-project-template.mdc",
    }
    opencode_by_group = {
        "policy": "opencode/instructions/00-policy.md",
        "modules": "opencode/instructions/10-modules.md",
        "language": "opencode/instructions/11-language.md",
        "queries": "opencode/instructions/20-queries.md",
        "data": "opencode/instructions/30-data-architecture.md",
        "security": "opencode/instructions/40-client-server-security.md",
        "forms": "opencode/instructions/50-forms-applied.md",
        "project": "opencode/instructions/90-project-template.md",
    }
    for group, group_rules in groups.items():
        for rule in group_rules:
            manifest["rules"][rule["id"]] = {
                "type": rule["type"],
                "cursor": cursor_names[group],
                "opencode": opencode_by_group[group],
                "canonical": rule["_file"],
                "loaded_by_default": group != "project",
            }
    write(ROOT / "catalog" / "adapter-manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    render_catalog()
    print(f"rules: {len(rules)}")
    for name, group_rules in groups.items():
        print(f"  {name}: {len(group_rules)}")


if __name__ == "__main__":
    main()
