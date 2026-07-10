#!/usr/bin/env python3
"""为公众号 Markdown 自动生成小组件编排计划并输出组件版新稿。"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


ARTICLE_TYPES = {
    "security-analysis": "安全分析",
    "agent-observation": "AI Agent 观察",
    "product-launch": "产品发布",
    "industry-observation": "行业观察",
    "case-review": "案例复盘",
}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def split_frontmatter(text: str) -> tuple[str, str]:
    lines = text.splitlines()
    if lines and lines[0].strip() == "---":
        for idx in range(1, min(len(lines), 80)):
            if lines[idx].strip() == "---":
                return "\n".join(lines[: idx + 1]) + "\n\n", "\n".join(lines[idx + 1 :]).lstrip()
    return "", text


def paragraphs(body: str) -> list[str]:
    blocks = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
    return [p for p in blocks if not p.startswith(":::") and not p.startswith("#")]


def first_sentence(text: str, fallback: str) -> str:
    clean = re.sub(r"\s+", " ", text).strip()
    match = re.split(r"(?<=[。！？!?])", clean, maxsplit=1)
    return (match[0].strip() if match and match[0].strip() else fallback)[:80]


def has_component(text: str) -> bool:
    return bool(re.search(r"^:::\s*[A-Za-z0-9_\-\u4e00-\u9fff]+", text, flags=re.M))


def make_block(style: str, title: str, text: str) -> str:
    title_part = f" {title}" if title else ""
    return f":::{style}{title_part}\n{text.strip()}\n:::"


def build_blocks(body: str, article_type: str) -> list[dict[str, str]]:
    paras = paragraphs(body)
    joined = "\n".join(paras)
    blocks: list[dict[str, str]] = []
    if paras:
        blocks.append(
            {
                "style": "question",
                "title": "",
                "text": f"这篇文章真正要回答的问题是什么？",
                "reason": "用短问题建立阅读目标。",
                "placement": "开头后",
            }
        )
        blocks.append(
            {
                "style": "quote" if article_type != "product-launch" else "insight",
                "title": "核心判断" if article_type == "product-launch" else "",
                "text": first_sentence(paras[min(1, len(paras) - 1)], "核心判断必须能被后文证据兑现。"),
                "reason": "突出核心判断，避免读者迷失在段落堆叠中。",
                "placement": "第一处分析段后",
            }
        )
    if re.search(r"(风险|漏洞|阻断|密钥|攻击|待核验|不确定|边界)", joined):
        blocks.append(
            {
                "style": "warning",
                "title": "风险提示",
                "text": "涉及风险、数据、漏洞、客户或产品边界的内容，必须有来源或保留待核验标记。",
                "reason": "收束风险边界，避免正文散落提示。",
                "placement": "风险段后",
            }
        )
    if re.search(r"(建议|检查|下一步|行动|试点|复核|评估|处置)", joined):
        blocks.append(
            {
                "style": "checklist",
                "title": "下一步检查",
                "text": "- 确认关键事实来源\n- 复核适用边界\n- 明确读者下一步动作",
                "reason": "把行动建议转成可扫读清单。",
                "placement": "行动建议前",
            }
        )
    if len(blocks) < 2:
        blocks.append(
            {
                "style": "summary",
                "title": "本节小结",
                "text": "- 核心判断要被证据支撑\n- 事实边界要明确\n- 下一步动作要具体",
                "reason": "补充章节收束。",
                "placement": "结尾前",
            }
        )
    if len(blocks) < 4 and re.search(r"(来源|依据|报告|公告|数据|待核验|http)", joined, flags=re.I):
        blocks.append(
            {
                "style": "source",
                "title": "依据与说明",
                "text": "具体事实以公开来源、内部材料或人工核验结果为准；未确认信息保留待核验。",
                "reason": "说明事实边界。",
                "placement": "结尾前",
            }
        )
    return blocks[:4]


def insert_blocks(frontmatter: str, body: str, blocks: list[dict[str, str]]) -> str:
    if has_component(body):
        return frontmatter + body.rstrip() + "\n"
    parts = re.split(r"\n\s*\n", body.strip())
    output: list[str] = []
    inserted = 0
    for idx, part in enumerate(parts):
        output.append(part)
        if idx == 1 and inserted < len(blocks):
            output.append(make_block(blocks[inserted]["style"], blocks[inserted]["title"], blocks[inserted]["text"]))
            inserted += 1
        elif idx == 3 and inserted < len(blocks):
            output.append(make_block(blocks[inserted]["style"], blocks[inserted]["title"], blocks[inserted]["text"]))
            inserted += 1
        elif idx == len(parts) - 2 and inserted < len(blocks):
            output.append(make_block(blocks[inserted]["style"], blocks[inserted]["title"], blocks[inserted]["text"]))
            inserted += 1
    while inserted < len(blocks):
        output.append(make_block(blocks[inserted]["style"], blocks[inserted]["title"], blocks[inserted]["text"]))
        inserted += 1
    return frontmatter + "\n\n".join(output).rstrip() + "\n"


def build_plan(src: Path, article_type: str, preset: str) -> tuple[dict[str, Any], str]:
    text = read_text(src)
    frontmatter, body = split_frontmatter(text)
    already_has = has_component(body)
    blocks = [] if already_has else build_blocks(body, article_type)
    component_md = insert_blocks(frontmatter, body, blocks)
    plan = {
        "ok": True,
        "source": str(src),
        "article_type": article_type,
        "article_type_label": ARTICLE_TYPES[article_type],
        "preset": preset,
        "source_already_has_components": already_has,
        "component_count": len(blocks) if not already_has else len(re.findall(r"^:::", body, flags=re.M)),
        "components": blocks,
        "note": "默认输出组件版新稿，不覆盖源稿；排版时应对该新稿锁定 preset 执行 wechat_format_presets.py。",
    }
    return plan, component_md


def main() -> None:
    parser = argparse.ArgumentParser(description="为公众号 Markdown 生成小组件编排计划和组件版新稿。")
    parser.add_argument("input", help="输入 Markdown。")
    parser.add_argument("--type", required=True, choices=sorted(ARTICLE_TYPES), help="文章类型。")
    parser.add_argument("--preset", default="tech", help="锁定排版预设。")
    parser.add_argument("--out", required=True, help="输出组件版 Markdown；不能与输入相同。")
    parser.add_argument("--plan", help="输出组件计划 JSON。")
    args = parser.parse_args()

    src = Path(args.input)
    out = Path(args.out)
    if not src.exists():
        raise SystemExit(f"输入文件不存在：{src}")
    if src.resolve() == out.resolve():
        raise SystemExit("为避免覆盖源稿，--out 不能与输入文件相同。")
    plan, component_md = build_plan(src, args.type, args.preset)
    out.write_text(component_md, encoding="utf-8")
    if args.plan:
        Path(args.plan).write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"组件版 Markdown 已生成：{out}")


if __name__ == "__main__":
    main()
