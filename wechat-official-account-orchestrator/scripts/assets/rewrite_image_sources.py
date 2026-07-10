#!/usr/bin/env python3
"""按映射表替换 HTML 中的图片 src，用于微信正文图片上传后的回填。"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def load_mapping(path: Path) -> dict[str, str]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if isinstance(data, dict) and "mapping" in data:
        data = data["mapping"]
    if not isinstance(data, dict):
        raise SystemExit("映射文件必须是 JSON 对象，或包含 mapping 对象。")
    return {str(k): str(v) for k, v in data.items()}


def rewrite(html: str, mapping: dict[str, str]) -> tuple[str, list[str]]:
    used: list[str] = []

    def repl(match: re.Match[str]) -> str:
        prefix, src, suffix = match.group(1), match.group(2), match.group(3)
        replacement = mapping.get(src) or mapping.get(Path(src).name)
        if not replacement:
            return match.group(0)
        used.append(src)
        return f'{prefix}{replacement}{suffix}'

    pattern = re.compile(r"(<img\b[^>]*\bsrc=[\"'])([^\"']+)([\"'][^>]*>)", flags=re.I)
    return pattern.sub(repl, html), used


def main() -> None:
    parser = argparse.ArgumentParser(description="按映射替换 HTML 图片 src。")
    parser.add_argument("html", help="输入 HTML。")
    parser.add_argument("--mapping", required=True, help='JSON 映射，如 {"local.png":"https://..."}。')
    parser.add_argument("--out", required=True, help="输出 HTML。")
    args = parser.parse_args()

    html_path = Path(args.html)
    mapping_path = Path(args.mapping)
    if not html_path.exists():
        raise SystemExit(f"HTML 不存在：{html_path}")
    if not mapping_path.exists():
        raise SystemExit(f"映射文件不存在：{mapping_path}")
    new_html, used = rewrite(html_path.read_text(encoding="utf-8-sig"), load_mapping(mapping_path))
    Path(args.out).write_text(new_html, encoding="utf-8")
    print(json.dumps({"ok": True, "output": args.out, "replaced": used, "count": len(used)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
