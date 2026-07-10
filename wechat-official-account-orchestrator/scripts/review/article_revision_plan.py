#!/usr/bin/env python3
"""根据 article_quality_review.py 的审稿 JSON 生成可执行改稿计划。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DIMENSION_LABELS = {
    "title_alignment": "标题兑现度",
    "structure": "结构完整度",
    "fact_reliability": "事实可信度",
    "professional_tone": "专业表达",
    "risk_compliance": "风险合规",
    "product_expression": "产品表达",
    "reader_value": "读者收益",
    "publish_readiness": "发布就绪度",
    "style_rigor": "表达严谨性",
}

FIX_PATTERNS = {
    "title_alignment": "重拟或收窄标题，让正文开头和结尾明确回应标题承诺。",
    "structure": "拆分长段落，补齐背景、分析、行动建议和章节小结。",
    "fact_reliability": "补来源、保留待核验标记，或删除无法核验的具体结论。",
    "professional_tone": "降级夸大、恐吓、绝对化表达，改成限定条件下的专业判断。",
    "risk_compliance": "删除敏感凭证、未授权信息和可滥用细节；必要时暂停发布。",
    "product_expression": "先讲场景和证据，再连接产品能力，并补充能力边界。",
    "reader_value": "增加判断标准、检查清单、下一步动作或读者可复用方法。",
    "publish_readiness": "补齐标题、摘要、作者、占位符、危险链接和草稿箱前元数据。",
    "style_rigor": "降低 AI 味，补具体场景、证据链和自然叙事节奏。",
}


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"文件不存在：{path}")
    return json.loads(path.read_text(encoding="utf-8-sig"))


def priority(score: int, blocking: list[str]) -> str:
    if blocking or score <= 2:
        return "P0"
    if score == 3:
        return "P1"
    if score == 4:
        return "P2"
    return "P3"


def build_tasks_from_dimensions(dimensions: dict[str, Any]) -> list[dict[str, Any]]:
    tasks = []
    for key, detail in dimensions.items():
        score = int(float(detail.get("score", 0)))
        issues = detail.get("issues", []) or []
        suggestions = detail.get("suggestions", []) or []
        blocking = detail.get("blocking", []) or []
        if score >= 5 and not issues and not blocking:
            continue
        label = DIMENSION_LABELS.get(key, key)
        tasks.append(
            {
                "dimension": key,
                "label": label,
                "priority": priority(score, blocking),
                "score": score,
                "blocking": blocking,
                "issues": issues,
                "revision_action": FIX_PATTERNS.get(key, "按审稿问题逐条修订。"),
                "suggestions": suggestions,
                "acceptance": [
                    f"{label}提升到 4/5 或以上。",
                    "不存在该维度阻断项。",
                    "修订后重新运行对应审稿脚本。",
                ],
            }
        )
    return tasks


def build_style_rigor_dimension(rigor: dict[str, Any] | None) -> dict[str, Any]:
    if not rigor:
        return {}
    return {
        "style_rigor": {
            "score": rigor.get("score", 0),
            "issues": rigor.get("issues", []) or [],
            "suggestions": rigor.get("suggestions", []) or [],
            "blocking": rigor.get("blocking", []) or [],
        }
    }


def build_plan(article: Path, review: dict[str, Any], rigor: dict[str, Any] | None = None) -> dict[str, Any]:
    dimensions = review.get("dimensions", {})
    tasks = build_tasks_from_dimensions(dimensions)
    tasks.extend(build_tasks_from_dimensions(build_style_rigor_dimension(rigor)))
    tasks.sort(key=lambda item: {"P0": 0, "P1": 1, "P2": 2, "P3": 3}.get(item["priority"], 9))
    blockers = (review.get("blocking", []) or []) + ((rigor or {}).get("blocking", []) or [])
    review_ok = bool(review.get("ok")) and (True if rigor is None else bool(rigor.get("ok")))
    review_score = review.get("score")
    return {
        "ok": not blockers and float(review.get("score", 0)) >= 4 and (True if rigor is None else float(rigor.get("score", 0)) >= 4),
        "article": str(article),
        "review_file": review.get("file") or str(article),
        "review_score": review_score,
        "review_ok": review_ok,
        "rigor_review": (
            {
                "file": rigor.get("file"),
                "score": rigor.get("score"),
                "ok": rigor.get("ok"),
                "model_review_prompt": rigor.get("model_review_prompt"),
            }
            if rigor
            else None
        ),
        "blocking": blockers,
        "tasks": tasks,
        "next_command": f"python scripts/review/article_quality_review.py {article} --out {article.with_suffix('.quality.json')}",
        "note": "本计划只生成改稿任务，不覆盖源稿；改完后必须重新审稿。",
    }


def render_markdown(plan: dict[str, Any]) -> str:
    lines = [
        "# 公众号审稿驱动改稿计划",
        "",
        f"- 文章：{plan['article']}",
        f"- 审稿分数：{plan['review_score']}",
        f"- 审稿结论：{'通过' if plan['review_ok'] else '未通过'}",
        "",
    ]
    if plan["blocking"]:
        lines.extend(["## 阻断项", ""])
        for item in plan["blocking"]:
            lines.append(f"- {item}")
        lines.append("")
    lines.extend(["## 改稿任务", ""])
    if not plan["tasks"]:
        lines.append("- 暂无需要修订的审稿任务。")
    for idx, task in enumerate(plan["tasks"], start=1):
        lines.extend(
            [
                f"### {idx}. [{task['priority']}] {task['label']}",
                "",
                f"- 当前评分：{task['score']}/5",
                f"- 修订动作：{task['revision_action']}",
            ]
        )
        if task["issues"]:
            lines.append("- 问题：")
            for issue in task["issues"]:
                lines.append(f"  - {issue}")
        if task["blocking"]:
            lines.append("- 阻断：")
            for item in task["blocking"]:
                lines.append(f"  - {item}")
        if task["suggestions"]:
            lines.append("- 建议：")
            for item in task["suggestions"]:
                lines.append(f"  - {item}")
        lines.append("- 通过标准：")
        for item in task["acceptance"]:
            lines.append(f"  - {item}")
        lines.append("")
    lines.extend(["## 复验命令", "", f"```bash\n{plan['next_command']}\n```", "", f"> {plan['note']}"])
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="根据审稿 JSON 生成公众号改稿计划。")
    parser.add_argument("article", help="原始 Markdown/HTML 稿件。")
    parser.add_argument("quality_json", help="article_quality_review.py 输出的 JSON。")
    parser.add_argument("--rigor-json", help="article_style_rigor_review.py 输出的 JSON。")
    parser.add_argument("--format", choices=["json", "markdown"], default=None, help="输出格式；默认按扩展名推断。")
    parser.add_argument("--out", help="输出文件。")
    args = parser.parse_args()

    article = Path(args.article)
    if not article.exists():
        raise SystemExit(f"文章不存在：{article}")
    plan = build_plan(article, read_json(Path(args.quality_json)), read_json(Path(args.rigor_json)) if args.rigor_json else None)
    out_format = args.format
    if out_format is None:
        out_format = "markdown" if args.out and Path(args.out).suffix.lower() in {".md", ".markdown"} else "json"
    content = render_markdown(plan) if out_format == "markdown" else json.dumps(plan, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        Path(args.out).write_text(content, encoding="utf-8")
        print(f"改稿计划已生成：{args.out}")
    else:
        print(content)


if __name__ == "__main__":
    main()

