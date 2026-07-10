#!/usr/bin/env python3
"""Render Markdown into WeChat-friendly inline-style HTML presets.

This script intentionally supports a practical Markdown subset. It is meant as a
stable preset renderer for公众号草稿准备, not as a full Markdown engine.
"""

from __future__ import annotations

import argparse
import html
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

try:
    from wechat_creative_blocks import render_creative_block
except Exception:  # pragma: no cover - 允许脚本被单文件搬运时降级
    render_creative_block = None


@dataclass(frozen=True)
class Preset:
    name: str
    label: str
    accent: str
    accent_soft: str
    text: str
    muted: str
    border: str
    bg: str
    panel: str
    heading_bg: str
    quote_bg: str
    code_bg: str
    code_text: str
    font: str


PRESETS: dict[str, Preset] = {
    "minimal": Preset(
        "minimal",
        "简约风",
        "#2f6f73",
        "#e9f4f3",
        "#222222",
        "#6b7280",
        "#e5e7eb",
        "#ffffff",
        "#ffffff",
        "#f6f8f8",
        "#f7faf9",
        "#f5f7f8",
        "#374151",
        "-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif",
    ),
    "formal": Preset(
        "formal",
        "正式风",
        "#8a1f1f",
        "#f8eeee",
        "#1f2933",
        "#5f6b7a",
        "#d9dee7",
        "#ffffff",
        "#ffffff",
        "#f7f3ef",
        "#fbf5f1",
        "#f3f4f6",
        "#374151",
        "'Noto Serif SC','Songti SC','SimSun',serif",
    ),
    "tech": Preset(
        "tech",
        "科技风",
        "#0f5f8c",
        "#e8f3fb",
        "#17212b",
        "#657586",
        "#d7e5ef",
        "#ffffff",
        "#ffffff",
        "#eef6ff",
        "#f4f9fd",
        "#eef3f7",
        "#123047",
        "-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif",
    ),
    "alert": Preset(
        "alert",
        "警示风",
        "#b42318",
        "#fff1f0",
        "#2b1d1d",
        "#7a5a55",
        "#f3c4bd",
        "#ffffff",
        "#ffffff",
        "#fff5f2",
        "#fff7f5",
        "#fff1f0",
        "#5a1f18",
        "-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif",
    ),
    "product": Preset(
        "product",
        "产品说明风",
        "#2f5d50",
        "#edf7f3",
        "#1f2d2a",
        "#66736f",
        "#d7e5df",
        "#ffffff",
        "#ffffff",
        "#f1f8f5",
        "#f6fbf8",
        "#f2f6f4",
        "#203b34",
        "-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif",
    ),
    "news": Preset(
        "news",
        "新闻评论风",
        "#111827",
        "#f3f4f6",
        "#111827",
        "#5b6472",
        "#d1d5db",
        "#fffdf9",
        "#fffdf9",
        "#f7f1e8",
        "#faf6ef",
        "#f4f4f5",
        "#27272a",
        "Georgia,'Times New Roman','Noto Serif SC','Songti SC',serif",
    ),
    "elegant": Preset(
        "elegant",
        "雅致风",
        "#7a4f8f",
        "#f5eef8",
        "#2e2633",
        "#73637b",
        "#eadff0",
        "#ffffff",
        "#ffffff",
        "#fbf6fd",
        "#fcf8fd",
        "#f6f2f8",
        "#43324a",
        "-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif",
    ),
    "government": Preset(
        "government",
        "政务正式风",
        "#7b1d1d",
        "#f8eeee",
        "#1f2933",
        "#667085",
        "#ded6cc",
        "#fffdf8",
        "#fffdf8",
        "#f8f1e8",
        "#fbf5ef",
        "#f4f4f5",
        "#333333",
        "'Noto Serif SC','Songti SC','SimSun',serif",
    ),
    "case": Preset(
        "case",
        "案例复盘风",
        "#3f5f45",
        "#eef6ef",
        "#223027",
        "#68736b",
        "#d8e3da",
        "#ffffff",
        "#ffffff",
        "#f3f8f3",
        "#f7faf7",
        "#f2f6f2",
        "#24382a",
        "-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif",
    ),
    "tutorial": Preset(
        "tutorial",
        "教程清单风",
        "#2563eb",
        "#eaf2ff",
        "#172033",
        "#64748b",
        "#d9e5f6",
        "#ffffff",
        "#ffffff",
        "#eef5ff",
        "#f6faff",
        "#f1f5f9",
        "#1e3a8a",
        "-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif",
    ),
    "deepread": Preset(
        "deepread",
        "深度长文风",
        "#334155",
        "#f1f5f9",
        "#1e293b",
        "#64748b",
        "#d6dde7",
        "#fffefb",
        "#fffefb",
        "#f5f1ea",
        "#faf7f1",
        "#f5f5f4",
        "#292524",
        "'Noto Serif SC','Songti SC','SimSun',serif",
    ),
    "warm": Preset(
        "warm",
        "温和品牌风",
        "#9a4d2e",
        "#fff3ed",
        "#2c2521",
        "#7a6a61",
        "#efd8cb",
        "#fffdfb",
        "#fffdfb",
        "#fff5ef",
        "#fff8f4",
        "#f8f1ed",
        "#4a2a1d",
        "-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif",
    ),
    "security": Preset(
        "security",
        "安全分析风",
        "#176b59",
        "#e9f7f2",
        "#182621",
        "#62716b",
        "#cfe1da",
        "#ffffff",
        "#ffffff",
        "#eef8f4",
        "#f5fbf8",
        "#f2f6f5",
        "#193d35",
        "-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif",
    ),
    "research": Preset(
        "research",
        "研究报告风",
        "#4b5563",
        "#f3f4f6",
        "#1f2937",
        "#6b7280",
        "#d9dee7",
        "#fffefc",
        "#fffefc",
        "#f5f2ec",
        "#faf8f3",
        "#f5f5f4",
        "#2f343d",
        "'Noto Serif SC','Songti SC','SimSun',serif",
    ),
    "launch": Preset(
        "launch",
        "新品发布风",
        "#1d6f5f",
        "#eef8f4",
        "#1f2f2b",
        "#68756f",
        "#d7e6df",
        "#ffffff",
        "#ffffff",
        "#f3faf6",
        "#f8fcfa",
        "#f3f6f4",
        "#24443d",
        "-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif",
    ),
    "ops": Preset(
        "ops",
        "运营复盘风",
        "#365a9c",
        "#edf3ff",
        "#172033",
        "#647084",
        "#d6e1f2",
        "#ffffff",
        "#ffffff",
        "#f1f6ff",
        "#f7faff",
        "#f3f5f8",
        "#253b65",
        "-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif",
    ),
}

ALIASES = {
    "简约": "minimal",
    "简约风": "minimal",
    "正式": "formal",
    "正式风": "formal",
    "政务": "formal",
    "政务正式": "government",
    "政务正式风": "government",
    "科技": "tech",
    "科技风": "tech",
    "警示": "alert",
    "警示风": "alert",
    "应急": "alert",
    "产品": "product",
    "产品风": "product",
    "新闻": "news",
    "评论": "news",
    "雅致": "elegant",
    "文艺": "elegant",
    "案例": "case",
    "复盘": "case",
    "案例复盘": "case",
    "教程": "tutorial",
    "教程清单": "tutorial",
    "清单": "tutorial",
    "深度": "deepread",
    "长文": "deepread",
    "深度长文": "deepread",
    "温和": "warm",
    "品牌": "warm",
    "温和品牌": "warm",
    "安全分析": "security",
    "安全分析风": "security",
    "威胁分析": "security",
    "研究报告": "research",
    "研究报告风": "research",
    "报告": "research",
    "新品": "launch",
    "新品发布": "launch",
    "新品发布风": "launch",
    "发布会": "launch",
    "运营": "ops",
    "运营复盘": "ops",
    "运营复盘风": "ops",
}


def esc(text: str) -> str:
    return html.escape(text, quote=False)


def safe_url(url: str) -> str:
    """Allow web URLs and local/relative image paths; block active URLs."""
    raw = html.unescape(url).strip()
    if not raw:
        return "#"
    lower = raw.lower()
    parsed = urlparse(raw)
    if parsed.scheme in ("http", "https"):
        return html.escape(raw, quote=True)
    if lower.startswith("data:image/"):
        return html.escape(raw, quote=True)
    if re.match(r"^[a-zA-Z]:[\\/]", raw):
        return html.escape(raw, quote=True)
    if parsed.scheme:
        return "#"
    if lower.startswith(("javascript:", "vbscript:", "file:")):
        return "#"
    return html.escape(raw, quote=True)


def inline(text: str, p: Preset) -> str:
    text = esc(text)
    text = re.sub(r"`([^`]+)`", rf'<code style="font-family:Consolas,Menlo,monospace;font-size:90%;color:{p.code_text};background:{p.code_bg};border:1px solid {p.border};border-radius:4px;padding:1px 5px;">\1</code>', text)
    text = re.sub(r"\*\*([^*]+)\*\*", rf'<strong style="color:{p.text};font-weight:700;">\1</strong>', text)
    text = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", text)
    def repl_link(match: re.Match[str]) -> str:
        label = match.group(1)
        url = safe_url(match.group(2))
        return f'<a href="{url}" style="color:{p.accent};text-decoration:none;border-bottom:1px solid {p.accent_soft};">{label}</a>'

    text = re.sub(r"\[([^\]]+)\]\(([^ \t\r\n]+(?:\([^)]*\)[^ \t\r\n]*)?)\)", repl_link, text)
    return text


def wrap_page(body: str, p: Preset, title: str | None) -> str:
    title_html = f"<title>{esc(title)}</title>" if title else "<title>WeChat Article</title>"
    return (
        "<!doctype html>\n<html>\n<head>\n<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
        f"{title_html}\n</head>\n"
        f'<body style="margin:0;background:{p.bg};">\n'
        f'<section data-preset="{p.name}" style="max-width:677px;margin:0 auto;padding:22px 16px 32px;box-sizing:border-box;'
        f'font-family:{p.font};color:{p.text};background:{p.bg};">\n'
        f"{body}\n</section>\n</body>\n</html>\n"
    )


def heading(text: str, level: int, p: Preset) -> str:
    clean = inline(text.strip(), p)
    if level <= 1:
        return (
            f'<h1 style="font-size:24px;line-height:1.42;color:{p.text};font-weight:800;'
            f'letter-spacing:0;margin:8px 0 20px;padding:0;">{clean}</h1>'
        )
    if level == 2:
        return (
            f'<section style="margin:30px 0 16px;padding:12px 14px;border-left:5px solid {p.accent};'
            f'background:{p.heading_bg};border-radius:6px;">'
            f'<h2 style="font-size:18px;line-height:1.45;color:{p.text};font-weight:800;margin:0;">{clean}</h2>'
            "</section>"
        )
    return (
        f'<h{min(level, 6)} style="font-size:16px;line-height:1.55;color:{p.accent};font-weight:800;'
        f'margin:22px 0 10px;">{clean}</h{min(level, 6)}>'
    )


def paragraph(text: str, p: Preset) -> str:
    return (
        f'<p style="font-size:16px;line-height:1.9;color:{p.text};margin:13px 0;'
        f'text-align:justify;">{inline(text.strip(), p)}</p>'
    )


def blockquote(lines: list[str], p: Preset) -> str:
    content = "<br>".join(inline(line.strip().lstrip("> ").strip(), p) for line in lines)
    return (
        f'<section style="margin:18px 0;padding:12px 14px;border-left:4px solid {p.accent};'
        f'background:{p.quote_bg};border-radius:0 6px 6px 0;color:{p.muted};font-size:15px;line-height:1.8;">'
        f"{content}</section>"
    )


def code_block(code: str, p: Preset) -> str:
    return (
        f'<pre style="box-sizing:border-box;white-space:pre-wrap;word-break:break-word;'
        f'font-family:Consolas,Menlo,monospace;font-size:13px;line-height:1.65;'
        f'color:{p.code_text};background:{p.code_bg};border:1px solid {p.border};'
        f'border-radius:6px;padding:12px 13px;margin:16px 0;overflow:hidden;">'
        f"{esc(code.rstrip())}</pre>"
    )


def image(src: str, alt: str, p: Preset) -> str:
    src = safe_url(src)
    return (
        f'<section style="margin:18px 0;text-align:center;">'
        f'<img src="{src}" alt="{html.escape(alt, quote=True)}" '
        f'style="max-width:100%;height:auto;border-radius:6px;border:1px solid {p.border};display:block;margin:0 auto;">'
        f'{f"<span style=\"display:block;font-size:13px;color:{p.muted};line-height:1.6;margin-top:6px;\">{esc(alt)}</span>" if alt else ""}'
        "</section>"
    )


def list_block(items: list[str], ordered: bool, p: Preset) -> str:
    tag = "ol" if ordered else "ul"
    lis = []
    for item in items:
        lis.append(f'<li style="margin:6px 0;line-height:1.75;color:{p.text};">{inline(item, p)}</li>')
    return (
        f'<{tag} style="font-size:16px;line-height:1.75;margin:12px 0 16px 0;padding-left:24px;color:{p.text};">'
        + "".join(lis)
        + f"</{tag}>"
    )


def table_block(rows: list[list[str]], p: Preset) -> str:
    if not rows:
        return ""
    head = rows[0]
    body_rows = rows[1:]
    ths = "".join(
        f'<th style="padding:9px 8px;border:1px solid {p.border};background:{p.heading_bg};'
        f'color:{p.text};font-size:14px;line-height:1.55;text-align:left;font-weight:700;">{inline(cell.strip(), p)}</th>'
        for cell in head
    )
    trs = [f"<tr>{ths}</tr>"]
    for row in body_rows:
        cells = row + [""] * max(0, len(head) - len(row))
        tds = "".join(
            f'<td style="padding:9px 8px;border:1px solid {p.border};color:{p.text};'
            f'font-size:14px;line-height:1.65;vertical-align:top;">{inline(cell.strip(), p)}</td>'
            for cell in cells[: len(head)]
        )
        trs.append(f"<tr>{tds}</tr>")
    return (
        f'<section style="margin:16px 0;overflow-x:auto;">'
        f'<table style="width:100%;border-collapse:collapse;table-layout:auto;">{"".join(trs)}</table>'
        f"</section>"
    )


def hr(p: Preset) -> str:
    return f'<section style="height:1px;background:{p.border};margin:26px 0;"></section>'


def parse_table_row(line: str) -> list[str] | None:
    stripped = line.strip()
    if not (stripped.startswith("|") and stripped.endswith("|")):
        return None
    cells = [cell.strip() for cell in stripped.strip("|").split("|")]
    return cells


def is_table_separator(line: str) -> bool:
    cells = parse_table_row(line)
    if not cells:
        return False
    return all(re.fullmatch(r":?-{3,}:?", cell.strip()) for cell in cells)


def strip_frontmatter(lines: list[str]) -> tuple[list[str], dict[str, str]]:
    if not lines or lines[0].strip() != "---":
        return lines, {}
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
        return lines, {}
    return lines[end + 1 :], meta


def render(markdown: str, p: Preset) -> tuple[str, str | None]:
    lines, meta = strip_frontmatter(markdown.splitlines())
    out: list[str] = []
    para: list[str] = []
    quote: list[str] = []
    items: list[str] = []
    ordered_items: list[str] = []
    code_lines: list[str] = []
    in_code = False
    title: str | None = meta.get("title")

    def flush_para() -> None:
        if para:
            out.append(paragraph(" ".join(x.strip() for x in para), p))
            para.clear()

    def flush_quote() -> None:
        if quote:
            out.append(blockquote(quote, p))
            quote.clear()

    def flush_lists() -> None:
        if items:
            out.append(list_block(items, False, p))
            items.clear()
        if ordered_items:
            out.append(list_block(ordered_items, True, p))
            ordered_items.clear()

    i = 0
    while i < len(lines):
        raw = lines[i]
        line = raw.rstrip()
        if line.startswith("```"):
            flush_para()
            flush_quote()
            flush_lists()
            if in_code:
                out.append(code_block("\n".join(code_lines), p))
                code_lines.clear()
                in_code = False
            else:
                in_code = True
            i += 1
            continue
        if in_code:
            code_lines.append(line)
            i += 1
            continue
        if not line.strip():
            flush_para()
            flush_quote()
            flush_lists()
            i += 1
            continue
        if re.match(r"^\s*---+\s*$", line):
            flush_para()
            flush_quote()
            flush_lists()
            out.append(hr(p))
            i += 1
            continue
        m_creative = re.match(r"^:::\s*([A-Za-z0-9_-]+|[\u4e00-\u9fff]+)(?:\s+(.+))?\s*$", line.strip())
        if m_creative:
            flush_para()
            flush_quote()
            flush_lists()
            style = m_creative.group(1)
            title_arg = (m_creative.group(2) or "").strip()
            block_lines: list[str] = []
            i += 1
            while i < len(lines) and lines[i].strip() != ":::":
                block_lines.append(lines[i].rstrip())
                i += 1
            if i < len(lines) and lines[i].strip() == ":::":
                i += 1
            text = "\n".join(block_lines).strip()
            if render_creative_block:
                out.append(render_creative_block(style, text, title_arg))
            else:
                out.append(blockquote([f"> {title_arg}", *[f"> {x}" for x in block_lines if x.strip()]], p))
            continue
        table_row = parse_table_row(line)
        if table_row and i + 1 < len(lines) and is_table_separator(lines[i + 1]):
            flush_para()
            flush_quote()
            flush_lists()
            table_rows = [table_row]
            i += 2
            while i < len(lines):
                next_row = parse_table_row(lines[i])
                if not next_row:
                    break
                table_rows.append(next_row)
                i += 1
            out.append(table_block(table_rows, p))
            continue
        m_img = re.match(r"!\[([^\]]*)\]\(([^ \t\r\n]+(?:\([^)]*\)[^ \t\r\n]*)?)\)", line.strip())
        if m_img:
            flush_para()
            flush_quote()
            flush_lists()
            out.append(image(m_img.group(2), m_img.group(1), p))
            i += 1
            continue
        if line.lstrip().startswith(">"):
            flush_para()
            flush_lists()
            quote.append(line)
            i += 1
            continue
        m_head = re.match(r"^(#{1,6})\s+(.+)$", line)
        if m_head:
            flush_para()
            flush_quote()
            flush_lists()
            level = len(m_head.group(1))
            text = m_head.group(2).strip()
            if title is None and level == 1:
                title = re.sub(r"`|\*|_", "", text)
            out.append(heading(text, level, p))
            i += 1
            continue
        m_task = re.match(r"^\s*[-*+]\s+\[([ xX])\]\s+(.+)$", line)
        if m_task:
            flush_para()
            flush_quote()
            ordered_items.clear()
            mark = "已完成" if m_task.group(1).lower() == "x" else "待处理"
            items.append(f"{mark}：{m_task.group(2).strip()}")
            i += 1
            continue
        m_ul = re.match(r"^\s*[-*+]\s+(.+)$", line)
        if m_ul:
            flush_para()
            flush_quote()
            ordered_items.clear()
            items.append(m_ul.group(1).strip())
            i += 1
            continue
        m_ol = re.match(r"^\s*\d+[.)]\s+(.+)$", line)
        if m_ol:
            flush_para()
            flush_quote()
            items.clear()
            ordered_items.append(m_ol.group(1).strip())
            i += 1
            continue
        para.append(line)
        i += 1

    flush_para()
    flush_quote()
    flush_lists()
    if in_code and code_lines:
        out.append(code_block("\n".join(code_lines), p))
    return "\n".join(out), title


def resolve_preset(name: str) -> Preset:
    key = ALIASES.get(name, name)
    if key not in PRESETS:
        known = ", ".join(sorted(PRESETS))
        raise SystemExit(f"Unknown preset: {name}. Available: {known}")
    return PRESETS[key]


def main() -> None:
    parser = argparse.ArgumentParser(description="Render Markdown with WeChat inline-style presets.")
    parser.add_argument("input", nargs="?", help="Input Markdown file")
    parser.add_argument("--preset", default="minimal", help="Preset name or Chinese alias")
    parser.add_argument("--out", help="Output HTML file")
    parser.add_argument("--list", action="store_true", help="List presets")
    args = parser.parse_args()

    if args.list:
        for key, preset in PRESETS.items():
            print(f"{key}\t{preset.label}")
        return

    if not args.input:
        raise SystemExit("Input Markdown file is required unless --list is used.")

    src = Path(args.input)
    if not src.exists():
        raise SystemExit(f"Input file not found: {src}")
    preset = resolve_preset(args.preset)
    markdown = src.read_text(encoding="utf-8-sig")
    body, title = render(markdown, preset)
    html_doc = wrap_page(body, preset, title)
    out = Path(args.out) if args.out else src.with_suffix(f".{preset.name}.html")
    out.write_text(html_doc, encoding="utf-8")
    print(f"Preset: {preset.name} ({preset.label})")
    print(f"Output: {out}")


if __name__ == "__main__":
    main()
