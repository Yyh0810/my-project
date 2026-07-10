#!/usr/bin/env python3
"""扫描公众号稿件里的图片，生成素材管理清单。"""

from __future__ import annotations

import argparse
import json
import mimetypes
import re
from pathlib import Path
from urllib.parse import urlparse


IMAGE_MD = re.compile(r"!\[([^\]]*)\]\(([^ \t\r\n]+(?:\([^)]*\)[^ \t\r\n]*)?)\)")
IMAGE_HTML = re.compile(r"<img\b[^>]*\bsrc=[\"']([^\"']+)[\"'][^>]*>", re.I)
ALT_HTML = re.compile(r"\balt=[\"']([^\"']*)[\"']", re.I)


def classify(src: str) -> str:
    lower = src.strip().lower()
    parsed = urlparse(src)
    if lower.startswith("data:image/"):
        return "data-image"
    if parsed.scheme in ("http", "https"):
        if "mmbiz.qpic.cn" in parsed.netloc or "qpic.cn" in parsed.netloc:
            return "wechat-url"
        return "remote-url"
    if parsed.scheme:
        return "blocked-scheme"
    return "local"


def resolve_local(src: str, base_dir: Path) -> Path:
    path = Path(src)
    if not path.is_absolute():
        path = base_dir / path
    return path


def item(src: str, alt: str, base_dir: Path, source: str) -> dict[str, object]:
    src = src.strip()
    kind = classify(src)
    record: dict[str, object] = {
        "source": source,
        "src": src,
        "alt": alt,
        "kind": kind,
        "exists": None,
        "size_bytes": None,
        "mime": mimetypes.guess_type(src)[0] or "",
        "suggested_action": "",
    }
    if kind == "local":
        path = resolve_local(src, base_dir)
        record["path"] = str(path)
        record["exists"] = path.exists()
        if path.exists():
            record["size_bytes"] = path.stat().st_size
            record["suggested_action"] = "检查尺寸与版权；进入草稿箱前按用途上传为正文图片或封面素材。"
        else:
            record["suggested_action"] = "修正本地路径或补齐图片文件。"
    elif kind == "remote-url":
        record["suggested_action"] = "确认版权、可访问性和微信后台兼容性；必要时下载后上传到微信。"
    elif kind == "wechat-url":
        record["suggested_action"] = "可作为正文图片 URL 使用；仍需预览确认显示正常。"
    elif kind == "data-image":
        record["suggested_action"] = "不建议直接进入微信草稿；导出为文件后上传。"
    else:
        record["suggested_action"] = "阻断：不接受该图片源协议。"
    return record


def scan(text: str, base_dir: Path) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for match in IMAGE_MD.finditer(text):
        records.append(item(match.group(2), match.group(1), base_dir, "markdown"))
    for match in IMAGE_HTML.finditer(text):
        tag = match.group(0)
        alt_match = ALT_HTML.search(tag)
        alt = alt_match.group(1) if alt_match else ""
        records.append(item(match.group(1), alt, base_dir, "html"))
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description="扫描 Markdown/HTML 图片并生成公众号素材清单。")
    parser.add_argument("file", help="Markdown 或 HTML 文件。")
    parser.add_argument("--base-dir", help="相对图片路径的基准目录；默认使用文件所在目录。")
    parser.add_argument("--out", help="输出 JSON 文件；默认打印到 stdout。")
    args = parser.parse_args()

    src = Path(args.file)
    if not src.exists():
        raise SystemExit(f"文件不存在：{src}")
    base_dir = Path(args.base_dir) if args.base_dir else src.parent
    records = scan(src.read_text(encoding="utf-8-sig"), base_dir)
    summary = {
        "file": str(src),
        "base_dir": str(base_dir),
        "total": len(records),
        "blocked": sum(1 for r in records if r["kind"] == "blocked-scheme"),
        "missing_local": sum(1 for r in records if r["kind"] == "local" and r["exists"] is False),
        "records": records,
    }
    data = json.dumps(summary, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).write_text(data + "\n", encoding="utf-8")
        print(f"素材清单已生成：{args.out}")
    else:
        print(data)


if __name__ == "__main__":
    main()
