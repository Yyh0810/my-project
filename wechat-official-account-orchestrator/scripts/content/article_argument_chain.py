#!/usr/bin/env python3
"""生成公众号文章论证链规划与缺口检查。"""

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

PRODUCT_LEVELS = ["none", "light", "medium", "strong"]


def read_text(path_text: str | None) -> str:
    if not path_text:
        return ""
    path = Path(path_text)
    if not path.exists():
        raise SystemExit(f"文件不存在：{path}")
    return path.read_text(encoding="utf-8-sig")


def read_ledger(path_text: str | None) -> dict[str, Any] | None:
    if not path_text:
        return None
    path = Path(path_text)
    if not path.exists():
        raise SystemExit(f"资料台账不存在：{path}")
    return json.loads(path.read_text(encoding="utf-8-sig"))


def claims_from_ledger(ledger: dict[str, Any] | None) -> list[str]:
    if not ledger:
        return []
    claims: list[str] = []
    for source in ledger.get("sources", []):
        for claim in source.get("usable_claims", []):
            text = str(claim).strip()
            if text and "待补充" not in text:
                claims.append(text)
    return claims[:8]


def extract_article_signals(text: str) -> dict[str, bool]:
    plain = re.sub(r"```.*?```", " ", text, flags=re.S)
    return {
        "has_evidence": bool(re.search(r"(来源|依据|报告|公告|研究|数据|http|https|:::source)", plain, flags=re.I)),
        "has_boundary": bool(re.search(r"(边界|前提|限制|不适合|不确定|待核验|不能|暂不)", plain)),
        "has_reader_action": bool(re.search(r"(建议|检查|清单|下一步|行动|试点|复核|评估)", plain)),
        "has_product_boundary": bool(re.search(r"(能力边界|适用条件|不替代|暂不覆盖|产品连接)", plain)),
    }


def build_chain(args: argparse.Namespace) -> dict[str, Any]:
    ledger = read_ledger(args.ledger)
    article_text = read_text(args.input)
    claims = claims_from_ledger(ledger)
    signals = extract_article_signals(article_text)
    evidence = claims or (["从已有稿件中发现来源/依据标记，需人工整理为明确证据。"] if signals["has_evidence"] else [])
    product_boundary = (
        "不主动加入产品表达，只保留中立分析。"
        if args.product_level == "none"
        else "只在读者动作之后轻量说明产品或方案能帮助的明确环节。"
        if args.product_level == "light"
        else "可解释产品适用环节，但必须保留能力边界和证据。"
    )
    dimensions = {
        "core_claim": {
            "ok": True,
            "value": args.claim or f"围绕“{args.topic}”给出一个面向{ARTICLE_TYPES[args.type]}的可验证判断。",
        },
        "supporting_evidence": {
            "ok": bool(evidence),
            "value": evidence or ["缺少可引用证据；需要公开资料调研或补充内部材料。"],
        },
        "reasoning": {
            "ok": True,
            "value": "问题现象 -> 证据 -> 判断 -> 影响 -> 行动建议。",
        },
        "scope_boundary": {
            "ok": signals["has_boundary"] or bool(ledger),
            "value": "明确适用对象、前提条件和不确定项；缺失时保留待核验。",
        },
        "reader_action": {
            "ok": signals["has_reader_action"],
            "value": "给出检查、试点、评估、复核或内部讨论动作。",
        },
        "product_connection_boundary": {
            "ok": args.product_level in {"none", "light"} or signals["has_product_boundary"],
            "value": product_boundary,
        },
    }
    blocking = []
    suggestions = []
    if not dimensions["supporting_evidence"]["ok"]:
        blocking.append("缺少支撑证据，不能进入成稿。")
        suggestions.append("先生成公开资料台账，或补充可引用内部材料。")
    if not dimensions["reader_action"]["ok"]:
        suggestions.append("补充读者下一步可以执行的检查、试点或复核动作。")
    if not dimensions["scope_boundary"]["ok"]:
        suggestions.append("补充适用边界、前提条件和不确定项。")
    ok = not blocking
    return {
        "ok": ok,
        "topic": args.topic,
        "article_type": args.type,
        "article_type_label": ARTICLE_TYPES[args.type],
        "product_level": args.product_level,
        "dimensions": dimensions,
        "blocking": blocking,
        "suggestions": suggestions,
        "ledger": args.ledger or "",
        "input": args.input or "",
    }


def render_markdown(chain: dict[str, Any]) -> str:
    lines = [
        "# 文章论证链",
        "",
        f"- 主题：{chain['topic']}",
        f"- 文章类型：{chain['article_type']} / {chain['article_type_label']}",
        f"- 产品连接强度：{chain['product_level']}",
        "",
        "## 论证链检查",
        "",
    ]
    labels = {
        "core_claim": "核心判断",
        "supporting_evidence": "支撑证据",
        "reasoning": "推理过程",
        "scope_boundary": "适用边界",
        "reader_action": "读者动作",
        "product_connection_boundary": "产品连接边界",
    }
    for key, item in chain["dimensions"].items():
        value = item["value"]
        lines.append(f"### {labels.get(key, key)}")
        lines.append(f"- 状态：{'通过' if item['ok'] else '需补充'}")
        if isinstance(value, list):
            for v in value:
                lines.append(f"- {v}")
        else:
            lines.append(f"- {value}")
        lines.append("")
    if chain["blocking"]:
        lines.extend(["## 阻断项", ""])
        for item in chain["blocking"]:
            lines.append(f"- {item}")
        lines.append("")
    if chain["suggestions"]:
        lines.extend(["## 建议", ""])
        for item in chain["suggestions"]:
            lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="生成公众号文章论证链规划与缺口检查。")
    parser.add_argument("--topic", required=True, help="文章主题。")
    parser.add_argument("--type", required=True, choices=sorted(ARTICLE_TYPES), help="文章类型。")
    parser.add_argument("--ledger", help="research_ledger_builder.py 输出的资料台账 JSON。")
    parser.add_argument("--input", help="已有 Markdown 稿件，用于检查论证信号。")
    parser.add_argument("--claim", help="指定核心判断。")
    parser.add_argument("--product-level", choices=PRODUCT_LEVELS, default="light", help="产品连接强度。")
    parser.add_argument("--format", choices=["json", "markdown"], default=None, help="输出格式；默认按扩展名推断。")
    parser.add_argument("--out", help="输出文件。")
    args = parser.parse_args()

    chain = build_chain(args)
    out_format = args.format
    if out_format is None:
        out_format = "markdown" if args.out and Path(args.out).suffix.lower() in {".md", ".markdown"} else "json"
    content = render_markdown(chain) if out_format == "markdown" else json.dumps(chain, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        Path(args.out).write_text(content, encoding="utf-8")
        print(f"文章论证链已生成：{args.out}")
    else:
        print(content)


if __name__ == "__main__":
    main()
