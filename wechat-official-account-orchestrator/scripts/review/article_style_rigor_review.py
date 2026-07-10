#!/usr/bin/env python3
"""公众号稿件 AI 味、叙事单一和表达严谨性审稿。"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from statistics import pstdev
from typing import Any


GENERIC_OPENINGS = [
    "随着",
    "在数字化浪潮",
    "众所周知",
    "近年来",
    "当今时代",
    "本文将",
    "在快速发展的今天",
]

MECHANICAL_TRANSITIONS = ["首先", "其次", "再次", "最后", "总之", "综上", "值得注意的是"]
EVIDENCE_MARKERS = ["来源", "依据", "报告", "公告", "研究", "数据", "http://", "https://", ":::source"]
SCENARIO_MARKERS = ["例如", "比如", "场景", "当团队", "在实际", "一个常见", "具体来说"]
PRODUCT_WORDS = ["产品", "平台", "方案", "能力", "版本", "功能", "试用", "演示"]


def read_article(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def strip_frontmatter(text: str) -> str:
    lines = text.splitlines()
    if lines and lines[0].strip() == "---":
        for idx in range(1, min(len(lines), 80)):
            if lines[idx].strip() == "---":
                return "\n".join(lines[idx + 1 :])
    return text


def plain_text(text: str) -> str:
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = re.sub(r"^:::[\s\S]*?^:::", " ", text, flags=re.M)
    return re.sub(r"\s+", " ", text).strip()


def sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[。！？!?])", text) if len(s.strip()) >= 8]


def score_from_issues(issue_count: int, blocking_count: int) -> float:
    return max(0.0, round(5 - issue_count * 0.45 - blocking_count * 1.25, 2))


def evaluate(path: Path) -> dict[str, Any]:
    raw = read_article(path)
    body = strip_frontmatter(raw)
    plain = plain_text(body)
    sents = sentences(plain)
    issues: list[str] = []
    suggestions: list[str] = []
    blocking: list[str] = []

    opening = sents[0] if sents else ""
    if any(marker in opening for marker in GENERIC_OPENINGS):
        issues.append("开头存在泛泛套话或模板化表达。")
        suggestions.append("改为从具体问题、真实工作流变化或可核验事件进入。")
    transition_hits = [word for word in MECHANICAL_TRANSITIONS if plain.count(word) >= 2]
    if transition_hits:
        issues.append("存在机械连接词重复：" + "、".join(transition_hits))
        suggestions.append("减少“首先/其次/最后”式结构，改用问题推进、证据推进或场景推进。")
    if len(sents) >= 6:
        lengths = [len(s) for s in sents]
        if pstdev(lengths) < 12:
            issues.append("句长过于均匀，可能显得 AI 化。")
            suggestions.append("混合短判断句、解释句和具体场景句，形成自然节奏。")
    headings = re.findall(r"^#{2,3}\s+(.+)$", body, flags=re.M)
    repetitive = sum(1 for h in headings if re.search(r"(现象|原因|建议|总结|影响)", h))
    if len(headings) >= 4 and repetitive >= len(headings) - 1:
        issues.append("章节结构过于单一，容易像模板填充。")
        suggestions.append("改为围绕问题、证据、判断、边界、行动组织章节。")
    if not any(marker in plain for marker in SCENARIO_MARKERS):
        issues.append("缺少具体场景或例子。")
        suggestions.append("补充一个目标读者熟悉的工作流、判断困难或使用场景。")
    has_conclusion = bool(re.search(r"(因此|所以|这意味着|可以判断|结论是|核心判断)", plain))
    has_evidence = any(marker in plain for marker in EVIDENCE_MARKERS)
    if has_conclusion and not has_evidence:
        issues.append("存在结论性表达，但没有明显证据或来源支撑。")
        suggestions.append("补充来源、依据或 `source` 组件；缺失事实保留待核验。")
    has_product = any(word in plain for word in PRODUCT_WORDS)
    has_context = bool(re.search(r"(场景|问题|痛点|边界|适用|使用路径|证据|示例)", plain))
    if has_product and not has_context:
        issues.append("产品表达像硬插广告，缺少场景、证据或边界。")
        suggestions.append("先写读者问题和使用路径，再轻量连接产品能力。")
    if "待核验" in plain and not has_evidence:
        blocking.append("存在待核验事实，但没有来源或依据说明。")
    score = score_from_issues(len(issues), len(blocking))
    return {
        "ok": score >= 4 and not blocking,
        "score": score,
        "file": str(path),
        "issues": issues,
        "suggestions": suggestions,
        "blocking": blocking,
        "model_review_prompt": (
            "请从公众号资深编辑角度复审这篇文章：检查是否 AI 味重、结构单一、缺少具体场景、"
            "论证不严谨、产品表达硬插。请只输出问题清单和可执行修改建议，不新增事实。"
        ),
        "note": "本结果为本地规则检查；复杂表达质量应结合模型复审和人工判断。",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="公众号稿件 AI 味与表达严谨性审稿。")
    parser.add_argument("file", help="Markdown 或 HTML 稿件。")
    parser.add_argument("--out", help="输出 JSON 文件。")
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        raise SystemExit(f"文件不存在：{path}")
    result = evaluate(path)
    data = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).write_text(data + "\n", encoding="utf-8")
        print(f"表达严谨性审稿已生成：{args.out}")
    else:
        print(data)


if __name__ == "__main__":
    main()
