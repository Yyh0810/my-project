#!/usr/bin/env python3
"""生成微信图文可复用的小创意排版模块。"""

from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


STYLE_ALIASES = {
    "question": "question",
    "ask": "question",
    "提问": "question",
    "问题": "question",
    "divider": "divider",
    "sep": "divider",
    "分割线": "divider",
    "分隔": "divider",
    "quote": "quote",
    "note": "quote",
    "highlight": "quote",
    "引语": "quote",
    "高亮": "quote",
    "insight": "insight",
    "洞察": "insight",
    "观点": "insight",
    "agentbox": "agentbox",
    "box": "agentbox",
    "card": "agentbox",
    "卡片": "agentbox",
    "信息卡": "agentbox",
    "checklist": "checklist",
    "checks": "checklist",
    "清单": "checklist",
    "检查清单": "checklist",
    "steps": "steps",
    "timeline": "steps",
    "步骤": "steps",
    "流程": "steps",
    "stat": "stat",
    "metric": "stat",
    "数据": "stat",
    "数字": "stat",
    "compare": "compare",
    "comparison": "compare",
    "对比": "compare",
    "cta": "cta",
    "action": "cta",
    "行动": "cta",
    "收束": "cta",
    "warning": "warning",
    "risk": "warning",
    "风险": "warning",
    "风险提示": "warning",
    "definition": "definition",
    "term": "definition",
    "定义": "definition",
    "概念": "definition",
    "summary": "summary",
    "recap": "summary",
    "小结": "summary",
    "总结": "summary",
    "source": "source",
    "sources": "source",
    "依据": "source",
    "来源": "source",
}

KNOWN_STYLES = {
    "question",
    "divider",
    "quote",
    "insight",
    "agentbox",
    "checklist",
    "steps",
    "stat",
    "compare",
    "cta",
    "warning",
    "definition",
    "summary",
    "source",
}


def esc(text: str) -> str:
    return html.escape(text, quote=False)


def normalize_style(style: str) -> str:
    key = STYLE_ALIASES.get(style.strip().lower(), style.strip().lower())
    if key not in KNOWN_STYLES:
        known = ", ".join(sorted(STYLE_ALIASES))
        raise SystemExit(f"未知创意模块：{style}。可用：{known}")
    return key


def inline(text: str, accent: str) -> str:
    text = esc(text)
    return re.sub(
        r"\*\*([^*]+)\*\*",
        rf'<strong style="color:{accent};font-weight:800;">\1</strong>',
        text,
    )


def paragraph_lines(text: str, accent: str, color: str, margin: str = "9px 0") -> str:
    blocks = []
    for para in re.split(r"\n\s*\n", text.strip()):
        clean = " ".join(line.strip() for line in para.splitlines() if line.strip())
        if clean:
            blocks.append(
                f'<p style="font-size:15px;line-height:1.9;color:{color};margin:{margin};text-align:justify;">'
                f"{inline(clean, accent)}</p>"
            )
    return "".join(blocks)


def plain_items(text: str) -> list[str]:
    items = []
    for line in text.splitlines():
        clean = re.sub(r"^\s*[-*+]\s+", "", line.strip())
        clean = re.sub(r"^\s*\d+[.)]\s+", "", clean)
        if clean:
            items.append(clean)
    return items


def render_divider(text: str, title: str = "") -> str:
    label = title.strip() or text.strip()
    label_html = (
        '<span style="display:inline-block;background:#ffffff;color:#2563eb;font-size:13px;'
        'font-weight:700;line-height:1.4;padding:0 10px;">'
        f"{inline(label, '#2563eb')}</span>"
        if label
        else '<span style="display:inline-block;background:#ffffff;color:#7d94ff;font-size:13px;padding:0 9px;">◆ ◆ ◆</span>'
    )
    return (
        '<section data-creative-block="divider" style="margin:26px 0;text-align:center;">'
        '<section style="margin:0 auto;max-width:330px;height:1px;line-height:1px;'
        'border-top:1px dotted #8ea2ff;text-align:center;">'
        f'<span style="display:inline-block;margin-top:-9px;">{label_html}</span>'
        "</section>"
        "</section>"
    )


def render_question(text: str, title: str = "") -> str:
    content = title.strip() or text.strip()
    if not content:
        raise SystemExit("question 模块需要标题或正文。")
    return (
        '<section data-creative-block="question" style="margin:28px 0 24px;text-align:center;">'
        '<section style="margin:0 auto 14px;max-width:260px;height:1px;line-height:1px;'
        'border-top:1px dotted #7d94ff;text-align:center;">'
        '<span style="display:inline-block;background:#ffffff;color:#6b82ff;font-size:13px;'
        'line-height:1;margin-top:-7px;padding:0 9px;">◆ ◆ ◆</span>'
        "</section>"
        '<section style="margin:0 0 8px;text-align:center;">'
        '<span style="display:inline-block;width:34px;height:24px;line-height:24px;text-align:center;'
        'border-radius:12px;background:#2f7df6;color:#ffffff;font-size:13px;font-weight:800;'
        'box-shadow:0 2px 0 #c9dcff;">AI</span>'
        "</section>"
        '<section style="display:inline-block;max-width:92%;box-sizing:border-box;padding:8px 18px;'
        'border:1px solid #c8dcff;border-radius:4px;background:#f4f8ff;'
        'box-shadow:inset 0 0 0 1px #edf4ff;color:#0b64e6;font-size:15px;line-height:1.65;'
        'font-weight:800;text-align:left;">'
        f'<span style="color:#0b64e6;">——、</span>{inline(content, "#0b64e6")}'
        "</section>"
        "</section>"
    )


def render_quote(text: str, title: str = "") -> str:
    body = paragraph_lines(text, "#7866dd", "#1f2933")
    if not body:
        raise SystemExit("quote 模块需要正文。")
    heading = (
        f'<p style="font-size:15px;line-height:1.8;color:#7866dd;font-weight:800;margin:0 0 8px;">'
        f"{inline(title.strip(), '#7866dd')}</p>"
        if title.strip()
        else ""
    )
    return (
        '<section data-creative-block="quote" style="margin:22px 0;padding:16px 18px 15px;'
        'border-left:4px solid #8977ff;background:#fffdf0;box-sizing:border-box;">'
        '<section style="font-size:30px;line-height:20px;color:#e4ddff;font-family:Georgia,serif;'
        'font-weight:700;margin:0 0 2px;">“</section>'
        f"{heading}{body}"
        "</section>"
    )


def render_insight(text: str, title: str = "") -> str:
    label = title.strip() or "核心洞察"
    body = paragraph_lines(text, "#005bea", "#172033")
    if not body:
        raise SystemExit("insight 模块需要正文。")
    return (
        '<section data-creative-block="insight" style="margin:22px 0;padding:14px 15px;'
        'border:1px solid #bcd4ff;border-radius:8px;background:#f7fbff;box-sizing:border-box;">'
        '<section style="font-size:13px;line-height:1.5;color:#005bea;font-weight:800;margin:0 0 8px;">'
        '<span style="display:inline-block;width:6px;height:6px;border-radius:50%;background:#005bea;'
        'vertical-align:middle;margin-right:7px;"></span>'
        f"{inline(label, '#005bea')}</section>{body}</section>"
    )


def render_agentbox(text: str, title: str = "") -> str:
    label = title.strip() or "AgentBox"
    body = paragraph_lines(text, "#005bea", "#111827")
    if not body:
        raise SystemExit("agentbox 模块需要正文。")
    return (
        '<section data-creative-block="agentbox" style="margin:28px 0 24px;">'
        '<section style="margin:0 0 -1px 16px;line-height:1;">'
        '<span style="display:inline-block;padding:6px 12px;border-radius:14px 14px 6px 6px;'
        'background:#8fcaff;color:#0b3b8c;font-size:14px;font-weight:800;letter-spacing:0;">'
        '<span style="display:inline-block;width:18px;height:18px;line-height:18px;text-align:center;'
        'border-radius:50%;background:#dff5ff;color:#2575ff;margin-right:5px;">AI</span>'
        f"{esc(label)}</span></section>"
        '<section style="border:1px solid #698cff;border-radius:10px;padding:10px;box-sizing:border-box;'
        'background:#ffffff;">'
        '<section style="border-radius:8px;padding:18px 17px;background:linear-gradient(180deg,#e7edff 0%,#d7efff 100%);'
        'box-sizing:border-box;">'
        f"{body}"
        "</section>"
        "</section>"
        '<section style="text-align:right;color:#7fdcff;font-size:16px;line-height:1;letter-spacing:3px;'
        'margin:-9px 6px 0 0;">••••••<br>••••••</section>'
        "</section>"
    )


def render_checklist(text: str, title: str = "") -> str:
    label = title.strip() or "检查清单"
    items = plain_items(text)
    if not items:
        raise SystemExit("checklist 模块需要清单正文。")
    rows = "".join(
        '<p style="font-size:15px;line-height:1.75;color:#172033;margin:8px 0;">'
        '<span style="display:inline-block;width:20px;height:20px;line-height:20px;text-align:center;'
        'border-radius:50%;background:#e7f1ff;color:#005bea;font-size:12px;font-weight:800;margin-right:8px;">✓</span>'
        f"{inline(item, '#005bea')}</p>"
        for item in items
    )
    return (
        '<section data-creative-block="checklist" style="margin:22px 0;padding:15px 16px;'
        'border:1px solid #d3e4ff;border-radius:8px;background:#ffffff;box-sizing:border-box;">'
        '<section style="font-size:15px;line-height:1.6;color:#005bea;font-weight:800;margin:0 0 8px;">'
        f"{esc(label)}</section>{rows}</section>"
    )


def render_steps(text: str, title: str = "") -> str:
    label = title.strip() or "推进路径"
    items = plain_items(text)
    if not items:
        raise SystemExit("steps 模块需要步骤正文。")
    rows = []
    for idx, item in enumerate(items, start=1):
        rows.append(
            '<section style="margin:0 0 12px;">'
            '<span style="display:inline-block;width:24px;height:24px;line-height:24px;text-align:center;'
            'border-radius:50%;background:#2563eb;color:#ffffff;font-size:13px;font-weight:800;margin-right:10px;">'
            f"{idx}</span>"
            '<span style="font-size:15px;line-height:1.75;color:#172033;">'
            f"{inline(item, '#005bea')}</span></section>"
        )
    return (
        '<section data-creative-block="steps" style="margin:22px 0;padding:16px 16px 6px;'
        'border-left:4px solid #2563eb;background:#f6f9ff;box-sizing:border-box;">'
        '<section style="font-size:15px;line-height:1.6;color:#005bea;font-weight:800;margin:0 0 12px;">'
        f"{esc(label)}</section>{''.join(rows)}</section>"
    )


def render_stat(text: str, title: str = "") -> str:
    metric = title.strip() or "关键数字"
    body = paragraph_lines(text, "#005bea", "#334155", "6px 0")
    return (
        '<section data-creative-block="stat" style="margin:22px 0;text-align:center;">'
        '<section style="display:inline-block;min-width:58%;box-sizing:border-box;padding:16px 18px;'
        'border:1px solid #c5dcff;border-radius:8px;background:#f8fbff;">'
        '<section style="font-size:28px;line-height:1.2;color:#005bea;font-weight:900;margin:0 0 6px;">'
        f"{inline(metric, '#005bea')}</section>"
        f"{body}</section></section>"
    )


def render_compare(text: str, title: str = "") -> str:
    parts = re.split(r"\n\s*---+\s*\n", text.strip(), maxsplit=1)
    if len(parts) != 2:
        raise SystemExit("compare 模块需要用单独一行 --- 分隔左右两侧内容。")
    left = paragraph_lines(parts[0], "#b42318", "#1f2933", "6px 0")
    right = paragraph_lines(parts[1], "#005bea", "#1f2933", "6px 0")
    label = title.strip() or "对比看"
    return (
        '<section data-creative-block="compare" style="margin:22px 0;">'
        '<section style="font-size:15px;line-height:1.6;color:#005bea;font-weight:800;margin:0 0 10px;">'
        f"{esc(label)}</section>"
        '<section style="padding:12px;border:1px solid #ffd1cb;background:#fff7f5;box-sizing:border-box;margin:0 0 10px;">'
        '<section style="font-size:13px;color:#b42318;font-weight:800;margin-bottom:6px;">常见做法</section>'
        f"{left}</section>"
        '<section style="padding:12px;border:1px solid #c5dcff;background:#f7fbff;box-sizing:border-box;">'
        '<section style="font-size:13px;color:#005bea;font-weight:800;margin-bottom:6px;">建议做法</section>'
        f"{right}</section></section>"
    )


def render_cta(text: str, title: str = "") -> str:
    label = title.strip() or "下一步"
    body = paragraph_lines(text, "#005bea", "#172033")
    if not body:
        raise SystemExit("cta 模块需要正文。")
    return (
        '<section data-creative-block="cta" style="margin:26px 0 18px;padding:16px 18px;'
        'border-radius:8px;background:#f1f7ff;border:1px solid #c8dcff;box-sizing:border-box;text-align:center;">'
        '<section style="display:inline-block;padding:4px 12px;border-radius:14px;background:#005bea;'
        'color:#ffffff;font-size:13px;font-weight:800;margin-bottom:8px;">'
        f"{esc(label)}</section>{body}</section>"
    )


def render_warning(text: str, title: str = "") -> str:
    label = title.strip() or "风险提示"
    body = paragraph_lines(text, "#b42318", "#2b1d1d")
    if not body:
        raise SystemExit("warning 模块需要正文。")
    return (
        '<section data-creative-block="warning" style="margin:22px 0;padding:14px 15px;'
        'border:1px solid #f3c4bd;border-left:5px solid #b42318;border-radius:6px;'
        'background:#fff7f5;box-sizing:border-box;">'
        '<section style="font-size:15px;line-height:1.6;color:#b42318;font-weight:800;margin:0 0 8px;">'
        f"{esc(label)}</section>{body}</section>"
    )


def render_definition(text: str, title: str = "") -> str:
    label = title.strip() or "概念解释"
    body = paragraph_lines(text, "#176b59", "#1f2933")
    if not body:
        raise SystemExit("definition 模块需要正文。")
    return (
        '<section data-creative-block="definition" style="margin:22px 0;padding:15px 16px;'
        'border:1px solid #cfe1da;border-radius:8px;background:#f7fbf9;box-sizing:border-box;">'
        '<section style="font-size:13px;line-height:1.5;color:#176b59;font-weight:800;margin:0 0 8px;">'
        '<span style="display:inline-block;padding:2px 8px;border-radius:12px;background:#e9f7f2;color:#176b59;">'
        f"{esc(label)}</span></section>{body}</section>"
    )


def render_summary(text: str, title: str = "") -> str:
    label = title.strip() or "本节小结"
    items = plain_items(text)
    if not items:
        raise SystemExit("summary 模块需要清单正文。")
    rows = "".join(
        '<p style="font-size:15px;line-height:1.75;color:#172033;margin:8px 0;">'
        '<span style="display:inline-block;width:7px;height:7px;border-radius:50%;'
        'background:#365a9c;margin-right:9px;vertical-align:middle;"></span>'
        f"{inline(item, '#365a9c')}</p>"
        for item in items
    )
    return (
        '<section data-creative-block="summary" style="margin:24px 0;padding:15px 16px;'
        'border-top:2px solid #365a9c;border-bottom:1px solid #d6e1f2;'
        'background:#f7faff;box-sizing:border-box;">'
        '<section style="font-size:15px;line-height:1.6;color:#365a9c;font-weight:800;margin:0 0 9px;">'
        f"{esc(label)}</section>{rows}</section>"
    )


def render_source(text: str, title: str = "") -> str:
    label = title.strip() or "依据与说明"
    body = paragraph_lines(text, "#64748b", "#475569", "6px 0")
    if not body:
        raise SystemExit("source 模块需要正文。")
    return (
        '<section data-creative-block="source" style="margin:20px 0;padding:12px 14px;'
        'border:1px dashed #cbd5e1;border-radius:6px;background:#f8fafc;box-sizing:border-box;">'
        '<section style="font-size:13px;line-height:1.5;color:#64748b;font-weight:800;margin:0 0 6px;">'
        f"{esc(label)}</section>{body}</section>"
    )


def render_creative_block(style: str, text: str, title: str = "") -> str:
    key = normalize_style(style)
    if key == "question":
        return render_question(text, title)
    if key == "divider":
        return render_divider(text, title)
    if key == "quote":
        return render_quote(text, title)
    if key == "insight":
        return render_insight(text, title)
    if key == "agentbox":
        return render_agentbox(text, title)
    if key == "checklist":
        return render_checklist(text, title)
    if key == "steps":
        return render_steps(text, title)
    if key == "stat":
        return render_stat(text, title)
    if key == "compare":
        return render_compare(text, title)
    if key == "cta":
        return render_cta(text, title)
    if key == "warning":
        return render_warning(text, title)
    if key == "definition":
        return render_definition(text, title)
    if key == "summary":
        return render_summary(text, title)
    return render_source(text, title)


def read_body(args: argparse.Namespace) -> str:
    if args.file:
        return Path(args.file).read_text(encoding="utf-8-sig")
    return args.text or ""


def main() -> None:
    parser = argparse.ArgumentParser(description="生成微信图文小创意 HTML 模块。")
    parser.add_argument("--style", default="question", help="question / quote / agentbox")
    parser.add_argument("--title", default="", help="标题或标签。")
    parser.add_argument("--text", default="", help="模块正文。支持用 **文字** 标记重点。")
    parser.add_argument("--file", help="从文本文件读取正文。")
    parser.add_argument("--out", help="输出 HTML 片段文件。")
    parser.add_argument("--list", action="store_true", help="列出可用模块。")
    args = parser.parse_args()

    if args.list:
        print("divider\t短分割线/转场标签")
        print("question\t分割提问模块")
        print("quote\t重点引语模块")
        print("insight\t核心洞察卡")
        print("agentbox\t标签信息卡模块")
        print("checklist\t检查清单模块")
        print("steps\t步骤/时间线模块")
        print("stat\t关键数字模块")
        print("compare\t左右对比模块")
        print("cta\t结尾行动提示模块")
        print("warning\t风险提示模块")
        print("definition\t概念解释模块")
        print("summary\t本节小结模块")
        print("source\t依据与来源说明模块")
        return

    html_block = render_creative_block(args.style, read_body(args), args.title)
    if args.out:
        Path(args.out).write_text(html_block + "\n", encoding="utf-8")
        print(f"创意模块已生成：{args.out}")
    else:
        print(html_block)


if __name__ == "__main__":
    main()
