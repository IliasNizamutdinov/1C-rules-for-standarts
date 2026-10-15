#!/usr/bin/env python3
"""Сверяет URL официальных правил с живыми страницами ИТС.

Обычный validate.py сеть не использует. Этот скрипт нужен при обновлении правил.
Он проверяет, что страница документа открывается и содержит заголовок из каталога.
Полный текст статьи скрипт не сравнивает.
"""

from __future__ import annotations

import html
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def fetch(url: str) -> str:
    parts = urllib.parse.urlsplit(html.unescape(url))
    path = urllib.parse.quote(parts.path, safe="/%")
    safe_url = urllib.parse.urlunsplit((parts.scheme, parts.netloc, path, parts.query, ""))
    request = urllib.request.Request(safe_url, headers={"User-Agent": "Mozilla/5.0"})
    raw = urllib.request.urlopen(request, timeout=40).read()
    return raw.decode("cp1251", "replace")


def main() -> int:
    rules = []
    for path in sorted((ROOT / "rules" / "official").glob("*.json")):
        rules.extend(json.loads(path.read_text(encoding="utf-8"))["rules"])
    seen = {}
    for rule in rules:
        for source in [rule["source"], *(rule.get("related_sources") or [])]:
            seen[source["standard_id"]] = source
    errors = []
    for standard_id, source in sorted(seen.items(), key=lambda item: int(item[0])):
        page = fetch(source["url"])
        title = re.search(r"<title[^>]*>([^<]+)</title>", page)
        title_text = html.unescape(title.group(1)) if title else ""
        if source["title"] not in title_text:
            errors.append(f"{standard_id}: в заголовке нет «{source['title']}»")
            continue
        frame = re.search(r'src="(/db/content/v8std/src/[^"]+)"', page)
        if not frame:
            errors.append(f"{standard_id}: нет фрейма текста")
            continue
        try:
            body = fetch("https://its.1c.ru" + frame.group(1).split("#")[0])
        except Exception as error:
            errors.append(f"{standard_id}: текст не открылся: {error}")
            continue
        if f"#std{standard_id}" not in body and source["title"] not in body:
            errors.append(f"{standard_id}: текст фрейма не содержит маркер")
        else:
            print(f"OK {standard_id} {source['title']}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"checked {len(seen)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
