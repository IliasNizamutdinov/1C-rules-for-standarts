#!/usr/bin/env python3
"""Проверяет структуру правил и совпадение адаптеров с каноном.

Скрипт не доказывает, что формулировка верно передает весь текст стандарта.
Он ловит пропущенный тип, битую ссылку на каталог и расхождение адаптеров.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from render_adapters import all_rules, load_json  # noqa: E402

REQUIRED_OFFICIAL = [
    "id",
    "type",
    "title",
    "normative_strength",
    "requirement",
    "agent_must",
    "scope",
    "applicability",
    "source",
    "checked_on",
    "verification_status",
]
REQUIRED_ENGINEERING = ["id", "type", "title", "rationale", "agent_must", "scope", "basis"]
REQUIRED_PROJECT = ["id", "type", "title", "requirement", "agent_must", "scope", "basis", "enabled"]
STRENGTHS = {
    "mandatory",
    "requirement",
    "recommended",
    "methodological_recommendation",
    "mixed",
}
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def check_rules(errors: list[str]) -> list[dict]:
    rules = all_rules()
    ids = [rule["id"] for rule in rules]
    if len(ids) != len(set(ids)):
        fail(errors, "Есть повторяющиеся идентификаторы правил")
    catalog = load_json(ROOT / "catalog" / "standards.json")
    known = {item["id"]: item for item in catalog["standards"]}
    if len(known) != len(catalog["standards"]):
        fail(errors, "В каталоге повторяются идентификаторы стандартов")
    for rule in rules:
        if rule["type"] == "OFFICIAL_STANDARD":
            check_official(rule, known, errors)
        elif rule["type"] == "ENGINEERING_RECOMMENDATION":
            check_engineering(rule, errors)
        elif rule["type"] == "PROJECT_REQUIREMENT":
            check_project(rule, errors)
        else:
            fail(errors, f"{rule['id']}: неизвестный тип {rule['type']}")
    return rules


def check_official(rule: dict, known: dict, errors: list[str]) -> None:
    for field in REQUIRED_OFFICIAL:
        if field not in rule or rule[field] in ("", None, [], {}):
            fail(errors, f"{rule['id']}: нет поля {field}")
    if rule.get("normative_strength") not in STRENGTHS:
        fail(errors, f"{rule['id']}: неизвестная сила нормы")
    if rule.get("verification_status") != "body_reviewed":
        fail(errors, f"{rule['id']}: официальное правило без статуса body_reviewed")
    if not DATE.match(rule.get("checked_on", "")):
        fail(errors, f"{rule['id']}: дата проверки не в формате ГГГГ-ММ-ДД")
    check_source(rule["id"], rule.get("source"), known, errors)
    for extra in rule.get("related_sources") or []:
        check_source(rule["id"], extra, known, errors)
    if "фирма «1С» требует" in rule.get("requirement", "") and rule.get("normative_strength") == "methodological_recommendation":
        fail(errors, f"{rule['id']}: методическая рекомендация сформулирована как обязательное требование фирмы")


def check_source(rule_id: str, source: dict | None, known: dict, errors: list[str]) -> None:
    if not source:
        fail(errors, f"{rule_id}: нет источника")
        return
    for field in ("standard_id", "title", "marker", "url"):
        if not source.get(field):
            fail(errors, f"{rule_id}: у источника нет {field}")
    standard = known.get(source.get("standard_id"))
    if standard is None:
        fail(errors, f"{rule_id}: стандарт {source.get('standard_id')} отсутствует в каталоге")
        return
    if standard["verification_status"] != "body_reviewed":
        fail(errors, f"{rule_id}: стандарт {source.get('standard_id')} не был прочитан")
    if standard["title"] != source.get("title"):
        fail(errors, f"{rule_id}: название источника не совпадает с каталогом")
    if source.get("url") != standard["url"]:
        fail(errors, f"{rule_id}: URL не совпадает с каталогом")
    if source.get("marker") != standard["marker"]:
        fail(errors, f"{rule_id}: маркер не совпадает с каталогом")


def check_engineering(rule: dict, errors: list[str]) -> None:
    for field in REQUIRED_ENGINEERING:
        if not rule.get(field):
            fail(errors, f"{rule['id']}: нет поля {field}")
    if "source" in rule:
        fail(errors, f"{rule['id']}: у инженерной рекомендации не должно быть поля source официального стандарта")
    for field in ("title", "rationale", "basis"):
        if "нарушен стандарт 1С" in rule.get(field, ""):
            fail(errors, f"{rule['id']}: рекомендация говорит о нарушении стандарта")


def check_project(rule: dict, errors: list[str]) -> None:
    for field in REQUIRED_PROJECT:
        if field not in rule:
            fail(errors, f"{rule['id']}: нет поля {field}")
    if rule.get("enabled") is not False:
        fail(errors, f"{rule['id']}: шаблон проекта должен быть выключен")


def check_adapters(rules: list[dict], errors: list[str]) -> None:
    manifest = load_json(ROOT / "catalog" / "adapter-manifest.json")
    mapped = manifest["rules"]
    if set(mapped) != {rule["id"] for rule in rules}:
        fail(errors, "Манифест адаптеров не совпадает с набором правил")
    config = load_json(ROOT / "opencode.json")
    instructions = config.get("instructions") or []
    if "opencode/instructions/90-project-template.md" in instructions:
        fail(errors, "Шаблон проекта подключен в opencode.json")
    for relative in instructions:
        if not (ROOT / relative).is_file():
            fail(errors, f"OpenCode не найдет файл {relative}")
    for rule in rules:
        entry = mapped[rule["id"]]
        if entry["type"] != rule["type"]:
            fail(errors, f"{rule['id']}: тип в манифесте другой")
        for key in ("cursor", "opencode"):
            path = ROOT / entry[key]
            if not path.is_file():
                fail(errors, f"{rule['id']}: нет адаптера {entry[key]}")
                continue
            text = path.read_text(encoding="utf-8")
            if rule["id"] not in text:
                fail(errors, f"{rule['id']}: идентификатор отсутствует в {entry[key]}")
            if f"`{rule['type']}`" not in text:
                fail(errors, f"{rule['id']}: тип не сохранен в {entry[key]}")
            payload = rule.get("requirement") or rule.get("rationale")
            if payload not in text:
                fail(errors, f"{rule['id']}: формулировка отсутствует в {entry[key]}")
        if rule["type"] == "OFFICIAL_STANDARD" and rule["source"]["url"] not in (ROOT / entry["cursor"]).read_text(encoding="utf-8"):
            fail(errors, f"{rule['id']}: в адаптере Cursor нет URL источника")
        if rule["type"] == "PROJECT_REQUIREMENT" and entry["loaded_by_default"]:
            fail(errors, f"{rule['id']}: шаблон проекта загружается по умолчанию")
    policy = (ROOT / ".cursor" / "rules" / "00-policy.mdc").read_text(encoding="utf-8")
    if not policy.startswith("---\n") or "alwaysApply: true" not in policy.split("---", 2)[1]:
        fail(errors, "Политика Cursor не помечена alwaysApply: true")
    manual = (ROOT / ".cursor" / "rules" / "90-project-template.mdc").read_text(encoding="utf-8")
    header = manual.split("---", 2)[1]
    if "description:" in header or "globs:" in header or "alwaysApply: false" not in header:
        fail(errors, "Шаблон проекта в Cursor должен подключаться только вручную")
    for path in (ROOT / ".cursor" / "rules").glob("*.mdc"):
        text = path.read_text(encoding="utf-8")
        if not text.startswith("---\n"):
            fail(errors, f"{path.name}: нет фронтматера MDC")
        if "alwaysApply:" not in text.split("---", 2)[1]:
            fail(errors, f"{path.name}: нет alwaysApply")
    if not (ROOT / "AGENTS.md").is_file():
        fail(errors, "Нет AGENTS.md")
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    if "opencode.json" not in agents or "instructions" not in agents:
        fail(errors, "AGENTS.md не объясняет, что OpenCode загружает instructions")


def check_secrets(errors: list[str]) -> None:
    private_marker = "BEGIN " + "PRIVATE KEY"
    pattern = re.compile(rf"{private_marker}|AKIA[0-9A-Z]{{16}}|ghp_[A-Za-z0-9]{{20}}")
    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts or path.name == "validate.py":
            continue
        if path.suffix.lower() not in {".md", ".json", ".mdc", ".py", ".yml", ".yaml", ".txt"}:
            continue
        if pattern.search(path.read_text(encoding="utf-8", errors="ignore")):
            fail(errors, f"Похоже на секрет: {path.relative_to(ROOT)}")


def check_regeneration(errors: list[str]) -> None:
    import subprocess

    before = snapshot_adapters()
    subprocess.run([sys.executable, str(ROOT / "scripts" / "render_adapters.py")], check=True, cwd=ROOT)
    after = snapshot_adapters()
    if before != after:
        fail(errors, "Адаптеры не совпадают с результатом scripts/render_adapters.py. Запустите скрипт и закоммитьте результат.")


def snapshot_adapters() -> dict[str, str]:
    paths = list((ROOT / ".cursor" / "rules").glob("*.mdc"))
    paths += list((ROOT / "opencode" / "instructions").glob("*.md"))
    paths += [
        ROOT / "opencode.json",
        ROOT / "catalog" / "adapter-manifest.json",
        ROOT / "docs" / "standards-catalog.md",
        ROOT / "docs" / "coverage.md",
    ]
    return {str(path.relative_to(ROOT)): path.read_text(encoding="utf-8") for path in paths}


def main() -> int:
    errors: list[str] = []
    rules = check_rules(errors)
    check_adapters(rules, errors)
    check_secrets(errors)
    if errors:
        print("\n".join(errors))
        return 1
    check_regeneration(errors)
    if errors:
        print("\n".join(errors))
        return 1
    official = sum(1 for rule in rules if rule["type"] == "OFFICIAL_STANDARD")
    engineering = sum(1 for rule in rules if rule["type"] == "ENGINEERING_RECOMMENDATION")
    project = sum(1 for rule in rules if rule["type"] == "PROJECT_REQUIREMENT")
    print(f"OK official={official} engineering={engineering} project={project}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
