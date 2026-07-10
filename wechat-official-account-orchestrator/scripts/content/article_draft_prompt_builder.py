#!/usr/bin/env python3
"""根据成稿写作包生成可直接交给模型的公众号初稿提示词。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def read_pack(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"写作包不存在：{path}")
    if path.suffix.lower() != ".json":
        raise SystemExit("当前脚本只读取 article_writing_pack.py 输出的 JSON 写作包。")
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    required = ["metadata", "writing_strategy", "fact_ledger", "section_tasks", "model_collaboration"]
    missing = [key for key in required if key not in data]
    if missing:
        raise SystemExit("写作包缺少字段：" + "、".join(missing))
    return data


def section_word_budget(total: int, count: int) -> list[int]:
    if count <= 0:
        return []
    opening = max(180, round(total * 0.12))
    ending = max(180, round(total * 0.12))
    middle_total = max(total - opening - ending, count * 180)
    budgets = [round(middle_total / count)] * count
    if budgets:
        budgets[0] = max(budgets[0], opening)
        budgets[-1] = max(budgets[-1], ending)
    return budgets


def build_prompt(pack: dict[str, Any]) -> dict[str, Any]:
    meta = pack["metadata"]
    strategy = pack["writing_strategy"]
    argument_chain = pack.get("argument_chain", {})
    section_tasks = pack["section_tasks"]
    target_length = int(meta.get("target_length") or 1800)
    budgets = section_word_budget(target_length, len(section_tasks))
    section_instructions = []
    for idx, task in enumerate(section_tasks):
        budget = budgets[idx] if idx < len(budgets) else 300
        section_instructions.append(
            {
                "section": task["section"],
                "word_budget": budget,
                "goal": task["writing_goal"],
                "must_include": task.get("must_include", []),
                "avoid": task.get("avoid", []),
                "instruction": (
                    f"撰写“{task['section']}”部分，约 {budget} 字。"
                    f"目标：{task['writing_goal']} "
                    "必须包含本节结论、支撑依据或待核验标记、边界条件；避免空泛套话和重复上一节。"
                ),
            }
        )
    fact_items = [
        f"- {item.get('fact', '待核验事实')}：{item.get('status', '待核验')}；来源：{item.get('source', '待补充')}"
        for item in pack.get("fact_ledger", [])
    ]
    system_prompt = pack["model_collaboration"].get("system_prompt", "")
    user_prompt = "\n".join(
        [
            f"请根据以下写作包撰写一篇微信公众号 Markdown 初稿。",
            "",
            f"主题：{meta['topic']}",
            f"拟定标题：{meta['title']}",
            f"文章类型：{meta['article_type_label']} / {meta['article_type']}",
            f"目标读者：{meta['audience']}",
            f"目标字数：约 {target_length} 字",
            f"核心角度：{strategy['core_angle']}",
            f"读者任务：{strategy['reader_job']}",
            f"产品表达策略：{strategy['product_policy']}",
            f"论证链核心判断：{argument_chain.get('core_claim', '待补充')}",
            f"论证链适用边界：{argument_chain.get('scope_boundary', '待补充')}",
            f"论证链读者动作：{argument_chain.get('reader_action', '待补充')}",
            f"论证链产品连接边界：{argument_chain.get('product_connection_boundary', '待补充')}",
            "",
            "事实台账：",
            *fact_items,
            "",
            "写作要求：",
            "- 输出完整 Markdown 初稿，保留 YAML frontmatter。",
            "- frontmatter 至少包含 title、author、digest、article_type、audience、fact_status。",
            "- 每个章节都要有明确结论、依据、边界和读者收益。",
            "- 具体事实没有来源时必须写“待核验”，不要改成确定事实。",
            "- 不新增客户、数字、漏洞编号、政策条款、市场规模、产品指标。",
            "- 不写正式发布、上传、草稿箱成功等状态描述。",
            "- 不使用夸大、恐吓、竞品贬损或过度营销表达。",
            "",
            "章节任务：",
        ]
    )
    for item in section_instructions:
        user_prompt += (
            f"\n\n## {item['section']}\n"
            f"- 字数建议：约 {item['word_budget']} 字\n"
            f"- 写作目标：{item['goal']}\n"
            f"- 必须包含：{'；'.join(item['must_include'])}\n"
            f"- 避免：{'；'.join(item['avoid'])}\n"
            f"- 执行指令：{item['instruction']}"
        )
    user_prompt += "\n\n结尾要求：用克制 CTA 收束，给出下一步检查、试点、咨询或内部讨论动作，不制造紧迫感。"
    return {
        "ok": True,
        "metadata": meta,
        "system_prompt": system_prompt,
        "user_prompt": user_prompt,
        "section_instructions": section_instructions,
        "fact_rules": [
            "缺少来源的具体事实必须标注待核验。",
            "不得新增客户、数字、漏洞编号、政策、产品指标。",
            "不得删除写作包中已有的待核验边界。",
        ],
        "output_contract": [
            "只输出 Markdown 初稿。",
            "不输出 HTML、图片、上传结果或草稿箱状态。",
            "初稿完成后必须进入 article_quality_review.py 审稿。",
        ],
    }


def render_markdown(prompt: dict[str, Any]) -> str:
    meta = prompt["metadata"]
    lines = [
        "# 公众号初稿生成提示词",
        "",
        f"- 主题：{meta['topic']}",
        f"- 文章类型：{meta['article_type']} / {meta['article_type_label']}",
        f"- 目标读者：{meta['audience']}",
        f"- 目标字数：{meta.get('target_length', 1800)}",
        "",
        "## System Prompt",
        "",
        prompt["system_prompt"],
        "",
        "## User Prompt",
        "",
        prompt["user_prompt"],
        "",
        "## 输出约束",
        "",
    ]
    for item in prompt["output_contract"]:
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="根据成稿写作包生成公众号初稿提示词。")
    parser.add_argument("writing_pack", help="article_writing_pack.py 输出的 JSON 写作包。")
    parser.add_argument("--format", choices=["json", "markdown"], default=None, help="输出格式；默认按扩展名推断。")
    parser.add_argument("--out", help="输出文件。")
    args = parser.parse_args()

    prompt = build_prompt(read_pack(Path(args.writing_pack)))
    out_format = args.format
    if out_format is None:
        out_format = "markdown" if args.out and Path(args.out).suffix.lower() in {".md", ".markdown"} else "json"
    content = render_markdown(prompt) if out_format == "markdown" else json.dumps(prompt, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        Path(args.out).write_text(content, encoding="utf-8")
        print(f"初稿生成提示词已生成：{args.out}")
    else:
        print(content)


if __name__ == "__main__":
    main()
