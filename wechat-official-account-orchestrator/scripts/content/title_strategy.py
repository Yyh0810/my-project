#!/usr/bin/env python3
"""生成公众号标题策略候选。"""

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

RISK_WORDS = ["最强", "唯一", "100%", "彻底解决", "零风险", "颠覆", "秒杀", "吊打"]


def read_topic(args: argparse.Namespace) -> str:
    if args.topic:
        return args.topic.strip()
    if args.input:
        text = Path(args.input).read_text(encoding="utf-8-sig")
        title_match = re.search(r"^#\s+(.+)$", text, flags=re.M)
        if title_match:
            return title_match.group(1).strip()
        frontmatter = re.search(r"^title:\s*[\"']?(.+?)[\"']?\s*$", text, flags=re.M)
        if frontmatter:
            return frontmatter.group(1).strip()
    raise SystemExit("必须提供 --topic 或 --input。")


def risk(title: str, style: str) -> tuple[str, str, bool]:
    hits = [w for w in RISK_WORDS if w in title]
    if hits:
        return "high", "包含夸大或绝对化表达：" + "、".join(hits), False
    if style == "传播标题":
        return "medium", "传播标题更容易提高期待，需要确认正文能兑现。", False
    if style == "客户向标题":
        return "low", "面向客户场景，需确认不暗示未经证实的效果。", False
    return "low", "表达稳妥，风险较低。", style == "专业标题"


def candidates(topic: str, article_type: str) -> list[dict[str, Any]]:
    label = ARTICLE_TYPES[article_type]
    raw = [
        ("专业标题", f"{topic}：一套面向{label}的判断框架"),
        ("传播标题", f"为什么{topic}正在改变团队的工作方式"),
        ("客户向标题", f"面向业务团队的{topic}落地清单"),
        ("正式标题", f"关于{topic}的阶段性观察与建议"),
    ]
    result = []
    for style, title in raw:
        risk_level, reason, recommended = risk(title, style)
        result.append(
            {
                "style": style,
                "title": title,
                "risk_level": risk_level,
                "reason": reason,
                "recommended": recommended,
                "requires_fact_support": style in {"传播标题", "客户向标题"},
            }
        )
    if not any(item["recommended"] for item in result):
        result[0]["recommended"] = True
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="生成公众号标题策略候选。")
    parser.add_argument("--topic", help="文章主题。")
    parser.add_argument("--input", help="从 Markdown 大纲或稿件读取主题。")
    parser.add_argument("--type", required=True, choices=sorted(ARTICLE_TYPES), help="文章类型。")
    parser.add_argument("--out", help="输出 JSON 文件。")
    args = parser.parse_args()

    topic = read_topic(args)
    payload = {
        "topic": topic,
        "article_type": args.type,
        "titles": candidates(topic, args.type),
        "note": "标题不会自动写回源稿；采用前需确认正文能兑现标题承诺。",
    }
    data = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).write_text(data + "\n", encoding="utf-8")
        print(f"标题策略已生成：{args.out}")
    else:
        print(data)


if __name__ == "__main__":
    main()
