#!/usr/bin/env python3
"""公众号稿件进入排版/草稿箱前的轻量预检。"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


PLACEHOLDER_PATTERNS = [
    r"TODO",
    r"placeholder",
    r"待补充",
    r"待确认",
    r"这里补",
    r"xxx+",
]


def strip_frontmatter(text: str) -> tuple[str, dict[str, str]]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return text, {}
    meta: dict[str, str] = {}
    end = None
    for idx in range(1, min(len(lines), 80)):
        if lines[idx].strip() == "---":
            end = idx
            break
        match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", lines[idx])
        if match:
            meta[match.group(1).lower()] = match.group(2).strip().strip('"').strip("'")
    if end is None:
        return text, {}
    return "\n".join(lines[end + 1 :]), meta


def markdown_images(text: str) -> list[str]:
    return re.findall(r"!\[[^\]]*\]\(([^ \t\r\n]+(?:\([^)]*\)[^ \t\r\n]*)?)\)", text)


def html_images(text: str) -> list[str]:
    return re.findall(r"<img\b[^>]*\bsrc=[\"']([^\"']+)[\"'][^>]*>", text, flags=re.I)


def count_words(text: str) -> int:
    chinese = len(re.findall(r"[\u4e00-\u9fff]", text))
    latin = len(re.findall(r"\b[A-Za-z0-9_+-]+\b", text))
    return chinese + latin


def score(base: int, issues: list[str]) -> int:
    return max(0, min(5, base - len(issues)))


def check_file(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8-sig")
    body, meta = strip_frontmatter(text)
    is_html = path.suffix.lower() in {".html", ".htm"} or "<html" in text.lower()
    title = meta.get("title") or ""
    if not title:
        h1 = re.search(r"^#\s+(.+)$", body, flags=re.M)
        if h1:
            title = h1.group(1).strip()
        else:
            html_title = re.search(r"<title>(.*?)</title>", text, flags=re.I | re.S)
            if html_title:
                title = re.sub(r"\s+", " ", html_title.group(1)).strip()

    issues: list[str] = []
    warnings: list[str] = []
    if not title:
        issues.append("缺少标题。")
    if not is_html and not meta.get("digest"):
        warnings.append("Markdown 缺少 digest 摘要元数据。")
    if not is_html and not meta.get("author"):
        warnings.append("Markdown 缺少 author 作者元数据。")
    for pattern in PLACEHOLDER_PATTERNS:
        if re.search(pattern, text, flags=re.I):
            issues.append(f"存在占位或待确认内容：{pattern}")
    if re.search(r"(javascript|vbscript):", text, flags=re.I):
        issues.append("存在危险链接协议。")

    images = html_images(text) if is_html else markdown_images(text)
    local_missing: list[str] = []
    for src in images:
        if re.match(r"^[a-zA-Z]+:", src) or src.startswith("data:image/"):
            continue
        img = Path(src)
        if not img.is_absolute():
            img = path.parent / img
        if not img.exists():
            local_missing.append(src)
    if local_missing:
        issues.append(f"本地图片缺失：{', '.join(local_missing[:5])}")

    creative_count = len(re.findall(r"data-creative-block=|^:::\s*[A-Za-z0-9_\-\u4e00-\u9fff]+", text, flags=re.M))
    if creative_count > 4:
        warnings.append(f"创意模块数量偏多：{creative_count} 个。")

    text_len = count_words(re.sub(r"<[^>]+>", "", body))
    if text_len < 300:
        warnings.append("正文偏短，可能不足以支撑公众号长文。")

    result = {
        "file": str(path),
        "kind": "html" if is_html else "markdown",
        "title": title,
        "word_like_count": text_len,
        "image_count": len(images),
        "creative_block_count": creative_count,
        "issues": issues,
        "warnings": warnings,
        "scores": {
            "metadata": score(5, [x for x in issues if "标题" in x] + [x for x in warnings if "元数据" in x]),
            "content_hygiene": score(5, [x for x in issues if "占位" in x or "危险" in x]),
            "asset_readiness": score(5, [x for x in issues if "图片" in x]),
        },
    }
    result["ok"] = not issues
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="公众号稿件轻量预检。")
    parser.add_argument("file", help="Markdown 或 HTML 文件。")
    parser.add_argument("--out", help="输出 JSON 文件。")
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        raise SystemExit(f"文件不存在：{path}")
    result = check_file(path)
    data = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).write_text(data + "\n", encoding="utf-8")
        print(f"预检结果已生成：{args.out}")
    else:
        print(data)


if __name__ == "__main__":
    main()
