#!/usr/bin/env python3
"""生成公众号文章 Markdown 大纲骨架。"""

from __future__ import annotations

import argparse
from pathlib import Path


ARTICLE_TYPES = {
    "security-analysis": {
        "label": "安全分析",
        "sections": ["背景与问题", "影响对象与风险边界", "风险链路分析", "检查与处置建议", "产品连接与下一步"],
        "opening": "从一个具体风险、暴露面或安全运营问题进入。",
        "evidence": "漏洞编号、影响范围、利用状态、日期、数据来源。",
        "cta": "引导读者检查资产、复核暴露面、补齐监测和处置动作。",
    },
    "agent-observation": {
        "label": "AI Agent 观察",
        "sections": ["观察到的现象", "变化背后的原因", "对团队协作的影响", "落地边界与风险", "下一步试点建议"],
        "opening": "从一个真实工作流变化或协作问题进入。",
        "evidence": "工具能力、实践案例、效率变化、失败边界。",
        "cta": "建议选择一个低风险场景试点，并设置评估指标。",
    },
    "product-launch": {
        "label": "产品发布",
        "sections": ["场景问题", "本次发布的能力", "使用路径", "能力边界", "试用或咨询入口"],
        "opening": "从用户场景和已有痛点进入，不直接堆功能。",
        "evidence": "版本号、能力范围、示例路径、客户效果、指标。",
        "cta": "引导试用、预约演示、查看文档或联系团队。",
    },
    "industry-observation": {
        "label": "行业观察",
        "sections": ["现象", "关键证据", "判断与影响", "边界与不确定性", "行动建议"],
        "opening": "从一个可观察现象进入，避免空泛趋势词。",
        "evidence": "报告、调研、公告、排名、市场规模。",
        "cta": "给出判断标准或内部讨论问题。",
    },
    "case-review": {
        "label": "案例复盘",
        "sections": ["背景与目标", "过程回顾", "关键问题", "经验沉淀", "后续改进动作"],
        "opening": "从复盘目标和约束进入。",
        "evidence": "项目背景、过程记录、结果数据、授权状态。",
        "cta": "给出可复用清单，避免同类问题。",
    },
}


def frontmatter(title: str, author: str, digest: str, article_type: str, audience: str) -> str:
    return "\n".join(
        [
            "---",
            f'title: "{title}"',
            f'author: "{author}"',
            f'digest: "{digest}"',
            f'article_type: "{article_type}"',
            f'audience: "{audience}"',
            'fact_status: "待核验"',
            "---",
            "",
        ]
    )


def build_outline(topic: str, article_type: str, audience: str, product_level: str, author: str) -> str:
    playbook = ARTICLE_TYPES[article_type]
    title = f"{topic}：{playbook['label']}大纲（待定标题）"
    digest = f"围绕{topic}形成一篇面向{audience}的{playbook['label']}文章，关键事实待核验。"
    lines = [frontmatter(title, author, digest, article_type, audience)]
    lines.append(f"# {title}")
    lines.append("")
    lines.append("## 写作定位")
    lines.append("")
    lines.append(f"- 主题：{topic}")
    lines.append(f"- 文章类型：{article_type} / {playbook['label']}")
    lines.append(f"- 目标读者：{audience}")
    lines.append(f"- 产品连接强度：{product_level}")
    lines.append(f"- 开头方式：{playbook['opening']}")
    lines.append("")
    lines.append("## 待核验事实")
    lines.append("")
    lines.append(f"- {playbook['evidence']}：待核验")
    lines.append("- 关键数据、客户案例、版本号、第三方结论：待核验")
    lines.append("- 可公开引用来源：待核验")
    lines.append("")
    for idx, section in enumerate(playbook["sections"], start=1):
        lines.append(f"## {idx}. {section}")
        lines.append("")
        lines.append("- 核心要点：待补充")
        lines.append("- 支撑事实：待核验")
        lines.append("- 读者收益：待补充")
        lines.append("")
    lines.append("## 结尾与 CTA")
    lines.append("")
    lines.append(f"- CTA 风格：{playbook['cta']}")
    lines.append("- 下一步动作：待补充")
    lines.append("")
    lines.append("## 禁用表达检查")
    lines.append("")
    lines.append("- 不写最强、唯一、100%、彻底解决、零风险。")
    lines.append("- 不写未经授权客户、指标、漏洞编号或产品能力。")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="生成公众号文章 Markdown 大纲骨架。")
    parser.add_argument("--topic", required=True, help="文章主题。")
    parser.add_argument("--type", required=True, choices=sorted(ARTICLE_TYPES), help="文章类型。")
    parser.add_argument("--audience", default="内部运营团队", help="目标读者。")
    parser.add_argument("--product-level", choices=["none", "light", "medium", "strong"], default="light", help="产品连接强度。")
    parser.add_argument("--author", default="内容运营组", help="作者。")
    parser.add_argument("--out", help="输出 Markdown 文件。")
    args = parser.parse_args()

    content = build_outline(args.topic, args.type, args.audience, args.product_level, args.author)
    if args.out:
        Path(args.out).write_text(content + "\n", encoding="utf-8")
        print(f"文章大纲已生成：{args.out}")
    else:
        print(content)


if __name__ == "__main__":
    main()
